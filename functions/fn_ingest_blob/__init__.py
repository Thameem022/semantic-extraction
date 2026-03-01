"""Blob ingestion function: incoming -> Cosmos doc + raw/{docId}/{filename}."""

import hashlib
import logging
import os
import time
import uuid
from datetime import datetime, timezone

import azure.functions as func
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

INCOMING_CONTAINER = "incoming"
COPY_POLL_INTERVAL_SEC = 1.5
COPY_TIMEOUT_SEC = 60

logger = logging.getLogger(__name__)


def main(myblob: func.InputStream) -> None:
    """Process blob from incoming container: Cosmos upsert, copy to raw, delete source."""
    doc_id: str | None = None
    name = ""

    try:
        name = myblob.name or ""
        if "/" in name:
            blob_name = name.split("/", 1)[1]
        else:
            blob_name = name

        doc_id = str(uuid.uuid4())
        policy_type = "unknown"
        original_filename = blob_name

        try:
            blob_bytes = myblob.read()
            sha256hex = hashlib.sha256(blob_bytes).hexdigest()
        except Exception:
            logger.exception("RECEIVED: Failed to read blob or compute sha256", extra={"docId": doc_id, "blobName": name})
            raise

        logger.info(
            "RECEIVED",
            extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "RECEIVED"},
        )

        conn_str = os.environ["AzureWebJobsStorage"]
        blob_service = BlobServiceClient.from_connection_string(conn_str)
        incoming_client = blob_service.get_container_client(INCOMING_CONTAINER)
        source_blob = incoming_client.get_blob_client(blob_name)

        try:
            props = source_blob.get_blob_properties()
        except Exception:
            logger.exception("RECEIVED: Failed to get blob properties", extra={"docId": doc_id, "blobName": name})
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

        uploaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        doc = {
            "id": doc_id,
            "docId": doc_id,
            "filename": original_filename,
            "uploadedAtUtc": uploaded_at,
            "policyType": policy_type,
            "sha256": sha256hex,
            "status": "RECEIVED",
            "sourceBlobPath": f"incoming/{blob_name}",
            "contentType": content_type,
            "sizeBytes": size_bytes,
            "etag": etag,
        }

        cosmos_endpoint = os.environ["COSMOS_ENDPOINT"]
        cosmos_db = os.environ["COSMOS_DB_NAME"]
        cosmos_container_name = os.environ["COSMOS_CONTAINER_NAME"]
        cred = DefaultAzureCredential()
        cosmos_client = CosmosClient(cosmos_endpoint, credential=cred)
        db = cosmos_client.get_database_client(cosmos_db)
        container = db.get_container_client(cosmos_container_name)

        try:
            container.upsert_item(doc)
            logger.info(
                "COSMOS_UPSERT_OK",
                extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "COSMOS_UPSERT_OK"},
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

        raw_container_name = os.environ.get("RAW_CONTAINER_NAME", "raw")
        raw_container = blob_service.get_container_client(raw_container_name)
        dest_path = f"{doc_id}/{original_filename}"
        dest_blob = raw_container.get_blob_client(dest_path)

        logger.info(
            "COPY_STARTED",
            extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "COPY_STARTED"},
        )

        dest_blob.start_copy_from_url(source_blob.url)
        start = time.monotonic()
        while True:
            dest_props = dest_blob.get_blob_properties()
            copy_info = getattr(dest_props, "copy", None)
            status = copy_info.status if copy_info else "success"
            if status in ("success", "complete"):
                break
            if status == "failed":
                msg = (copy_info.status_description if copy_info else None) or "Copy failed"
                raise RuntimeError(f"Blob copy failed: {msg}")
            if time.monotonic() - start > COPY_TIMEOUT_SEC:
                raise RuntimeError("Blob copy timed out")
            time.sleep(COPY_POLL_INTERVAL_SEC)

        logger.info(
            "COPY_SUCCEEDED",
            extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "COPY_SUCCEEDED"},
        )

        source_blob.delete_blob()
        logger.info(
            "INCOMING_DELETED",
            extra={"docId": doc_id, "blobName": name, "policyType": policy_type, "step": "INCOMING_DELETED"},
        )
    except Exception:
        logger.exception("fn_ingest_blob failed", extra={"docId": doc_id, "blobName": name})
        raise
