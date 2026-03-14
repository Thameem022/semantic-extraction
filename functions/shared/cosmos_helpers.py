"""Reusable Cosmos helpers for document status transitions."""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from azure.cosmos import CosmosClient
from azure.cosmos.aio import CosmosClient as CosmosClientAio
from azure.identity import DefaultAzureCredential

from shared.statuses import is_valid_status

_UNSET = object()

# Module-level Cosmos clients to enable connection pooling and reuse across
# function invocations. These are created lazily on first use.
_COSMOS_CLIENT: Optional[CosmosClient] = None
_COSMOS_CLIENT_AIO: Optional[CosmosClientAio] = None


def _get_sync_cosmos_client() -> CosmosClient:
    """Return a singleton sync CosmosClient, creating it on first use."""
    global _COSMOS_CLIENT
    if _COSMOS_CLIENT is None:
        cosmos_endpoint = os.environ["COSMOS_ENDPOINT"]
        cred = DefaultAzureCredential()
        _COSMOS_CLIENT = CosmosClient(cosmos_endpoint, credential=cred)
    return _COSMOS_CLIENT


def _get_async_cosmos_client() -> CosmosClientAio:
    """Return a singleton async CosmosClientAio, creating it on first use."""
    global _COSMOS_CLIENT_AIO
    if _COSMOS_CLIENT_AIO is None:
        cosmos_endpoint = os.environ["COSMOS_ENDPOINT"]
        cred = DefaultAzureCredential()
        _COSMOS_CLIENT_AIO = CosmosClientAio(cosmos_endpoint, credential=cred)
    return _COSMOS_CLIENT_AIO


def utc_now_iso() -> str:
    """Return UTC timestamp in the pipeline's canonical format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def get_cosmos_container_from_env():
    """Build and return the configured Cosmos container client from env vars."""
    cosmos_db = os.environ["COSMOS_DB_NAME"]
    cosmos_container_name = os.environ["COSMOS_CONTAINER_NAME"]

    cosmos_client = _get_sync_cosmos_client()
    db = cosmos_client.get_database_client(cosmos_db)
    return db.get_container_client(cosmos_container_name)


def update_document_status(
    *,
    container,
    doc_id: str,
    partition_key: str,
    new_status: str,
    error_message: Any = _UNSET,
    stage_details: Any = _UNSET,
    logger: logging.Logger | None = None,
) -> dict:
    """
    Safely update document status fields while preserving all existing fields.

    Behavior:
    - Reads the current document.
    - Updates status + statusUpdatedAtUtc.
    - Optionally updates/clears errorMessage and stageDetails.
    - Replaces the same document in Cosmos.
    """
    if not is_valid_status(new_status):
        raise ValueError(f"Invalid status: {new_status}")

    log = logger or logging.getLogger(__name__)
    doc = container.read_item(item=doc_id, partition_key=partition_key)
    old_status = doc.get("status")

    doc["status"] = new_status
    doc["statusUpdatedAtUtc"] = utc_now_iso()

    if error_message is not _UNSET:
        if error_message is None:
            doc.pop("errorMessage", None)
        else:
            doc["errorMessage"] = str(error_message)

    if stage_details is not _UNSET:
        if stage_details is None:
            doc.pop("stageDetails", None)
        else:
            doc["stageDetails"] = stage_details

    # Use the full document for replacement to preserve all existing fields.
    # The SDK accepts either the item dict or item id as "item"; passing the
    # document we just mutated is the safest option.
    updated = container.replace_item(item=doc, body=doc)

    log.info(
        "COSMOS_STATUS_TRANSITION",
        extra={
            "docId": doc_id,
            "previousStatus": old_status,
            "newStatus": new_status,
            "statusUpdatedAtUtc": doc["statusUpdatedAtUtc"],
            "step": "COSMOS_STATUS_TRANSITION",
        },
    )

    return updated


# ---------------------------------------------------------------------------
# Async variants for use with asyncio (e.g. fn_run_ocr).
# ---------------------------------------------------------------------------


async def get_cosmos_container_from_env_async() -> Any:
    """Async helper returning the configured Cosmos container (aio client).
    Callers should use this helper rather than creating their own client to benefit
    from the shared singleton and connection pooling."""
    cosmos_db = os.environ["COSMOS_DB_NAME"]
    cosmos_container_name = os.environ["COSMOS_CONTAINER_NAME"]
    client = _get_async_cosmos_client()
    db = client.get_database_client(cosmos_db)
    container = db.get_container_client(cosmos_container_name)
    return container


async def update_document_status_async(
    *,
    container: Any,
    doc_id: str,
    partition_key: str,
    new_status: str,
    error_message: Any = _UNSET,
    stage_details: Any = _UNSET,
    logger: logging.Logger | None = None,
) -> dict:
    """Async: update document status (read, mutate, replace) in Cosmos."""
    if not is_valid_status(new_status):
        raise ValueError(f"Invalid status: {new_status}")

    log = logger or logging.getLogger(__name__)
    doc = await container.read_item(item=doc_id, partition_key=partition_key)
    old_status = doc.get("status")

    doc["status"] = new_status
    doc["statusUpdatedAtUtc"] = utc_now_iso()

    if error_message is not _UNSET:
        if error_message is None:
            doc.pop("errorMessage", None)
        else:
            doc["errorMessage"] = str(error_message)

    if stage_details is not _UNSET:
        if stage_details is None:
            doc.pop("stageDetails", None)
        else:
            doc["stageDetails"] = stage_details

    updated = await container.replace_item(item=doc, body=doc)
    log.info(
        "COSMOS_STATUS_TRANSITION",
        extra={
            "docId": doc_id,
            "previousStatus": old_status,
            "newStatus": new_status,
            "statusUpdatedAtUtc": doc["statusUpdatedAtUtc"],
            "step": "COSMOS_STATUS_TRANSITION",
        },
    )
    return updated
