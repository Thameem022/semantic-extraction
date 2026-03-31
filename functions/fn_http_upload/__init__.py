from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

import azure.functions as func
from azure.storage.blob import ContentSettings, BlobServiceClient

from shared.cosmos_helpers import get_cosmos_container_from_env, utc_now_iso
from shared.statuses import RECEIVED

logger = logging.getLogger(__name__)


def _cors_headers() -> dict[str, str]:
    # Allow the local dev Next.js origin and also support wildcard when running
    # locally without App Service CORS configuration.
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def _get_required_env() -> dict[str, str]:
    required = ["AzureWebJobsStorage", "COSMOS_DB_NAME", "COSMOS_CONTAINER_NAME", "COSMOS_ENDPOINT"]
    out: dict[str, str] = {}
    for key in required:
        val = os.environ.get(key)
        if not val or not str(val).strip():
            raise RuntimeError(f"Missing required environment variable: {key}")
        out[key] = str(val).strip()
    return out


def _get_pdf_bytes(req: func.HttpRequest) -> bytes:
    """
    Accept raw PDF bytes in the request body.
    Frontend should send: fetch(url, { method: 'POST', body: fileBlob, headers: { 'Content-Type': 'application/pdf' } })
    """
    body = req.get_body()
    if not body:
        raise ValueError("Missing request body (expected raw PDF bytes).")
    return body


def _extract_upload_payload(req: func.HttpRequest) -> tuple[bytes, str | None, str]:
    """
    Extract upload payload from multipart form-data (preferred) or raw body.
    Returns: (pdf_bytes, original_filename, content_type)
    """
    default_content_type = (req.headers.get("content-type") or "").strip() or "application/pdf"

    files = getattr(req, "files", None)
    if files:
        try:
            file_items = list(files.values()) if hasattr(files, "values") else list(files)
            if file_items:
                file_obj = file_items[0]
                original_filename = (
                    getattr(file_obj, "filename", None) or getattr(file_obj, "name", None) or None
                )
                file_content_type = (
                    getattr(file_obj, "content_type", None) or default_content_type
                )
                if hasattr(file_obj, "stream") and hasattr(file_obj.stream, "read"):
                    file_bytes = file_obj.stream.read()
                elif hasattr(file_obj, "read"):
                    file_bytes = file_obj.read()
                else:
                    file_bytes = b""
                if not file_bytes:
                    raise ValueError("Uploaded multipart file is empty.")
                return bytes(file_bytes), original_filename, file_content_type
        except Exception:
            logger.exception("Failed to parse multipart upload payload")
            raise

    # Fallback: raw body uploads.
    raw_bytes = _get_pdf_bytes(req)
    return raw_bytes, None, default_content_type


def main(req: func.HttpRequest) -> func.HttpResponse:
    """POST PDF -> {docId} + upload to incoming + Cosmos RECEIVED doc."""
    headers = _cors_headers()
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=headers)

    if req.method != "POST":
        return func.HttpResponse("Method Not Allowed", status_code=405, headers=headers)

    try:
        _get_required_env()

        pdf_bytes, original_filename, content_type = _extract_upload_payload(req)

        doc_id = str(uuid.uuid4())
        now = utc_now_iso()
        filename = f"{doc_id}.pdf"
        display_filename = (original_filename or filename).strip()

        # Create initial tracking doc so the UI can start polling immediately.
        cosmos_container = get_cosmos_container_from_env()
        initial_doc: dict[str, Any] = {
            "id": doc_id,
            "docId": doc_id,
            "filename": filename,
            "originalFilename": display_filename,
            "uploadedAtUtc": now,
            "policyType": "unknown",
            # Cosmos unique key policy requires /sha256 values; use a per-doc placeholder.
            "sha256": f"pending-{doc_id}",
            "status": RECEIVED,
            "statusUpdatedAtUtc": now,
            # Pre-populate expected paths so status queries and troubleshooting are consistent.
            "sourceBlobPath": f"incoming/{filename}",
            "rawBlobPath": f"raw/{doc_id}/{filename}",
            "contentType": content_type,
        }
        cosmos_container.upsert_item(initial_doc)

        # Upload PDF to the existing pipeline's blob trigger.
        conn_str = os.environ["AzureWebJobsStorage"]
        incoming_container_name = "incoming"
        blob_service = BlobServiceClient.from_connection_string(conn_str)
        incoming_container = blob_service.get_container_client(incoming_container_name)
        blob_client = incoming_container.get_blob_client(filename)
        blob_client.upload_blob(
            pdf_bytes,
            overwrite=False,
            content_settings=ContentSettings(content_type=content_type),
        )

        logger.info("fn_http_upload_OK", extra={"docId": doc_id, "docFilename": filename})

        return func.HttpResponse(
            json.dumps({"docId": doc_id, "filename": display_filename}, ensure_ascii=False),
            status_code=202,
            mimetype="application/json",
            headers=headers,
        )
    except ValueError as ve:
        return func.HttpResponse(str(ve), status_code=400, headers=headers)
    except Exception as exc:
        logger.exception("fn_http_upload failed")
        return func.HttpResponse(
            json.dumps({"error": str(exc)}, ensure_ascii=False),
            status_code=500,
            mimetype="application/json",
            headers=headers,
        )

