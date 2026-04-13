"""Blob-triggered candidate builder: ocr-layout -> structured extraction JSON + Cosmos status."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional, Tuple

import azure.functions as func
from azure.storage.blob.aio import BlobServiceClient

from shared import CANDIDATES_FAILED, CANDIDATES_GENERATED, CandidateBuilder
from shared.blob_paths import get_candidates_blob_path
from shared.cosmos_helpers import (
    get_cosmos_container_from_env_async,
    update_document_status_async,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.storage").setLevel(logging.WARNING)

COSMOS_LOOKUP_RETRY_ATTEMPTS = 5
COSMOS_LOOKUP_RETRY_SLEEP_SEC = 2.0


def _get_required_env() -> dict[str, str]:
    required = [
        "AzureWebJobsStorage",
        "COSMOS_ENDPOINT",
        "COSMOS_DB_NAME",
        "COSMOS_CONTAINER_NAME",
    ]
    out: dict[str, str] = {}
    for key in required:
        val = os.environ.get(key)
        if not val or not str(val).strip():
            raise RuntimeError(f"Missing required environment variable: {key}")
        out[key] = str(val).strip()
    return out


def _parse_layout_blob_name(blob_name: str) -> str:
    if not blob_name:
        raise ValueError("Blob name is empty")
    parts = Path(blob_name).parts
    if len(parts) < 3:
        raise ValueError(f"Unexpected blob name format: {blob_name!r}")

    if parts[0] == "ocr-layout":
        _, doc_id, filename = parts[0], parts[1], parts[-1]
    else:
        doc_id, filename = parts[-2], parts[-1]

    if filename != "layout.json":
        raise ValueError(f"Expected blob filename 'layout.json', got: {filename!r}")
    if not doc_id:
        raise ValueError(f"Missing docId in blob path: {blob_name!r}")
    return doc_id


async def _get_document_and_partition_key_async(
    container: Any, doc_id: str
) -> Tuple[Optional[dict], Optional[str]]:
    query = "SELECT * FROM c WHERE c.id = @docId OR c.docId = @docId"
    kwargs = {"query": query, "parameters": [{"name": "@docId", "value": doc_id}]}

    async def _run_query() -> list[dict]:
        items: list[dict] = []
        async for item in container.query_items(**kwargs):
            items.append(item)
        return items

    for attempt in range(COSMOS_LOOKUP_RETRY_ATTEMPTS):
        items = await _run_query()
        if items:
            doc = items[0]
            return doc, doc.get("policyType")
        if attempt < COSMOS_LOOKUP_RETRY_ATTEMPTS - 1:
            logger.warning(
                "Document %s not found yet, retrying (Attempt %d/%d)...",
                doc_id,
                attempt + 1,
                COSMOS_LOOKUP_RETRY_ATTEMPTS,
                extra={
                    "docId": doc_id,
                    "attempt": attempt + 1,
                    "maxAttempts": COSMOS_LOOKUP_RETRY_ATTEMPTS,
                    "step": "COSMOS_LOOKUP_RETRY",
                },
            )
            await asyncio.sleep(COSMOS_LOOKUP_RETRY_SLEEP_SEC)
    raise RuntimeError(
        f"Handshake failed: No metadata record found in Cosmos for docId {doc_id} after 10 seconds."
    )


async def main(myblob: func.InputStream) -> None:
    doc_id: Optional[str] = None
    policy_type: Optional[str] = None

    try:
        env = _get_required_env()
        conn_str = env["AzureWebJobsStorage"]

        blob_name = myblob.name or ""
        doc_id = _parse_layout_blob_name(blob_name)

        logger.info(
            "OCR_LOOKUP_START",
            extra={"docId": doc_id, "blobName": blob_name, "step": "OCR_LOOKUP_START"},
        )

        container = await get_cosmos_container_from_env_async()
        doc, policy_type = await _get_document_and_partition_key_async(container, doc_id)
        if not doc or not policy_type:
            raise RuntimeError(
                f"Handshake failed: Document found for docId {doc_id} but policyType is missing in Cosmos."
            )

        payload = myblob.read()
        layout_json = json.loads(payload.decode("utf-8"))

        builder = CandidateBuilder(layout_json)
        package = await builder.build()

        candidates_path = get_candidates_blob_path(doc_id)
        candidates_container_name, candidates_blob_name = candidates_path.split("/", 1)
        output_payload = json.dumps(
            package.model_dump(),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        async with BlobServiceClient.from_connection_string(conn_str) as blob_service:
            candidates_container = blob_service.get_container_client(candidates_container_name)
            candidates_blob = candidates_container.get_blob_client(candidates_blob_name)
            await candidates_blob.upload_blob(output_payload, overwrite=True)

        non_null_count = sum(
            1
            for section in package.model_dump().values()
            if isinstance(section, dict)
            for v in section.values()
            if v is not None
        )

        stage_details = {
            "stage": "candidates",
            "extractedFieldCount": non_null_count,
            "timestamp": utc_now_iso(),
            "candidatesPath": candidates_path,
        }
        await update_document_status_async(
            container=container,
            doc_id=doc_id,
            partition_key=policy_type,
            new_status=CANDIDATES_GENERATED,
            error_message=None,
            stage_details=stage_details,
            logger=logger,
        )

        logger.info(
            "CANDIDATES_GENERATED",
            extra={
                "docId": doc_id,
                "policyType": policy_type,
                "extractedFieldCount": non_null_count,
                "candidatesPath": candidates_path,
                "step": "CANDIDATES_GENERATED",
            },
        )
    except Exception as exc:
        logger.exception(
            "fn_build_candidates failed",
            extra={"docId": doc_id, "policyType": policy_type, "step": "CANDIDATES_FAILED"},
        )

        if policy_type and doc_id:
            try:
                container = await get_cosmos_container_from_env_async()
                await update_document_status_async(
                    container=container,
                    doc_id=doc_id,
                    partition_key=policy_type,
                    new_status=CANDIDATES_FAILED,
                    error_message=str(exc),
                    stage_details={"stage": "candidates", "timestamp": utc_now_iso()},
                    logger=logger,
                )
            except Exception:
                logger.exception(
                    "Failed to update status to CANDIDATES_FAILED",
                    extra={
                        "docId": doc_id,
                        "policyType": policy_type,
                        "step": "CANDIDATES_FAILED_STATUS_UPDATE_FAILED",
                    },
                )
        raise
