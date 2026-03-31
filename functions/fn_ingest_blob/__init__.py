"""Blob ingestion function: incoming -> Cosmos doc + raw/{docId}/{filename}."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from pathlib import Path
import time
import uuid

import azure.functions as func
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.storage.blob.aio import BlobServiceClient

from shared.cosmos_helpers import get_cosmos_container_from_env_async, utc_now_iso
from shared.statuses import RECEIVED

INCOMING_CONTAINER = "incoming"
COPY_POLL_INTERVAL_SEC = 1.5
COPY_TIMEOUT_SEC = 60
HASH_CHUNK_SIZE = 65536  # 64 KB for memory-safe hashing

logger = logging.getLogger(__name__)

# Suppress Azure SDK noise so function logs stay visible.
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)


def _get_required_env() -> dict[str, str]:
    """Load required env vars at startup; raise if any are missing (fail-fast)."""
    required = [
        "AzureWebJobsStorage",
        "COSMOS_ENDPOINT",
        "COSMOS_DB_NAME",
        "COSMOS_CONTAINER_NAME",
    ]
    out: dict[str, str] = {}
    for key in required:
        val = os.environ.get(key)
        if not val:
            raise RuntimeError(f"Missing required environment variable: {key}")
        out[key] = val
    out["RAW_CONTAINER_NAME"] = os.environ.get("RAW_CONTAINER_NAME", "raw")
    return out


async def _compute_sha256_chunked(stream) -> str:
    """Compute SHA256 by reading stream in 64KB chunks (avoids OOM on large files)."""
    hasher = hashlib.sha256()
    while True:
        chunk = stream.read(HASH_CHUNK_SIZE)
        if not chunk:
            break
        hasher.update(chunk)
    return hasher.hexdigest()


def _doc_id_from_blob_name(blob_name: str) -> str:
    """
    Derive docId from an incoming blob filename when possible.

    Expected HTTP-upload path is `incoming/{docId}.pdf`, so the blob filename stem
    should be a UUID. If not UUID-shaped, fall back to generating a new UUID.
    """
    stem = Path(blob_name).stem.strip()
    if not stem:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(stem))
    except Exception:
        logger.warning(
            "DOC_ID_DERIVE_FALLBACK",
            extra={"blobName": blob_name, "stem": stem, "step": "DOC_ID_DERIVE_FALLBACK"},
        )
        return str(uuid.uuid4())


async def main(myblob: func.InputStream) -> None:
    """Process blob from incoming container: Cosmos upsert, copy to raw, delete source (async)."""
    doc_id: str | None = None
    name = ""

    try:
        # Fail-fast: load all required config at start.
        env = _get_required_env()
        conn_str = env["AzureWebJobsStorage"]
        raw_container_name = env["RAW_CONTAINER_NAME"]

        name = myblob.name or ""
        if "/" in name:
            blob_name = name.split("/", 1)[1]
        else:
            blob_name = name

        # Reuse the uploaded UUID from incoming filename when available.
        doc_id = _doc_id_from_blob_name(blob_name)
        policy_type = "unknown"
        original_filename = blob_name

        try:
            sha256hex = await _compute_sha256_chunked(myblob)
        except Exception:
            logger.exception(
                "RECEIVED: Failed to read blob or compute sha256",
                extra={"docId": doc_id, "blobName": name},
            )
            raise

        logger.info(
            "RECEIVED",
            extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "RECEIVED"},
        )

        async with BlobServiceClient.from_connection_string(conn_str) as blob_service:
            incoming_client = blob_service.get_container_client(INCOMING_CONTAINER)
            source_blob = incoming_client.get_blob_client(blob_name)

            try:
                props = await source_blob.get_blob_properties()
            except Exception:
                logger.exception(
                    "RECEIVED: Failed to get blob properties",
                    extra={"docId": doc_id, "blobName": name},
                )
                raise

        content_type = props.content_settings.content_type or ""
        size_bytes = props.size or 0
        etag = props.etag or ""

        metadata = props.metadata or {}
        policy_type = metadata.get("policyType") or metadata.get("policytype")
        if policy_type is None and "/" in blob_name:
            policy_type = blob_name.split("/")[0]
        if policy_type is None:
            policy_type = "unknown"

        if "/" in blob_name:
            original_filename = blob_name.split("/")[-1]
        else:
            original_filename = blob_name

        uploaded_at = utc_now_iso()
        doc = {
            "id": doc_id,
            "docId": doc_id,
            "filename": original_filename,
            "uploadedAtUtc": uploaded_at,
            "policyType": policy_type,
            "sha256": sha256hex,
            "status": RECEIVED,
            "statusUpdatedAtUtc": uploaded_at,
            "sourceBlobPath": f"incoming/{blob_name}",
            "rawBlobPath": f"raw/{doc_id}/{original_filename}",
            "contentType": content_type,
            "sizeBytes": size_bytes,
            "etag": etag,
        }

        # get_cosmos_container_from_env_async is a plain async function (not a context manager).
        container = await get_cosmos_container_from_env_async()
        try:
            await container.upsert_item(doc)
            logger.info(
                "COSMOS_UPSERT_OK",
                extra={
                    "docId": doc_id,
                    "blobName": name,
                    "policyType": policy_type,
                    "step": "COSMOS_UPSERT_OK",
                },
            )
        except CosmosHttpResponseError as e:
            if e.status_code == 409:
                logger.warning(
                    "DUPLICATE_SHA256",
                    extra={
                        "docId": doc_id,
                        "blobName": name,
                        "policyType": policy_type,
                        "sha256": sha256hex,
                        "step": "DUPLICATE_SHA256",
                    },
                )
            else:
                raise

        async with BlobServiceClient.from_connection_string(conn_str) as blob_service:
            raw_container = blob_service.get_container_client(raw_container_name)
            dest_path = f"{doc_id}/{original_filename}"
            dest_blob = raw_container.get_blob_client(dest_path)
            source_blob = blob_service.get_container_client(INCOMING_CONTAINER).get_blob_client(
                blob_name
            )

            logger.info(
                "COPY_STARTED",
                extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "COPY_STARTED"},
            )

            await dest_blob.start_copy_from_url(source_blob.url)
            start = time.monotonic()
            while True:
                dest_props = await dest_blob.get_blob_properties()
                copy_info = getattr(dest_props, "copy", None)
                status = getattr(copy_info, "status", "success") if copy_info else "success"
                if status in ("success", "complete"):
                    break
                if status == "failed":
                    msg = (
                        getattr(copy_info, "status_description", None) if copy_info else None
                    ) or "Copy failed"
                    raise RuntimeError(f"Blob copy failed: {msg}")
                if time.monotonic() - start > COPY_TIMEOUT_SEC:
                    raise RuntimeError("Blob copy timed out")
                await asyncio.sleep(COPY_POLL_INTERVAL_SEC)

            logger.info(
                "COPY_SUCCEEDED",
                extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "COPY_SUCCEEDED"},
            )

            await source_blob.delete_blob()
            logger.info(
                "INCOMING_DELETED",
                extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "INCOMING_DELETED"},
            )
    except Exception:
        logger.exception("fn_ingest_blob failed", extra={"docId": doc_id, "blobName": name})
        raise
