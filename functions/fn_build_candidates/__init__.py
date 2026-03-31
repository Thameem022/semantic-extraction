"""Blob-triggered candidate builder: ocr-layout -> candidates JSON + Cosmos status."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional, Tuple

import azure.functions as func
from azure.storage.blob.aio import BlobServiceClient

from shared import CANDIDATES_FAILED, CANDIDATES_GENERATED, Candidate, CandidateBuilder
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
OVERLAP_THRESHOLD = 0.5
SOURCE_PRIORITY = {"Pattern": 1, "Table": 2, "KV": 3}

# CandidateBuilder.build() returns only deterministic KV matches for Applicant Info.
_APPLICANT_INFO_FIELD_IDS = frozenset(
    {
        "applicant_name",
        "insured_address",
        "naics_code",
        "sic_naics_code",
        "year_established",
        "telephone_number",
        "website",
        "business_description",
        "emp_full_time",
        "email_address",
    }
)


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

    # Host-provided names often include container prefix.
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


def _polygon_to_aabb(polygon: list[float]) -> Optional[tuple[float, float, float, float]]:
    if not isinstance(polygon, list) or len(polygon) != 8:
        return None
    xs = [float(polygon[i]) for i in range(0, 8, 2)]
    ys = [float(polygon[i]) for i in range(1, 8, 2)]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if max_x <= min_x or max_y <= min_y:
        return None
    return min_x, min_y, max_x, max_y


def _overlap_score(a: list[float], b: list[float]) -> float:
    a_box = _polygon_to_aabb(a)
    b_box = _polygon_to_aabb(b)
    if not a_box or not b_box:
        return 0.0

    a_min_x, a_min_y, a_max_x, a_max_y = a_box
    b_min_x, b_min_y, b_max_x, b_max_y = b_box

    inter_w = max(0.0, min(a_max_x, b_max_x) - max(a_min_x, b_min_x))
    inter_h = max(0.0, min(a_max_y, b_max_y) - max(a_min_y, b_min_y))
    inter_area = inter_w * inter_h
    if inter_area <= 0:
        return 0.0

    a_area = (a_max_x - a_min_x) * (a_max_y - a_min_y)
    b_area = (b_max_x - b_min_x) * (b_max_y - b_min_y)
    union = a_area + b_area - inter_area
    if union <= 0:
        return 0.0

    iou = inter_area / union
    contained_overlap = inter_area / min(a_area, b_area)
    return max(iou, contained_overlap)


def _source_tokens(value: str) -> list[str]:
    tokens = [token.strip() for token in str(value).split("|") if token.strip()]
    seen: set[str] = set()
    ordered: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            ordered.append(token)
    return ordered


def _merge_sources(a: str, b: str) -> str:
    merged = set(_source_tokens(a)) | set(_source_tokens(b))
    ordered = sorted(merged, key=lambda token: SOURCE_PRIORITY.get(token, 0), reverse=True)
    return " | ".join(ordered)


def _source_rank(candidate: Candidate) -> int:
    tokens = _source_tokens(candidate.source)
    if not tokens:
        return 0
    return max(SOURCE_PRIORITY.get(token, 0) for token in tokens)


def _prefer_candidate(a: Candidate, b: Candidate) -> Candidate:
    rank_a = _source_rank(a)
    rank_b = _source_rank(b)
    if rank_b > rank_a:
        return b
    if rank_a > rank_b:
        return a
    return b if b.confidence > a.confidence else a


def _merge_candidate_pair(a: Candidate, b: Candidate) -> Candidate:
    winner = _prefer_candidate(a, b)
    source = _merge_sources(a.source, b.source)
    return winner.model_copy(update={"source": source})


def _deduplicate_candidates(candidates: list[Candidate]) -> list[Candidate]:
    deduped: list[Candidate] = []
    for candidate in candidates:
        merged = False
        for idx, existing in enumerate(deduped):
            if candidate.fieldId != existing.fieldId:
                continue
            if int(candidate.pageNumber) != int(existing.pageNumber):
                continue
            if _overlap_score(candidate.boundingBox, existing.boundingBox) < OVERLAP_THRESHOLD:
                continue
            deduped[idx] = _merge_candidate_pair(existing, candidate)
            merged = True
            break
        if not merged:
            deduped.append(candidate)
    return deduped


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
        # We only use build(), which returns kv_hunter() results (Applicant Info KV only).
        combined = builder.build()
        deduped = _deduplicate_candidates(combined)
        deduped = [c for c in deduped if c.fieldId in _APPLICANT_INFO_FIELD_IDS]

        if not deduped:
            logger.warning(
                "No candidates found for document",
                extra={"docId": doc_id, "policyType": policy_type, "step": "CANDIDATES_EMPTY"},
            )

        candidates_path = get_candidates_blob_path(doc_id)
        candidates_container_name, candidates_blob_name = candidates_path.split("/", 1)
        output_payload = json.dumps(
            [candidate.model_dump() for candidate in deduped],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        async with BlobServiceClient.from_connection_string(conn_str) as blob_service:
            candidates_container = blob_service.get_container_client(candidates_container_name)
            candidates_blob = candidates_container.get_blob_client(candidates_blob_name)
            await candidates_blob.upload_blob(output_payload, overwrite=True)

        stage_details = {
            "stage": "candidates",
            "candidateCount": len(deduped),
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
                "candidateCount": len(deduped),
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
