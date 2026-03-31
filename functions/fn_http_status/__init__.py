from __future__ import annotations

import json
import logging
import os
from typing import Any

import azure.functions as func
from azure.storage.blob import BlobServiceClient

from shared.blob_paths import get_candidates_blob_path
from shared.cosmos_helpers import get_cosmos_container_from_env
from shared.statuses import CANDIDATES_GENERATED

logger = logging.getLogger(__name__)


def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def _get_doc_id(req: func.HttpRequest) -> str | None:
    # Azure Functions merges route + query params into req.params; we still
    # defensively check a few common keys.
    params: dict[str, Any] = getattr(req, "params", None) or {}
    doc_id = params.get("docId") or params.get("doc_id")
    if isinstance(doc_id, str):
        doc_id = doc_id.strip()
    else:
        doc_id = None
    return doc_id or None


def main(req: func.HttpRequest) -> func.HttpResponse:
    """GET doc status; when complete, include candidates.json payload."""
    headers = _cors_headers()
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=headers)

    if req.method != "GET":
        return func.HttpResponse("Method Not Allowed", status_code=405, headers=headers)

    try:
        doc_id = _get_doc_id(req)
        if not doc_id:
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameter: docId"}),
                status_code=400,
                mimetype="application/json",
                headers=headers,
            )

        cosmos_container = get_cosmos_container_from_env()

        query = "SELECT * FROM c WHERE c.id = @docId OR c.docId = @docId"
        items = list(
            cosmos_container.query_items(
                query=query,
                parameters=[{"name": "@docId", "value": doc_id}],
                enable_cross_partition_query=True,
            )
        )
        if not items:
            return func.HttpResponse(
                json.dumps({"docId": doc_id, "error": "Document not found"}),
                status_code=404,
                mimetype="application/json",
                headers=headers,
            )

        doc = items[0]
        status = doc.get("status")
        if not status:
            return func.HttpResponse(
                json.dumps({"docId": doc_id, "error": "Status missing in Cosmos doc"}),
                status_code=500,
                mimetype="application/json",
                headers=headers,
            )

        if status != CANDIDATES_GENERATED:
            return func.HttpResponse(
                json.dumps(
                    {
                        "docId": doc.get("id"),
                        "filename": doc.get("originalFilename") or doc.get("filename"),
                        "status": status,
                    },
                    ensure_ascii=False,
                ),
                status_code=200,
                mimetype="application/json",
                headers=headers,
            )

        # Status is complete: fetch candidates.json from candidates/{docId}/.
        candidates_path = get_candidates_blob_path(doc_id)
        container_name, blob_name = candidates_path.split("/", 1)

        conn_str = os.environ["AzureWebJobsStorage"]
        blob_service = BlobServiceClient.from_connection_string(conn_str)
        blob_client = blob_service.get_container_client(container_name).get_blob_client(blob_name)
        data = blob_client.download_blob().readall()
        payload_bytes = data if isinstance(data, (bytes, bytearray)) else bytes(data)
        candidates_json = json.loads(payload_bytes.decode("utf-8"))

        return func.HttpResponse(
            json.dumps(
                {
                    "docId": doc.get("id"),
                    "filename": doc.get("originalFilename") or doc.get("filename"),
                    "status": status,
                    "candidates": candidates_json,
                },
                ensure_ascii=False,
            ),
            status_code=200,
            mimetype="application/json",
            headers=headers,
        )
    except Exception as exc:
        logger.exception("fn_http_status failed")
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=500,
            mimetype="application/json",
            headers=headers,
        )

