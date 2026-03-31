#!/usr/bin/env python3
"""
Download `candidates.json` blobs for a list of documents.

Prereqs:
  - `pip install -r requirements.txt`
  - Set env var: `AzureWebJobsStorage` to your Azure Storage connection string

Usage:
  python scripts/download_candidates.py

Edit the `ITEMS` variable below to "pass the array variable every time".
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from azure.storage.blob import BlobServiceClient


# Your items array (only `id`/`docId`, `filename`, and optionally `stageDetails.candidatesPath` are used).
ITEMS = [
    {
        "id": "e94f3a07-c275-4db1-8e2d-7ba2cd73e6d0",
        "filename": "1._Chubb_D&O,_EPLI_App_SiVEC_Biotech_11.18.2025.pdf",
    },
    {
        "id": "b71f90dd-72f6-4200-bfa7-f7b05b295cc5",
        "filename": "25-26_EPL_CRIME_-_Chubb_Supp_App.pdf",
    },
    {
        "id": "857adc50-f242-4739-a7b5-58ee1cfa800b",
        "filename": "EPLI_-_Travelers_-_Wodden_Nickle_Enterprises_Inc.pdf",
    },
    {
        "id": "4bf4a7d4-7655-4371-908f-375e23a1411a",
        "filename": "EPLI_-_Chubb_Application_10-01-25.pdf",
    },
    {
        "id": "3c55ab11-ba3e-4bd7-ae19-a5219d84bf0b",
        "filename": "EPLI_App__Travelers__Bill_Cramer_Chevrolet_GMC__2026.pdf",
    },
    {
        "id": "883740a8-b0f7-449f-9279-c30c36e5a66c",
        "filename": "EPL_Application_Travelers-_Pacific_Water_Conditioning.pdf",
    },
    {
        "id": "01f9e3f9-c89a-4d88-a86c-c5cbf3596f4f",
        "filename": "FF_Chubb_EPLI_Application_11.21.25_print.pdf",
    },
    {
        "id": "a41f70da-79ba-4655-86d3-3df955378b48",
        "filename": "Travelers_App_for_EPLI-Crime-_Teds_RV_Land_Inc_26-27.pdf",
    },
    {
        "id": "0f50bc74-771e-469c-a23f-adad33f6fd7c",
        "filename": "Travelers_App_for_EPLI-Crime_-D_&_O_and_Fiduciary.pdf",
    },
    {
        "id": "f81a4dfd-8d9b-44f3-92c2-2d2f82c4abe7",
        "filename": "Travelers_EPL.pdf",
    },
    {
        "id": "6d3077f7-c829-40a8-b4ea-9571bd0d7492",
        "filename": "chubb_application_do_epl_etc_2025.pdf",
    },
]


def _sanitize_filename(name: str) -> str:
    # Keep it simple: replace characters that commonly break paths/shells.
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", str(name)).strip()


def _get_doc_id(item: dict) -> str:
    # In your payload both `id` and `docId` exist; we prefer `id` but fall back safely.
    doc_id = item.get("id") or item.get("docId")
    if not doc_id or not str(doc_id).strip():
        raise ValueError(f"Missing `id`/`docId` in item: {json.dumps(item)[:200]}")
    return str(doc_id).strip()


def _get_candidates_blob_path(item: dict) -> str:
    stage_details = item.get("stageDetails") or {}
    # If provided, use the exact path from Cosmos stageDetails.
    candidates_path = stage_details.get("candidatesPath")
    if candidates_path and str(candidates_path).strip():
        return str(candidates_path).strip()

    # Otherwise compute from the doc id (matches repo's blob_paths helper).
    doc_id = _get_doc_id(item)
    return f"candidates/{doc_id}/candidates.json"


def main() -> None:
    conn_str = os.environ.get("AzureWebJobsStorage") or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str or not conn_str.strip():
        # Local dev convenience: allow pulling connection string from local.settings.json.
        local_settings_path = Path("local.settings.json")
        if local_settings_path.exists():
            try:
                local_settings = json.loads(local_settings_path.read_text(encoding="utf-8"))
                conn_str = (
                    (local_settings.get("Values") or {}).get("AzureWebJobsStorage")
                    or (local_settings.get("Values") or {}).get("AZURE_STORAGE_CONNECTION_STRING")
                )
            except Exception:
                # We'll fail with the clearer error message below.
                conn_str = None

    if not conn_str or not conn_str.strip() or "<your-storage-connection-string>" in conn_str:
        raise RuntimeError(
            "Missing storage connection string. Set `AzureWebJobsStorage` (preferred) "
            "or `AZURE_STORAGE_CONNECTION_STRING` (or fill it in `local.settings.json`)."
        )

    out_dir = Path("downloads/candidates")
    out_dir.mkdir(parents=True, exist_ok=True)

    blob_service = BlobServiceClient.from_connection_string(conn_str)

    for i, item in enumerate(ITEMS, start=1):
        doc_id = _get_doc_id(item)
        filename = item.get("filename") or doc_id

        blob_path = _get_candidates_blob_path(item)
        if "/" not in blob_path:
            raise ValueError(f"Unexpected candidates blob path (missing '/'): {blob_path!r}")

        container_name, blob_name = blob_path.split("/", 1)
        out_path = out_dir / f"{doc_id}__{_sanitize_filename(filename)}.candidates.json"

        print(f"[{i}/{len(ITEMS)}] Downloading {blob_path} -> {out_path}")

        blob_client = blob_service.get_container_client(container_name).get_blob_client(blob_name)
        data = blob_client.download_blob().readall()
        out_path.write_bytes(data)

    print(f"Done. Downloaded {len(ITEMS)} candidates.json files to: {out_dir}")


if __name__ == "__main__":
    main()

