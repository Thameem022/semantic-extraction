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
        "id": "ec6cd6b5-e846-42e5-afd5-c43bc27eafa7",
        "docId": "ec6cd6b5-e846-42e5-afd5-c43bc27eafa7",
        "filename": "1._Chubb_D&O,_EPLI_App_SiVEC_Biotech_11.18.2025.pdf",
        "uploadedAtUtc": "2026-04-28T02:54:07.000Z",
        "policyType": "test",
        "sha256": "82b113bd16f62ede4cd638737b8ad9eeff12c92943885c835eefc2be80d8e0c1",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T02:54:45.000Z",
        "sourceBlobPath": "incoming/test/1._Chubb_D&O,_EPLI_App_SiVEC_Biotech_11.18.2025.pdf",
        "rawBlobPath": "raw/ec6cd6b5-e846-42e5-afd5-c43bc27eafa7/1._Chubb_D&O,_EPLI_App_SiVEC_Biotech_11.18.2025.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 694939,
        "etag": "\"0x8DEA4D166570631\"",
        "_rid": "23IPAIehKsplAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsplAAAAAAAAAA==/",
        "_etag": "\"0000c141-0000-1800-0000-69f021750000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 23,
            "timestamp": "2026-04-28T02:54:45.000Z",
            "candidatesPath": "candidates/ec6cd6b5-e846-42e5-afd5-c43bc27eafa7/candidates.json"
        },
        "_ts": 1777344885
    },
    {
        "id": "75f9e797-918c-4ef1-a06c-4d06d5a6d95f",
        "docId": "75f9e797-918c-4ef1-a06c-4d06d5a6d95f",
        "filename": "24-25_Travelers_Mgmt_Renewal_App.pdf.pdf",
        "uploadedAtUtc": "2026-04-28T02:54:07.000Z",
        "policyType": "test",
        "sha256": "1e054e8544eddcd881b37582e73a89a0749218ce58cb531ed6d541756dd0c276",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T02:54:46.000Z",
        "sourceBlobPath": "incoming/test/24-25_Travelers_Mgmt_Renewal_App.pdf.pdf",
        "rawBlobPath": "raw/75f9e797-918c-4ef1-a06c-4d06d5a6d95f/24-25_Travelers_Mgmt_Renewal_App.pdf.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 832404,
        "etag": "\"0x8DEA4D168FF09B1\"",
        "_rid": "23IPAIehKspmAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspmAAAAAAAAAA==/",
        "_etag": "\"0000c341-0000-1800-0000-69f021760000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 35,
            "timestamp": "2026-04-28T02:54:46.000Z",
            "candidatesPath": "candidates/75f9e797-918c-4ef1-a06c-4d06d5a6d95f/candidates.json"
        },
        "_ts": 1777344886
    },
    {
        "id": "86edf91e-c73d-4091-9baf-123142047d7f",
        "docId": "86edf91e-c73d-4091-9baf-123142047d7f",
        "filename": "25-26_EPLI_Application_-_Travelers3_.pdf",
        "uploadedAtUtc": "2026-04-28T02:54:18.000Z",
        "policyType": "test",
        "sha256": "04ae100a570e2efe5adc52ea33a5ed0bcf57647493fc07e256ea273f33355d26",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T02:56:13.000Z",
        "sourceBlobPath": "incoming/test/25-26_EPLI_Application_-_Travelers3_.pdf",
        "rawBlobPath": "raw/86edf91e-c73d-4091-9baf-123142047d7f/25-26_EPLI_Application_-_Travelers3_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1764034,
        "etag": "\"0x8DEA4D16BBC7F09\"",
        "_rid": "23IPAIehKspnAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspnAAAAAAAAAA==/",
        "_etag": "\"00000b42-0000-1800-0000-69f021cd0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 28,
            "timestamp": "2026-04-28T02:56:12.000Z",
            "candidatesPath": "candidates/86edf91e-c73d-4091-9baf-123142047d7f/candidates.json"
        },
        "_ts": 1777344973
    },
    {
        "id": "9c5748bd-8a7f-4335-9862-e09ba28e8676",
        "docId": "9c5748bd-8a7f-4335-9862-e09ba28e8676",
        "filename": "25-26_EPL_CRIME_-_Chubb_Supp_App.pdf",
        "uploadedAtUtc": "2026-04-28T02:57:19.000Z",
        "policyType": "test",
        "sha256": "f20f82307794645d596cb78f9c4e244981a5908ba33297a101074ea07a3dc909",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T02:57:58.000Z",
        "sourceBlobPath": "incoming/test/25-26_EPL_CRIME_-_Chubb_Supp_App.pdf",
        "rawBlobPath": "raw/9c5748bd-8a7f-4335-9862-e09ba28e8676/25-26_EPL_CRIME_-_Chubb_Supp_App.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 251259,
        "etag": "\"0x8DEA4D1D99D84EB\"",
        "_rid": "23IPAIehKspoAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspoAAAAAAAAAA==/",
        "_etag": "\"0000d942-0000-1800-0000-69f022360000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 23,
            "timestamp": "2026-04-28T02:57:58.000Z",
            "candidatesPath": "candidates/9c5748bd-8a7f-4335-9862-e09ba28e8676/candidates.json"
        },
        "_ts": 1777345078
    },
    {
        "id": "027c63b7-026d-4acd-bfa5-ab8e5d051367",
        "docId": "027c63b7-026d-4acd-bfa5-ab8e5d051367",
        "filename": "Chubb_App.pdf",
        "uploadedAtUtc": "2026-04-28T02:57:30.000Z",
        "policyType": "test",
        "sha256": "a1b8628204a65f99b776b812f00755eb0d2c7186857a630d5918e6d3743d0db9",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T02:58:41.000Z",
        "sourceBlobPath": "incoming/test/Chubb_App.pdf",
        "rawBlobPath": "raw/027c63b7-026d-4acd-bfa5-ab8e5d051367/Chubb_App.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 488266,
        "etag": "\"0x8DEA4D1E1761CF4\"",
        "_rid": "23IPAIehKsppAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsppAAAAAAAAAA==/",
        "_etag": "\"00006543-0000-1800-0000-69f022610000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 38,
            "timestamp": "2026-04-28T02:58:40.000Z",
            "candidatesPath": "candidates/027c63b7-026d-4acd-bfa5-ab8e5d051367/candidates.json"
        },
        "_ts": 1777345121
    },
    {
        "id": "3e19b0ea-75df-4732-b05d-cf57ae73c0c8",
        "docId": "3e19b0ea-75df-4732-b05d-cf57ae73c0c8",
        "filename": "4i_Chubb_Application_.pdf",
        "uploadedAtUtc": "2026-04-28T02:57:32.000Z",
        "policyType": "test",
        "sha256": "a24a7d3159e27fd22e74801ed10ff82c8c7136f8b5dd362c661ffe37904d198a",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T02:59:44.000Z",
        "sourceBlobPath": "incoming/test/4i_Chubb_Application_.pdf",
        "rawBlobPath": "raw/3e19b0ea-75df-4732-b05d-cf57ae73c0c8/4i_Chubb_Application_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 13981681,
        "etag": "\"0x8DEA4D1DEAE4E0E\"",
        "_rid": "23IPAIehKspqAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspqAAAAAAAAAA==/",
        "_etag": "\"00003e44-0000-1800-0000-69f022a00000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 31,
            "timestamp": "2026-04-28T02:59:43.000Z",
            "candidatesPath": "candidates/3e19b0ea-75df-4732-b05d-cf57ae73c0c8/candidates.json"
        },
        "_ts": 1777345184
    },
    {
        "id": "e4ca183b-a976-43fe-a046-d580248246d2",
        "docId": "e4ca183b-a976-43fe-a046-d580248246d2",
        "filename": "Chubb_EPL_Application_25-26.pdf",
        "uploadedAtUtc": "2026-04-28T03:00:41.000Z",
        "policyType": "test",
        "sha256": "f45a453f98a60b639608382733e452214992d4761e504fa8c5d636bccb6daf00",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:01:20.000Z",
        "sourceBlobPath": "incoming/test/Chubb_EPL_Application_25-26.pdf",
        "rawBlobPath": "raw/e4ca183b-a976-43fe-a046-d580248246d2/Chubb_EPL_Application_25-26.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 904106,
        "etag": "\"0x8DEA4D24FAD8221\"",
        "_rid": "23IPAIehKsprAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsprAAAAAAAAAA==/",
        "_etag": "\"00000f45-0000-1800-0000-69f023000000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 27,
            "timestamp": "2026-04-28T03:01:19.000Z",
            "candidatesPath": "candidates/e4ca183b-a976-43fe-a046-d580248246d2/candidates.json"
        },
        "_ts": 1777345280
    },
    {
        "id": "96d2abb1-fa47-4929-8ef4-36c1f4d43320",
        "docId": "96d2abb1-fa47-4929-8ef4-36c1f4d43320",
        "filename": "EPLI_-_Chubb_Application_10-01-25.pdf",
        "uploadedAtUtc": "2026-04-28T03:00:42.000Z",
        "policyType": "test",
        "sha256": "3e9429dec6b0a7a4ca66c5031aeec61ef06f2895f764d0e7a76e9fda04a55343",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:01:21.000Z",
        "sourceBlobPath": "incoming/test/EPLI_-_Chubb_Application_10-01-25.pdf",
        "rawBlobPath": "raw/96d2abb1-fa47-4929-8ef4-36c1f4d43320/EPLI_-_Chubb_Application_10-01-25.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 9448669,
        "etag": "\"0x8DEA4D254F02E13\"",
        "_rid": "23IPAIehKspsAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspsAAAAAAAAAA==/",
        "_etag": "\"00001145-0000-1800-0000-69f023010000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 22,
            "timestamp": "2026-04-28T03:01:21.000Z",
            "candidatesPath": "candidates/96d2abb1-fa47-4929-8ef4-36c1f4d43320/candidates.json"
        },
        "_ts": 1777345281
    },
    {
        "id": "75b0b54c-3bcb-4213-90fb-7b4bafd2e8de",
        "docId": "75b0b54c-3bcb-4213-90fb-7b4bafd2e8de",
        "filename": "EPLI_-_Travelers_-_Wodden_Nickle_Enterprises_Inc.pdf",
        "uploadedAtUtc": "2026-04-28T03:00:51.000Z",
        "policyType": "test",
        "sha256": "52ba0ad7225181ba6aa726c1692eacbef45c9f8cec16742aca4a387aa0fb1ca2",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:01:50.000Z",
        "sourceBlobPath": "incoming/test/EPLI_-_Travelers_-_Wodden_Nickle_Enterprises_Inc.pdf",
        "rawBlobPath": "raw/75b0b54c-3bcb-4213-90fb-7b4bafd2e8de/EPLI_-_Travelers_-_Wodden_Nickle_Enterprises_Inc.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1902275,
        "etag": "\"0x8DEA4D25792B92C\"",
        "_rid": "23IPAIehKsptAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsptAAAAAAAAAA==/",
        "_etag": "\"00005445-0000-1800-0000-69f0231e0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 18,
            "timestamp": "2026-04-28T03:01:49.000Z",
            "candidatesPath": "candidates/75b0b54c-3bcb-4213-90fb-7b4bafd2e8de/candidates.json"
        },
        "_ts": 1777345310
    },
    {
        "id": "f4e112ba-242b-47f1-a6ec-d864e1033728",
        "docId": "f4e112ba-242b-47f1-a6ec-d864e1033728",
        "filename": "EPLI_App__Travelers__Bill_Cramer_Chevrolet_GMC__2026.pdf",
        "uploadedAtUtc": "2026-04-28T03:03:52.000Z",
        "policyType": "test",
        "sha256": "6c3bf5658ef695c82dd0ac9199d0f118fa8b9d9f09212459f1afed8429886481",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:04:35.000Z",
        "sourceBlobPath": "incoming/test/EPLI_App__Travelers__Bill_Cramer_Chevrolet_GMC__2026.pdf",
        "rawBlobPath": "raw/f4e112ba-242b-47f1-a6ec-d864e1033728/EPLI_App__Travelers__Bill_Cramer_Chevrolet_GMC__2026.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 937504,
        "etag": "\"0x8DEA4D2C5847CFF\"",
        "_rid": "23IPAIehKspuAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspuAAAAAAAAAA==/",
        "_etag": "\"00001546-0000-1800-0000-69f023c40000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 43,
            "timestamp": "2026-04-28T03:04:35.000Z",
            "candidatesPath": "candidates/f4e112ba-242b-47f1-a6ec-d864e1033728/candidates.json"
        },
        "_ts": 1777345476
    },
    {
        "id": "23f020b3-f1e2-4883-8531-3bdef9237b51",
        "docId": "23f020b3-f1e2-4883-8531-3bdef9237b51",
        "filename": "EPL_Application_Travelers-_Pacific_Water_Conditioning.pdf",
        "uploadedAtUtc": "2026-04-28T03:04:03.000Z",
        "policyType": "test",
        "sha256": "592c56d5ff6265409f8ccaebf5f8137b102dca43e74b690e7571b2ea6fad38b6",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:05:38.000Z",
        "sourceBlobPath": "incoming/test/EPL_Application_Travelers-_Pacific_Water_Conditioning.pdf",
        "rawBlobPath": "raw/23f020b3-f1e2-4883-8531-3bdef9237b51/EPL_Application_Travelers-_Pacific_Water_Conditioning.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 2315414,
        "etag": "\"0x8DEA4D2C8242F04\"",
        "_rid": "23IPAIehKspvAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspvAAAAAAAAAA==/",
        "_etag": "\"00003e46-0000-1800-0000-69f024020000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 27,
            "timestamp": "2026-04-28T03:05:37.000Z",
            "candidatesPath": "candidates/23f020b3-f1e2-4883-8531-3bdef9237b51/candidates.json"
        },
        "_ts": 1777345538
    },
    {
        "id": "6c8d823c-beca-4298-8651-46ebe2c3b99d",
        "docId": "6c8d823c-beca-4298-8651-46ebe2c3b99d",
        "filename": "FF_Chubb_EPLI_Application_11.21.25_print.pdf",
        "uploadedAtUtc": "2026-04-28T03:04:03.000Z",
        "policyType": "test",
        "sha256": "78a7144c6bc9e54b0cbae797fa4587ec9f241a3f9bd4de73eec187ef1a9933d5",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:04:41.000Z",
        "sourceBlobPath": "incoming/test/FF_Chubb_EPLI_Application_11.21.25_print.pdf",
        "rawBlobPath": "raw/6c8d823c-beca-4298-8651-46ebe2c3b99d/FF_Chubb_EPLI_Application_11.21.25_print.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 3947105,
        "etag": "\"0x8DEA4D2CADA4931\"",
        "_rid": "23IPAIehKspwAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspwAAAAAAAAAA==/",
        "_etag": "\"00001746-0000-1800-0000-69f023c90000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 37,
            "timestamp": "2026-04-28T03:04:41.000Z",
            "candidatesPath": "candidates/6c8d823c-beca-4298-8651-46ebe2c3b99d/candidates.json"
        },
        "_ts": 1777345481
    },
    {
        "id": "f6ec1092-458f-4db3-886e-fee1ff468533",
        "docId": "f6ec1092-458f-4db3-886e-fee1ff468533",
        "filename": "Travelers_App.pdf",
        "uploadedAtUtc": "2026-04-28T03:07:04.000Z",
        "policyType": "test",
        "sha256": "dfc709ea97dcb838b1a5d8d15c89a83ff08725df0a4bd595ce2e85618e45a32b",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:07:50.000Z",
        "sourceBlobPath": "incoming/test/Travelers_App.pdf",
        "rawBlobPath": "raw/f6ec1092-458f-4db3-886e-fee1ff468533/Travelers_App.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 471507,
        "etag": "\"0x8DEA4D338C75B1E\"",
        "_rid": "23IPAIehKspxAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspxAAAAAAAAAA==/",
        "_etag": "\"0000c247-0000-1800-0000-69f024860000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 19,
            "timestamp": "2026-04-28T03:07:50.000Z",
            "candidatesPath": "candidates/f6ec1092-458f-4db3-886e-fee1ff468533/candidates.json"
        },
        "_ts": 1777345670
    },
    {
        "id": "18f299af-138d-4235-8359-af8f3432b467",
        "docId": "18f299af-138d-4235-8359-af8f3432b467",
        "filename": "Travelers_App_for_EPLI-Crime-_Teds_RV_Land_Inc_26-27.pdf",
        "uploadedAtUtc": "2026-04-28T03:07:15.000Z",
        "policyType": "test",
        "sha256": "be4dd2e45280aac3991b40cf93c1107aaf0272d70ce95959175a8332e50bdf12",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:07:59.000Z",
        "sourceBlobPath": "incoming/test/Travelers_App_for_EPLI-Crime-_Teds_RV_Land_Inc_26-27.pdf",
        "rawBlobPath": "raw/18f299af-138d-4235-8359-af8f3432b467/Travelers_App_for_EPLI-Crime-_Teds_RV_Land_Inc_26-27.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1500982,
        "etag": "\"0x8DEA4D33BC32C69\"",
        "_rid": "23IPAIehKspyAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspyAAAAAAAAAA==/",
        "_etag": "\"0000ef47-0000-1800-0000-69f0248f0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 30,
            "timestamp": "2026-04-28T03:07:59.000Z",
            "candidatesPath": "candidates/18f299af-138d-4235-8359-af8f3432b467/candidates.json"
        },
        "_ts": 1777345679
    },
    {
        "id": "89a14dda-6e32-4382-822f-115c36058f04",
        "docId": "89a14dda-6e32-4382-822f-115c36058f04",
        "filename": "Travelers_App_for_EPLI-Crime_-D_&_O_and_Fiduciary.pdf",
        "uploadedAtUtc": "2026-04-28T03:07:16.000Z",
        "policyType": "test",
        "sha256": "c8d6beb684694204a821fff5fbb3a1df3f44d277a6e134a0bda075e1f02cbd13",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:08:04.000Z",
        "sourceBlobPath": "incoming/test/Travelers_App_for_EPLI-Crime_-D_&_O_and_Fiduciary.pdf",
        "rawBlobPath": "raw/89a14dda-6e32-4382-822f-115c36058f04/Travelers_App_for_EPLI-Crime_-D_&_O_and_Fiduciary.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1058974,
        "etag": "\"0x8DEA4D33E57B99D\"",
        "_rid": "23IPAIehKspzAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspzAAAAAAAAAA==/",
        "_etag": "\"00000e48-0000-1800-0000-69f024940000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 26,
            "timestamp": "2026-04-28T03:08:04.000Z",
            "candidatesPath": "candidates/89a14dda-6e32-4382-822f-115c36058f04/candidates.json"
        },
        "_ts": 1777345684
    },
    {
        "id": "38dff0cf-041a-4abe-9fa4-394a08cacfef",
        "docId": "38dff0cf-041a-4abe-9fa4-394a08cacfef",
        "filename": "Travelers_Private_Company_Multi-Coverage_Application.pdf",
        "uploadedAtUtc": "2026-04-28T03:10:28.000Z",
        "policyType": "test",
        "sha256": "392155c8600d80ee2dc0d343d88e899d87a701b5c24b0c7bb95a393e190a7d5a",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:11:09.000Z",
        "sourceBlobPath": "incoming/test/Travelers_Private_Company_Multi-Coverage_Application.pdf",
        "rawBlobPath": "raw/38dff0cf-041a-4abe-9fa4-394a08cacfef/Travelers_Private_Company_Multi-Coverage_Application.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 384921,
        "etag": "\"0x8DEA4D3B1BBEE6B\"",
        "_rid": "23IPAIehKsp0AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsp0AAAAAAAAAA==/",
        "_etag": "\"00001749-0000-1800-0000-69f0254d0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 32,
            "timestamp": "2026-04-28T03:11:09.000Z",
            "candidatesPath": "candidates/38dff0cf-041a-4abe-9fa4-394a08cacfef/candidates.json"
        },
        "_ts": 1777345869
    },
    {
        "id": "3d4ec247-738d-4627-8c6a-61ffd6de1d6e",
        "docId": "3d4ec247-738d-4627-8c6a-61ffd6de1d6e",
        "filename": "Travelers_EPL.pdf",
        "uploadedAtUtc": "2026-04-28T03:10:28.000Z",
        "policyType": "test",
        "sha256": "efe4190c59b35c47587911ee3d96a57922d4f708d00cf4c32aaa96b57473a512",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:12:12.000Z",
        "sourceBlobPath": "incoming/test/Travelers_EPL.pdf",
        "rawBlobPath": "raw/3d4ec247-738d-4627-8c6a-61ffd6de1d6e/Travelers_EPL.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 2454520,
        "etag": "\"0x8DEA4D3ACEEDD53\"",
        "_rid": "23IPAIehKsp1AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsp1AAAAAAAAAA==/",
        "_etag": "\"00009249-0000-1800-0000-69f0258c0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 24,
            "timestamp": "2026-04-28T03:12:11.000Z",
            "candidatesPath": "candidates/3d4ec247-738d-4627-8c6a-61ffd6de1d6e/candidates.json"
        },
        "_ts": 1777345932
    },
    {
        "id": "9bdc2100-c799-45ce-ad17-7d05846aa799",
        "docId": "9bdc2100-c799-45ce-ad17-7d05846aa799",
        "filename": "Travelers_EPLI_App.pdf",
        "uploadedAtUtc": "2026-04-28T03:10:28.000Z",
        "policyType": "test",
        "sha256": "ee6a8836e69b8fa5021804a26855f4f1a2dba6b3e7f23e81c94dac97482952b3",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:11:09.000Z",
        "sourceBlobPath": "incoming/test/Travelers_EPLI_App.pdf",
        "rawBlobPath": "raw/9bdc2100-c799-45ce-ad17-7d05846aa799/Travelers_EPLI_App.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 713768,
        "etag": "\"0x8DEA4D3AF4D5B7B\"",
        "_rid": "23IPAIehKsp2AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsp2AAAAAAAAAA==/",
        "_etag": "\"00001649-0000-1800-0000-69f0254d0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 36,
            "timestamp": "2026-04-28T03:11:09.000Z",
            "candidatesPath": "candidates/9bdc2100-c799-45ce-ad17-7d05846aa799/candidates.json"
        },
        "_ts": 1777345869
    },
    {
        "id": "3c2ad5aa-014f-4fbb-866e-40b7a2f639c8",
        "docId": "3c2ad5aa-014f-4fbb-866e-40b7a2f639c8",
        "filename": "_EPL_-_App_Fillable5-142022_response_Aug_25_08-25-2025_06-20-51_.pdf",
        "uploadedAtUtc": "2026-04-28T03:13:39.000Z",
        "policyType": "test",
        "sha256": "237b436f92a69666807892ae578ff4e4929b5f026d24714ba2cff9b78548337b",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:14:30.000Z",
        "sourceBlobPath": "incoming/test/_EPL_-_App_Fillable5-142022_response_Aug_25_08-25-2025_06-20-51_.pdf",
        "rawBlobPath": "raw/3c2ad5aa-014f-4fbb-866e-40b7a2f639c8/_EPL_-_App_Fillable5-142022_response_Aug_25_08-25-2025_06-20-51_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 246431,
        "etag": "\"0x8DEA4D41F92D7AE\"",
        "_rid": "23IPAIehKsp3AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsp3AAAAAAAAAA==/",
        "_etag": "\"0000bb4a-0000-1800-0000-69f026160000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 14,
            "timestamp": "2026-04-28T03:14:29.000Z",
            "candidatesPath": "candidates/3c2ad5aa-014f-4fbb-866e-40b7a2f639c8/candidates.json"
        },
        "_ts": 1777346070
    },
    {
        "id": "92d8bfda-38db-4285-88b9-20d397cd61f0",
        "docId": "92d8bfda-38db-4285-88b9-20d397cd61f0",
        "filename": "chubb_application_do_epl_etc_2025.pdf",
        "uploadedAtUtc": "2026-04-28T03:13:39.000Z",
        "policyType": "test",
        "sha256": "d9aa97d93ee37231f9736a8bc3259e302a75d217b5aeaaa7d43a06ff2d8a0f87",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-28T03:14:17.000Z",
        "sourceBlobPath": "incoming/test/chubb_application_do_epl_etc_2025.pdf",
        "rawBlobPath": "raw/92d8bfda-38db-4285-88b9-20d397cd61f0/chubb_application_do_epl_etc_2025.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 450887,
        "etag": "\"0x8DEA4D42250B3D5\"",
        "_rid": "23IPAIehKsp4AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKsp4AAAAAAAAAA==/",
        "_etag": "\"0000884a-0000-1800-0000-69f0260a0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 30,
            "timestamp": "2026-04-28T03:14:17.000Z",
            "candidatesPath": "candidates/92d8bfda-38db-4285-88b9-20d397cd61f0/candidates.json"
        },
        "_ts": 1777346058
    }
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

