"""Blob-triggered OCR function: raw -> Azure Document Intelligence (prebuilt-layout).

Triggered when a blob appears in the `raw` container at:
    raw/{docId}/{filename}

Behavior:
- Wait for blob copy to complete (poll copy_status) so fn_ingest_blob has finished.
- Resolve the document metadata in Cosmos (including policyType).
- Update status to OCR_STARTED.
- Call Azure Document Intelligence using the shared wrapper (async).
- Persist the raw vendor OCR response to ocr-raw/{docId}/document_intelligence.json
- Update status to OCR_COMPLETE, or OCR_FAILED on errors.
- On full success, delete the source blob from raw.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional, Tuple

import azure.functions as func
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient

from shared.blob_paths import get_ocr_layout_blob_path, get_ocr_raw_blob_path
from shared.cosmos_helpers import (
    get_cosmos_container_from_env_async,
    update_document_status_async,
)
from shared.document_intelligence_client import DocumentIntelligenceWrapper
from shared.layout_normalizer import normalize_layout_result
from shared.statuses import OCR_COMPLETE, OCR_FAILED, OCR_STARTED

logger = logging.getLogger(__name__)

# Silence Azure SDK HTTP and storage noise so function logs stay visible.
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)

COPY_POLL_MAX_ATTEMPTS = 5
COPY_POLL_SLEEP_SEC = 2.0
COSMOS_LOOKUP_RETRY_ATTEMPTS = 5
COSMOS_LOOKUP_RETRY_SLEEP_SEC = 2.0


def _get_required_env() -> dict[str, str]:
    """Load required env vars at startup; raise if any are missing (fail-fast)."""
    required = [
        "AzureWebJobsStorage",
        "COSMOS_ENDPOINT",
        "COSMOS_DB_NAME",
        "COSMOS_CONTAINER_NAME",
        "DOCUMENT_INTELLIGENCE_ENDPOINT",
    ]
    out: dict[str, str] = {}
    for key in required:
        val = os.environ.get(key)
        if not val or not str(val).strip():
            raise RuntimeError(f"Missing required environment variable: {key}")
        out[key] = str(val).strip()
    return out


def _parse_raw_blob_name(blob_name: str) -> Tuple[str, str, Optional[str]]:
    """
    Parse a blob name into (docId, filename, policyTypeHint) with validation.

    Supported patterns:
    - raw/{docId}/{filename}
    - raw/{policyType}/{docId}/{filename}
    - incoming/test/{filename}
    """
    if not blob_name:
        raise ValueError("Blob name is empty")

    path = Path(blob_name)
    parts = path.parts

    if len(parts) < 2:
        raise ValueError(f"Unexpected blob name format: {blob_name!r}")

    # Test harness / non-production blobs can live under incoming/test/{filename}.
    if parts[0] == "incoming" and len(parts) >= 3 and parts[1] == "test":
        filename = "/".join(parts[2:])
        if not filename:
            raise ValueError(f"Missing filename segment in blob name: {blob_name!r}")
        doc_id = Path(filename).stem
        return doc_id, filename, None

    if parts[0] != "raw":
        raise ValueError(
            f"Expected blob path to start with 'raw/' or 'incoming/test/', got: {blob_name!r}"
        )

    # New-style path with policy type encoded: raw/{policyType}/{docId}/{filename...}
    if len(parts) >= 4:
        _, policy_type, doc_id, *rest = parts
        filename = "/".join(rest)
        if not doc_id:
            raise ValueError(f"Missing docId segment in blob name: {blob_name!r}")
        if not filename:
            raise ValueError(f"Missing filename segment in blob name: {blob_name!r}")
        return doc_id, filename, policy_type

    # Legacy path: raw/{docId}/{filename...}
    _, doc_id, *rest = parts
    filename = "/".join(rest)
    if not doc_id:
        raise ValueError(f"Missing docId segment in blob name: {blob_name!r}")
    if not filename:
        raise ValueError(f"Missing filename segment in blob name: {blob_name!r}")
    return doc_id, filename, None


async def _get_document_and_partition_key_async(
    container: Any, blob_path: str, policy_type_hint: Optional[str] = None
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Async: lookup document in Cosmos by path and return (document, policyType).

    Uses rawBlobPath when blob_path starts with "raw/", else sourceBlobPath.
    When policy_type_hint is provided, the first query is partition-scoped;
    if it returns no results, a cross-partition fallback is performed.
    Retries up to COSMOS_LOOKUP_RETRY_ATTEMPTS times with 2s delay when the
    query returns 0 documents (handles race with fn_ingest_blob and eventual consistency).
    """
    if not blob_path or not str(blob_path).strip():
        raise ValueError("blob_path must be a non-empty string")

    # Lookup key: raw trigger path is stored in rawBlobPath; incoming/source path in sourceBlobPath.
    if blob_path.startswith("raw/"):
        lookup_key = "rawBlobPath"
    else:
        lookup_key = "sourceBlobPath"
    query = f"SELECT * FROM c WHERE c.{lookup_key} = @blobPath"
    base_kwargs: dict[str, Any] = {
        "query": query,
        "parameters": [{"name": "@blobPath", "value": blob_path}],
    }

    async def _run_query(kwargs: dict[str, Any]) -> list[dict]:
        results: list[dict] = []
        async for item in container.query_items(**kwargs):
            results.append(item)
        return results

    items: list[dict] = []
    for attempt in range(COSMOS_LOOKUP_RETRY_ATTEMPTS):
        items = []

        # Partition-scoped query when we have a hint from path segments.
        if policy_type_hint:
            scoped_kwargs = dict(base_kwargs)
            scoped_kwargs["partition_key"] = policy_type_hint
            items = await _run_query(scoped_kwargs)
            if not items:
                logger.info(
                    "COSMOS_PARTITION_LOOKUP_EMPTY",
                    extra={
                        "blobPath": blob_path,
                        "policyTypeHint": policy_type_hint,
                        "step": "COSMOS_PARTITION_LOOKUP_EMPTY",
                    },
                )

        # Fallback: cross-partition query (no partition_key).
        if not items:
            items = await _run_query(base_kwargs)

        if items:
            doc = items[0]
            policy_type = doc.get("policyType")
            return doc, policy_type

        if attempt < COSMOS_LOOKUP_RETRY_ATTEMPTS - 1:
            logger.warning(
                "Document record for %s not found yet, retrying (Attempt %d/%d)...",
                blob_path,
                attempt + 1,
                COSMOS_LOOKUP_RETRY_ATTEMPTS,
                extra={
                    "blobPath": blob_path,
                    "attempt": attempt + 1,
                    "maxAttempts": COSMOS_LOOKUP_RETRY_ATTEMPTS,
                    "step": "COSMOS_LOOKUP_RETRY",
                },
            )
            await asyncio.sleep(COSMOS_LOOKUP_RETRY_SLEEP_SEC)

    raise RuntimeError(
        f"Handshake failed: No metadata record found in Cosmos for blob path {blob_path} after 10 seconds. Ensure fn_ingest_blob succeeded."
    )


async def _wait_for_blob_copy_success(
    raw_blob_client: Any,
    doc_id: str,
    filename: str,
    full_name: str,
) -> None:
    """Poll blob properties until copy_status is not 'pending' (max COPY_POLL_MAX_ATTEMPTS)."""
    for attempt in range(COPY_POLL_MAX_ATTEMPTS):
        props = await raw_blob_client.get_blob_properties()
        copy = getattr(props, "copy", None)
        status = getattr(copy, "status", "success").lower() if copy else "success"

        if status in ("success", "complete"):
            if attempt > 0:
                logger.info(
                    "COPY_STATUS_READY",
                    extra={
                        "docId": doc_id,
                        "doc_filename": filename,
                        "attempt": attempt + 1,
                        "step": "COPY_STATUS_READY",
                    },
                )
            return

        if status == "failed":
            desc = getattr(copy, "status_description", None) or "Copy failed"
            raise RuntimeError(f"Blob copy failed: {desc}")

        logger.info(
            "COPY_STATUS_PENDING",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "attempt": attempt + 1,
                "maxAttempts": COPY_POLL_MAX_ATTEMPTS,
                "step": "COPY_STATUS_PENDING",
            },
        )
        await asyncio.sleep(COPY_POLL_SLEEP_SEC)

    raise RuntimeError(
        f"Blob copy still pending after {COPY_POLL_MAX_ATTEMPTS} attempts: {full_name}"
    )


async def main(myblob: func.InputStream) -> None:
    """Run OCR for a document blob in the raw container (async)."""
    doc_id: Optional[str] = None
    filename: str = ""
    policy_type: Optional[str] = None

    try:
        # Fail-fast: load all required config at start.
        env = _get_required_env()
        conn_str = env["AzureWebJobsStorage"]

        full_name = myblob.name or ""
        doc_id, filename, policy_type_hint = _parse_raw_blob_name(full_name)

        # Derive a partition key hint from the blob path when possible to keep
        # the primary lookup partition-scoped for performance.
        if policy_type_hint is None:
            parts = full_name.split("/")
            if len(parts) >= 2 and parts[0] == "incoming":
                policy_type_hint = parts[1]

        policy_type = policy_type_hint

        async with BlobServiceClient.from_connection_string(conn_str) as blob_service:
            raw_container = blob_service.get_container_client("raw")
            raw_blob_client = raw_container.get_blob_client(f"{doc_id}/{filename}")

            # Wait for fn_ingest_blob to finish copying before reading the blob.
            await _wait_for_blob_copy_success(
                raw_blob_client, doc_id, filename, full_name
            )

        logger.info(
            "COSMOS_LOOKUP_START",
            extra={
                "docId": doc_id,
                "blobName": full_name,
                "policyTypeHint": policy_type_hint,
                "step": "COSMOS_LOOKUP_START",
            },
        )
        container = await get_cosmos_container_from_env_async()
        doc, policy_type = await _get_document_and_partition_key_async(
            container, full_name, policy_type_hint
        )
        if not policy_type:
            logger.error(
                "DOC_MISSING_POLICY_TYPE",
                extra={
                    "docId": doc_id,
                    "blobName": full_name,
                    "policyTypeHint": policy_type_hint,
                    "step": "DOC_LOOKUP_FAILED",
                },
            )
            raise RuntimeError(
                f"Handshake failed: Document found for blob path {full_name} but policyType is missing in Cosmos."
            )

        logger.info(f"Found document {doc['id']} for blob {full_name}")

        stage_details = {
            "stage": "ocr",
            "filename": filename,
        }

        await update_document_status_async(
            container=container,
            doc_id=doc_id,
            partition_key=policy_type,
            new_status=OCR_STARTED,
            error_message=None,
            stage_details=stage_details,
            logger=logger,
        )

        logger.info(
            "OCR_STARTED",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "policyType": policy_type,
                "step": "OCR_STARTED",
            },
        )

        di_wrapper = DocumentIntelligenceWrapper.from_env()
        blob_bytes = myblob.read()
        blob_size = len(blob_bytes) if blob_bytes is not None else 0

        logger.info(
            "OCR_BLOB_SIZE_BYTES",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "policyType": policy_type,
                "blobSize": blob_size,
                "step": "OCR_BLOB_SIZE_BYTES",
            },
        )

        if not blob_bytes:
            logger.error(
                "OCR_EMPTY_BLOB",
                extra={
                    "docId": doc_id,
                    "doc_filename": filename,
                    "policyType": policy_type,
                    "blobSize": blob_size,
                    "step": "OCR_EMPTY_BLOB",
                },
            )
            raise RuntimeError("Blob content is empty; skipping OCR.")

        seekable_stream = io.BytesIO(blob_bytes)
        seekable_stream.seek(0)

        logger.info(
            "OCR_DOCUMENT_INTELLIGENCE_START",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "policyType": policy_type,
                "blobSize": blob_size,
                "step": "OCR_DOCUMENT_INTELLIGENCE_START",
            },
        )
        try:
            ocr_result = await di_wrapper.analyze_document_stream_async(
                seekable_stream
            )
        except Exception as ocr_exc:
            logger.exception(
                "OCR Document Intelligence call failed",
                extra={
                    "docId": doc_id,
                    "doc_filename": filename,
                    "policyType": policy_type,
                    "step": "OCR_DOCUMENT_INTELLIGENCE_FAILED",
                },
            )
            raise
        logger.info(
            "OCR_DOCUMENT_INTELLIGENCE_END",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "policyType": policy_type,
                "step": "OCR_DOCUMENT_INTELLIGENCE_END",
            },
        )

        ocr_raw_path = get_ocr_raw_blob_path(doc_id)
        ocr_layout_path = get_ocr_layout_blob_path(doc_id)
        ocr_raw_container_name, ocr_raw_blob_name = ocr_raw_path.split("/", 1)
        ocr_layout_container_name, ocr_layout_blob_name = ocr_layout_path.split(
            "/", 1
        )

        ocr_payload = json.dumps(
            ocr_result, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        layout_payload = json.dumps(
            normalize_layout_result(doc_id, di_wrapper.model_id, ocr_result),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        async with BlobServiceClient.from_connection_string(conn_str) as blob_service:
            ocr_raw_container = blob_service.get_container_client(
                ocr_raw_container_name
            )
            ocr_raw_blob = ocr_raw_container.get_blob_client(ocr_raw_blob_name)
            await ocr_raw_blob.upload_blob(ocr_payload, overwrite=True)

        logger.info(
            "OCR_RAW_WRITTEN",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "policyType": policy_type,
                "ocrRawPath": ocr_raw_path,
                "step": "OCR_RAW_WRITTEN",
            },
        )

        async with BlobServiceClient.from_connection_string(conn_str) as blob_service:
            ocr_layout_container = blob_service.get_container_client(
                ocr_layout_container_name
            )
            ocr_layout_blob = ocr_layout_container.get_blob_client(
                ocr_layout_blob_name
            )
            await ocr_layout_blob.upload_blob(layout_payload, overwrite=True)

        logger.info(
            "OCR_LAYOUT_WRITTEN",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "policyType": policy_type,
                "ocrLayoutPath": ocr_layout_path,
                "step": "OCR_LAYOUT_WRITTEN",
            },
        )

        completion_details = {
            "stage": "ocr",
            "filename": filename,
            "ocrRawPath": ocr_raw_path,
            "ocrLayoutPath": ocr_layout_path,
            "modelId": di_wrapper.model_id,
        }

        container = await get_cosmos_container_from_env_async()
        await update_document_status_async(
            container=container,
            doc_id=doc_id,
            partition_key=policy_type,
            new_status=OCR_COMPLETE,
            error_message=None,
            stage_details=completion_details,
            logger=logger,
        )

        logger.info(
            "OCR_COMPLETE",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "policyType": policy_type,
                "ocrRawPath": ocr_raw_path,
                "step": "OCR_COMPLETE",
            },
        )

        async with BlobServiceClient.from_connection_string(conn_str) as blob_service:
            raw_container = blob_service.get_container_client("raw")
            raw_blob = raw_container.get_blob_client(f"{doc_id}/{filename}")
            logger.info(
                "RAW_BLOB_DELETE_STARTED",
                extra={
                    "docId": doc_id,
                    "doc_filename": filename,
                    "rawBlobPath": full_name,
                    "step": "RAW_BLOB_DELETE_STARTED",
                },
            )
            try:
                await raw_blob.delete_blob()
                logger.info(
                    "RAW_BLOB_DELETED",
                    extra={
                        "docId": doc_id,
                        "doc_filename": filename,
                        "rawBlobPath": full_name,
                        "step": "RAW_BLOB_DELETED",
                    },
                )
            except ResourceNotFoundError:
                logger.info(
                    "RAW_BLOB_ALREADY_MISSING",
                    extra={
                        "docId": doc_id,
                        "doc_filename": filename,
                        "rawBlobPath": full_name,
                        "step": "RAW_BLOB_ALREADY_MISSING",
                    },
                )
            except Exception as del_exc:
                logger.warning(
                    "RAW_BLOB_DELETE_FAILED",
                    extra={
                        "docId": doc_id,
                        "doc_filename": filename,
                        "rawBlobPath": full_name,
                        "step": "RAW_BLOB_DELETE_FAILED",
                        "error": str(del_exc),
                    },
                    exc_info=True,
                )

    except Exception as exc:
        logger.exception(
            "fn_run_ocr failed",
            extra={
                "docId": doc_id,
                "doc_filename": filename,
                "policyType": policy_type,
                "step": "OCR_FAILED",
            },
        )

        if policy_type and doc_id:
            try:
                container = await get_cosmos_container_from_env_async()
                failure_details = {
                    "stage": "ocr",
                    "filename": filename,
                }
                await update_document_status_async(
                    container=container,
                    doc_id=doc_id,
                    partition_key=policy_type,
                    new_status=OCR_FAILED,
                    error_message=str(exc),
                    stage_details=failure_details,
                    logger=logger,
                )
            except Exception:
                logger.exception(
                    "Failed to update status to OCR_FAILED",
                    extra={
                        "docId": doc_id,
                        "doc_filename": filename,
                        "policyType": policy_type,
                        "step": "OCR_FAILED_STATUS_UPDATE_FAILED",
                    },
                )

        raise
