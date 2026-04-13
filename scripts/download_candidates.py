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
        "id": "475f3f13-cf65-477a-b91c-4f50bb0c6a31",
        "docId": "475f3f13-cf65-477a-b91c-4f50bb0c6a31",
        "filename": "25-26_EPLI_Application_-_Travelers3_.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:07.000Z",
        "policyType": "test",
        "sha256": "04ae100a570e2efe5adc52ea33a5ed0bcf57647493fc07e256ea273f33355d26",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:32:50.000Z",
        "sourceBlobPath": "incoming/test/25-26_EPLI_Application_-_Travelers3_.pdf",
        "rawBlobPath": "raw/475f3f13-cf65-477a-b91c-4f50bb0c6a31/25-26_EPLI_Application_-_Travelers3_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1764034,
        "etag": "\"0x8DE99265BBF94E8\"",
        "_rid": "23IPAIehKso6AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKso6AAAAAAAAAA==/",
        "_etag": "\"1600c3f7-0000-1800-0000-69dc8e120000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 27,
            "timestamp": "2026-04-13T06:32:49.000Z",
            "candidatesPath": "candidates/475f3f13-cf65-477a-b91c-4f50bb0c6a31/candidates.json"
        },
        "_ts": 1776061970
    },
    {
        "id": "4ba75393-e433-4761-9fd7-946bea5cdaa7",
        "docId": "4ba75393-e433-4761-9fd7-946bea5cdaa7",
        "filename": "A-Majestic Care of Wellington Parc LLC25-26_EPL_CRIME_-_Chubb_Supp_App.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:17.000Z",
        "policyType": "test",
        "sha256": "f20f82307794645d596cb78f9c4e244981a5908ba33297a101074ea07a3dc909",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:33:08.000Z",
        "sourceBlobPath": "incoming/test/A-Majestic Care of Wellington Parc LLC25-26_EPL_CRIME_-_Chubb_Supp_App.pdf",
        "rawBlobPath": "raw/4ba75393-e433-4761-9fd7-946bea5cdaa7/A-Majestic Care of Wellington Parc LLC25-26_EPL_CRIME_-_Chubb_Supp_App.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 251259,
        "etag": "\"0x8DE992664DF0361\"",
        "_rid": "23IPAIehKso7AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKso7AAAAAAAAAA==/",
        "_etag": "\"1600d0f7-0000-1800-0000-69dc8e240000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 17,
            "timestamp": "2026-04-13T06:33:08.000Z",
            "candidatesPath": "candidates/4ba75393-e433-4761-9fd7-946bea5cdaa7/candidates.json"
        },
        "_ts": 1776061988
    },
    {
        "id": "36eda17e-923c-4570-ad9b-735921c7f642",
        "docId": "36eda17e-923c-4570-ad9b-735921c7f642",
        "filename": "4i_Chubb_Application_.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:18.000Z",
        "policyType": "test",
        "sha256": "a24a7d3159e27fd22e74801ed10ff82c8c7136f8b5dd362c661ffe37904d198a",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:33:13.000Z",
        "sourceBlobPath": "incoming/test/4i_Chubb_Application_.pdf",
        "rawBlobPath": "raw/36eda17e-923c-4570-ad9b-735921c7f642/4i_Chubb_Application_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 13981681,
        "etag": "\"0x8DE99266231E141\"",
        "_rid": "23IPAIehKso8AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKso8AAAAAAAAAA==/",
        "_etag": "\"1600d5f7-0000-1800-0000-69dc8e290000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 27,
            "timestamp": "2026-04-13T06:33:12.000Z",
            "candidatesPath": "candidates/36eda17e-923c-4570-ad9b-735921c7f642/candidates.json"
        },
        "_ts": 1776061993
    },
    {
        "id": "dbb690be-73e5-41df-9f06-55c52e5cf787",
        "docId": "dbb690be-73e5-41df-9f06-55c52e5cf787",
        "filename": "AA-Next.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:26.000Z",
        "policyType": "test",
        "sha256": "d9aa97d93ee37231f9736a8bc3259e302a75d217b5aeaaa7d43a06ff2d8a0f87",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:34:12.000Z",
        "sourceBlobPath": "incoming/test/AA-Next.pdf",
        "rawBlobPath": "raw/dbb690be-73e5-41df-9f06-55c52e5cf787/AA-Next.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 450887,
        "etag": "\"0x8DE992667D9283D\"",
        "_rid": "23IPAIehKso9AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKso9AAAAAAAAAA==/",
        "_etag": "\"160012f8-0000-1800-0000-69dc8e640000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 8,
            "timestamp": "2026-04-13T06:34:12.000Z",
            "candidatesPath": "candidates/dbb690be-73e5-41df-9f06-55c52e5cf787/candidates.json"
        },
        "_ts": 1776062052
    },
    {
        "id": "b598f77b-1614-4ddf-bcf6-8c6a3c9b1188",
        "docId": "b598f77b-1614-4ddf-bcf6-8c6a3c9b1188",
        "filename": "BB-SiVEC Biotechnologies.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:27.000Z",
        "policyType": "test",
        "sha256": "82b113bd16f62ede4cd638737b8ad9eeff12c92943885c835eefc2be80d8e0c1",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:33:35.000Z",
        "sourceBlobPath": "incoming/test/BB-SiVEC Biotechnologies.pdf",
        "rawBlobPath": "raw/b598f77b-1614-4ddf-bcf6-8c6a3c9b1188/BB-SiVEC Biotechnologies.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 694939,
        "etag": "\"0x8DE99266A6C9BC5\"",
        "_rid": "23IPAIehKso+AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKso+AAAAAAAAAA==/",
        "_etag": "\"1600e6f7-0000-1800-0000-69dc8e3f0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 21,
            "timestamp": "2026-04-13T06:33:35.000Z",
            "candidatesPath": "candidates/b598f77b-1614-4ddf-bcf6-8c6a3c9b1188/candidates.json"
        },
        "_ts": 1776062015
    },
    {
        "id": "3bd7f57b-1cd7-4f38-8f1d-617dedce189d",
        "docId": "3bd7f57b-1cd7-4f38-8f1d-617dedce189d",
        "filename": "Bill Cramer Chevrolet Cadillac Buick GMC, Inc. EPLI_App__Travelers__Bill_Cramer_Chevrolet_GMC__2026.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:27.000Z",
        "policyType": "test",
        "sha256": "6c3bf5658ef695c82dd0ac9199d0f118fa8b9d9f09212459f1afed8429886481",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:33:54.000Z",
        "sourceBlobPath": "incoming/test/Bill Cramer Chevrolet Cadillac Buick GMC, Inc. EPLI_App__Travelers__Bill_Cramer_Chevrolet_GMC__2026.pdf",
        "rawBlobPath": "raw/3bd7f57b-1cd7-4f38-8f1d-617dedce189d/Bill Cramer Chevrolet Cadillac Buick GMC, Inc. EPLI_App__Travelers__Bill_Cramer_Chevrolet_GMC__2026.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 937504,
        "etag": "\"0x8DE99266D4BE1CB\"",
        "_rid": "23IPAIehKso-AAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKso-AAAAAAAAAA==/",
        "_etag": "\"1600f8f7-0000-1800-0000-69dc8e520000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 19,
            "timestamp": "2026-04-13T06:33:54.000Z",
            "candidatesPath": "candidates/3bd7f57b-1cd7-4f38-8f1d-617dedce189d/candidates.json"
        },
        "_ts": 1776062034
    },
    {
        "id": "123b1c6d-4a27-4cd5-9ff5-d791da915d73",
        "docId": "123b1c6d-4a27-4cd5-9ff5-d791da915d73",
        "filename": "Chubb_App.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:37.000Z",
        "policyType": "test",
        "sha256": "a1b8628204a65f99b776b812f00755eb0d2c7186857a630d5918e6d3743d0db9",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:34:42.000Z",
        "sourceBlobPath": "incoming/test/Chubb_App.pdf",
        "rawBlobPath": "raw/123b1c6d-4a27-4cd5-9ff5-d791da915d73/Chubb_App.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 488266,
        "etag": "\"0x8DE99267030FDB0\"",
        "_rid": "23IPAIehKspAAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspAAAAAAAAAAA==/",
        "_etag": "\"160034f8-0000-1800-0000-69dc8e820000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 23,
            "timestamp": "2026-04-13T06:34:42.000Z",
            "candidatesPath": "candidates/123b1c6d-4a27-4cd5-9ff5-d791da915d73/candidates.json"
        },
        "_ts": 1776062082
    },
    {
        "id": "1f625123-52d9-498f-8952-33a343b91fe8",
        "docId": "1f625123-52d9-498f-8952-33a343b91fe8",
        "filename": "Farris Motor Company Travelers_App_for_EPLI-Crime_-D_&_O_and_Fiduciary.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:50.000Z",
        "policyType": "test",
        "sha256": "c8d6beb684694204a821fff5fbb3a1df3f44d277a6e134a0bda075e1f02cbd13",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:34:12.000Z",
        "sourceBlobPath": "incoming/test/Farris Motor Company Travelers_App_for_EPLI-Crime_-D_&_O_and_Fiduciary.pdf",
        "rawBlobPath": "raw/1f625123-52d9-498f-8952-33a343b91fe8/Farris Motor Company Travelers_App_for_EPLI-Crime_-D_&_O_and_Fiduciary.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1058974,
        "etag": "\"0x8DE992678060CC5\"",
        "_rid": "23IPAIehKspBAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspBAAAAAAAAAA==/",
        "_etag": "\"160013f8-0000-1800-0000-69dc8e640000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 12,
            "timestamp": "2026-04-13T06:34:12.000Z",
            "candidatesPath": "candidates/1f625123-52d9-498f-8952-33a343b91fe8/candidates.json"
        },
        "_ts": 1776062052
    },
    {
        "id": "aab82088-5bad-4273-a824-1fb61741847f",
        "docId": "aab82088-5bad-4273-a824-1fb61741847f",
        "filename": "D-Curry Management Corp.pdf",
        "uploadedAtUtc": "2026-04-13T06:32:51.000Z",
        "policyType": "test",
        "sha256": "3e9429dec6b0a7a4ca66c5031aeec61ef06f2895f764d0e7a76e9fda04a55343",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:35:37.000Z",
        "sourceBlobPath": "incoming/test/D-Curry Management Corp.pdf",
        "rawBlobPath": "raw/aab82088-5bad-4273-a824-1fb61741847f/D-Curry Management Corp.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 9448669,
        "etag": "\"0x8DE992674F5F4FE\"",
        "_rid": "23IPAIehKspCAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspCAAAAAAAAAA==/",
        "_etag": "\"160066f8-0000-1800-0000-69dc8eb90000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 20,
            "timestamp": "2026-04-13T06:35:36.000Z",
            "candidatesPath": "candidates/aab82088-5bad-4273-a824-1fb61741847f/candidates.json"
        },
        "_ts": 1776062137
    },
    {
        "id": "24373596-c636-414d-a355-8c2ab4d232db",
        "docId": "24373596-c636-414d-a355-8c2ab4d232db",
        "filename": "Industrial-Travelers_EPL-1.pdf",
        "uploadedAtUtc": "2026-04-13T06:33:04.000Z",
        "policyType": "test",
        "sha256": "efe4190c59b35c47587911ee3d96a57922d4f708d00cf4c32aaa96b57473a512",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:36:00.000Z",
        "sourceBlobPath": "incoming/test/Industrial-Travelers_EPL-1.pdf",
        "rawBlobPath": "raw/24373596-c636-414d-a355-8c2ab4d232db/Industrial-Travelers_EPL-1.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 2454520,
        "etag": "\"0x8DE99267B643335\"",
        "_rid": "23IPAIehKspDAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspDAAAAAAAAAA==/",
        "_etag": "\"16008cf8-0000-1800-0000-69dc8ed00000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 14,
            "timestamp": "2026-04-13T06:36:00.000Z",
            "candidatesPath": "candidates/24373596-c636-414d-a355-8c2ab4d232db/candidates.json"
        },
        "_ts": 1776062160
    },
    {
        "id": "297339bf-35ee-4a57-bb43-263a12dada3c",
        "docId": "297339bf-35ee-4a57-bb43-263a12dada3c",
        "filename": "Travelers_App.pdf",
        "uploadedAtUtc": "2026-04-13T06:33:09.000Z",
        "policyType": "test",
        "sha256": "dfc709ea97dcb838b1a5d8d15c89a83ff08725df0a4bd595ce2e85618e45a32b",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:35:42.000Z",
        "sourceBlobPath": "incoming/test/Travelers_App.pdf",
        "rawBlobPath": "raw/297339bf-35ee-4a57-bb43-263a12dada3c/Travelers_App.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 471507,
        "etag": "\"0x8DE99268384D71F\"",
        "_rid": "23IPAIehKspEAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspEAAAAAAAAAA==/",
        "_etag": "\"16007cf8-0000-1800-0000-69dc8ebf0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 19,
            "timestamp": "2026-04-13T06:35:42.000Z",
            "candidatesPath": "candidates/297339bf-35ee-4a57-bb43-263a12dada3c/candidates.json"
        },
        "_ts": 1776062143
    },
    {
        "id": "3342abc6-0493-418e-a715-9c4cf20b063c",
        "docId": "3342abc6-0493-418e-a715-9c4cf20b063c",
        "filename": "Ted's RV Land Inc Travelers_App_for_EPLI-Crime-_Teds_RV_Land_Inc_26-27.pdf",
        "uploadedAtUtc": "2026-04-13T06:33:09.000Z",
        "policyType": "test",
        "sha256": "be4dd2e45280aac3991b40cf93c1107aaf0272d70ce95959175a8332e50bdf12",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:36:06.000Z",
        "sourceBlobPath": "incoming/test/Ted's RV Land Inc Travelers_App_for_EPLI-Crime-_Teds_RV_Land_Inc_26-27.pdf",
        "rawBlobPath": "raw/3342abc6-0493-418e-a715-9c4cf20b063c/Ted's RV Land Inc Travelers_App_for_EPLI-Crime-_Teds_RV_Land_Inc_26-27.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1500982,
        "etag": "\"0x8DE992680968A10\"",
        "_rid": "23IPAIehKspFAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspFAAAAAAAAAA==/",
        "_etag": "\"160091f8-0000-1800-0000-69dc8ed60000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 11,
            "timestamp": "2026-04-13T06:36:05.000Z",
            "candidatesPath": "candidates/3342abc6-0493-418e-a715-9c4cf20b063c/candidates.json"
        },
        "_ts": 1776062166
    },
    {
        "id": "f27f42da-6e10-4d9d-8211-829a41549847",
        "docId": "f27f42da-6e10-4d9d-8211-829a41549847",
        "filename": "Travelers_EPLI_App.pdf",
        "uploadedAtUtc": "2026-04-13T06:33:27.000Z",
        "policyType": "test",
        "sha256": "ee6a8836e69b8fa5021804a26855f4f1a2dba6b3e7f23e81c94dac97482952b3",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:36:37.000Z",
        "sourceBlobPath": "incoming/test/Travelers_EPLI_App.pdf",
        "rawBlobPath": "raw/f27f42da-6e10-4d9d-8211-829a41549847/Travelers_EPLI_App.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 713768,
        "etag": "\"0x8DE99268925FADA\"",
        "_rid": "23IPAIehKspGAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspGAAAAAAAAAA==/",
        "_etag": "\"1600b2f8-0000-1800-0000-69dc8ef50000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 8,
            "timestamp": "2026-04-13T06:36:36.000Z",
            "candidatesPath": "candidates/f27f42da-6e10-4d9d-8211-829a41549847/candidates.json"
        },
        "_ts": 1776062197
    },
    {
        "id": "8e9bb2d1-d848-43a9-a7e1-64cabb8d0b17",
        "docId": "8e9bb2d1-d848-43a9-a7e1-64cabb8d0b17",
        "filename": "Travelers_Crime_app1_.pdf",
        "uploadedAtUtc": "2026-04-13T06:33:27.000Z",
        "policyType": "test",
        "sha256": "a4140e1ca64d50904c207cd83e72361b8b1c789cd561cc09160a78d1e4bbfa27",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:37:09.000Z",
        "sourceBlobPath": "incoming/test/Travelers_Crime_app1_.pdf",
        "rawBlobPath": "raw/8e9bb2d1-d848-43a9-a7e1-64cabb8d0b17/Travelers_Crime_app1_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 717966,
        "etag": "\"0x8DE9926862CC4DC\"",
        "_rid": "23IPAIehKspHAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspHAAAAAAAAAA==/",
        "_etag": "\"1600d0f8-0000-1800-0000-69dc8f150000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 12,
            "timestamp": "2026-04-13T06:37:08.000Z",
            "candidatesPath": "candidates/8e9bb2d1-d848-43a9-a7e1-64cabb8d0b17/candidates.json"
        },
        "_ts": 1776062229
    },
    {
        "id": "5b668ae6-3daf-4d3c-82ff-e3c085d41c62",
        "docId": "5b668ae6-3daf-4d3c-82ff-e3c085d41c62",
        "filename": "_Crime_Application.pdf",
        "uploadedAtUtc": "2026-04-13T06:33:45.000Z",
        "policyType": "test",
        "sha256": "0b2c08b9c12532f9ca0ebf89ac0c3011c904e54d65e2e05b6bbb6e8db1019707",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:36:40.000Z",
        "sourceBlobPath": "incoming/test/_Crime_Application.pdf",
        "rawBlobPath": "raw/5b668ae6-3daf-4d3c-82ff-e3c085d41c62/_Crime_Application.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 285811,
        "etag": "\"0x8DE992691DD1FEB\"",
        "_rid": "23IPAIehKspIAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspIAAAAAAAAAA==/",
        "_etag": "\"1600b7f8-0000-1800-0000-69dc8ef80000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 12,
            "timestamp": "2026-04-13T06:36:40.000Z",
            "candidatesPath": "candidates/5b668ae6-3daf-4d3c-82ff-e3c085d41c62/candidates.json"
        },
        "_ts": 1776062200
    },
    {
        "id": "249ffe6f-bd95-4de2-9da7-f6190bde8fd6",
        "docId": "249ffe6f-bd95-4de2-9da7-f6190bde8fd6",
        "filename": "Travelers_Private_Company_Multi-Coverage_Application.pdf",
        "uploadedAtUtc": "2026-04-13T06:33:45.000Z",
        "policyType": "test",
        "sha256": "392155c8600d80ee2dc0d343d88e899d87a701b5c24b0c7bb95a393e190a7d5a",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:36:17.000Z",
        "sourceBlobPath": "incoming/test/Travelers_Private_Company_Multi-Coverage_Application.pdf",
        "rawBlobPath": "raw/249ffe6f-bd95-4de2-9da7-f6190bde8fd6/Travelers_Private_Company_Multi-Coverage_Application.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 384921,
        "etag": "\"0x8DE99268BCC2DF6\"",
        "_rid": "23IPAIehKspJAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspJAAAAAAAAAA==/",
        "_etag": "\"16009ef8-0000-1800-0000-69dc8ee10000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 8,
            "timestamp": "2026-04-13T06:36:17.000Z",
            "candidatesPath": "candidates/249ffe6f-bd95-4de2-9da7-f6190bde8fd6/candidates.json"
        },
        "_ts": 1776062177
    },
    {
        "id": "b7e6b84f-6c88-481d-8fcf-73730388a3a3",
        "docId": "b7e6b84f-6c88-481d-8fcf-73730388a3a3",
        "filename": "Wooden Nickle Enterprises, Inc dba Wooden Nickel.pdf",
        "uploadedAtUtc": "2026-04-13T06:33:45.000Z",
        "policyType": "test",
        "sha256": "52ba0ad7225181ba6aa726c1692eacbef45c9f8cec16742aca4a387aa0fb1ca2",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:37:40.000Z",
        "sourceBlobPath": "incoming/test/Wooden Nickle Enterprises, Inc dba Wooden Nickel.pdf",
        "rawBlobPath": "raw/b7e6b84f-6c88-481d-8fcf-73730388a3a3/Wooden Nickle Enterprises, Inc dba Wooden Nickel.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1902275,
        "etag": "\"0x8DE99268F414C98\"",
        "_rid": "23IPAIehKspKAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspKAAAAAAAAAA==/",
        "_etag": "\"1600edf8-0000-1800-0000-69dc8f340000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 0,
            "timestamp": "2026-04-13T06:37:40.000Z",
            "candidatesPath": "candidates/b7e6b84f-6c88-481d-8fcf-73730388a3a3/candidates.json"
        },
        "_ts": 1776062260
    },
    {
        "id": "1dc915db-3899-4f95-8546-ec2d8c69ff3e",
        "docId": "1dc915db-3899-4f95-8546-ec2d8c69ff3e",
        "filename": "_EPL_-_App_Fillable5-142022_response_Aug_25_08-25-2025_06-20-51_.pdf",
        "uploadedAtUtc": "2026-04-13T06:34:05.000Z",
        "policyType": "test",
        "sha256": "237b436f92a69666807892ae578ff4e4929b5f026d24714ba2cff9b78548337b",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:37:40.000Z",
        "sourceBlobPath": "incoming/test/_EPL_-_App_Fillable5-142022_response_Aug_25_08-25-2025_06-20-51_.pdf",
        "rawBlobPath": "raw/1dc915db-3899-4f95-8546-ec2d8c69ff3e/_EPL_-_App_Fillable5-142022_response_Aug_25_08-25-2025_06-20-51_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 246431,
        "etag": "\"0x8DE992697CB1E52\"",
        "_rid": "23IPAIehKspLAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspLAAAAAAAAAA==/",
        "_etag": "\"1600ecf8-0000-1800-0000-69dc8f340000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 13,
            "timestamp": "2026-04-13T06:37:39.000Z",
            "candidatesPath": "candidates/1dc915db-3899-4f95-8546-ec2d8c69ff3e/candidates.json"
        },
        "_ts": 1776062260
    },
    {
        "id": "d4f5ddee-47cc-4180-b594-3983cf98f831",
        "docId": "d4f5ddee-47cc-4180-b594-3983cf98f831",
        "filename": "_E&OAPD_MED_Home_Health_and_General_Liability_Appplication144APP0724_.pdf",
        "uploadedAtUtc": "2026-04-13T06:34:05.000Z",
        "policyType": "test",
        "sha256": "df06d2c993f8164692db8915ded987a5a125731458321e8ac01bd527b8b0dd93",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:37:15.000Z",
        "sourceBlobPath": "incoming/test/_E&OAPD_MED_Home_Health_and_General_Liability_Appplication144APP0724_.pdf",
        "rawBlobPath": "raw/d4f5ddee-47cc-4180-b594-3983cf98f831/_E&OAPD_MED_Home_Health_and_General_Liability_Appplication144APP0724_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1263719,
        "etag": "\"0x8DE992695128DB5\"",
        "_rid": "23IPAIehKspMAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspMAAAAAAAAAA==/",
        "_etag": "\"1600d7f8-0000-1800-0000-69dc8f1b0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 1,
            "timestamp": "2026-04-13T06:37:15.000Z",
            "candidatesPath": "candidates/d4f5ddee-47cc-4180-b594-3983cf98f831/candidates.json"
        },
        "_ts": 1776062235
    },
    {
        "id": "9fc59e75-bcf8-43bf-beb1-7863be24cecb",
        "docId": "9fc59e75-bcf8-43bf-beb1-7863be24cecb",
        "filename": "_Entered_See_File_1071105Lillii_RNB_Inc-_New_Business_SubmissionChild-1-New_Business_Application_-_Private_Company_Protection_Plus36-106382_.pdf",
        "uploadedAtUtc": "2026-04-13T06:34:20.000Z",
        "policyType": "test",
        "sha256": "ac76df9750372eb11933d7f0c0286ddeb21f5cf1828fe963a5d6c8482284b999",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:38:58.000Z",
        "sourceBlobPath": "incoming/test/_Entered_See_File_1071105Lillii_RNB_Inc-_New_Business_SubmissionChild-1-New_Business_Application_-_Private_Company_Protection_Plus36-106382_.pdf",
        "rawBlobPath": "raw/9fc59e75-bcf8-43bf-beb1-7863be24cecb/_Entered_See_File_1071105Lillii_RNB_Inc-_New_Business_SubmissionChild-1-New_Business_Application_-_Private_Company_Protection_Plus36-106382_.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 1615366,
        "etag": "\"0x8DE99269AB1A118\"",
        "_rid": "23IPAIehKspNAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspNAAAAAAAAAA==/",
        "_etag": "\"160042f9-0000-1800-0000-69dc8f820000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 13,
            "timestamp": "2026-04-13T06:38:57.000Z",
            "candidatesPath": "candidates/9fc59e75-bcf8-43bf-beb1-7863be24cecb/candidates.json"
        },
        "_ts": 1776062338
    },
    {
        "id": "524d70b2-b32a-41b3-b611-632cf9849d20",
        "docId": "524d70b2-b32a-41b3-b611-632cf9849d20",
        "filename": "ndustrial Water Service, Inc-2.pdf",
        "uploadedAtUtc": "2026-04-13T06:34:43.000Z",
        "policyType": "test",
        "sha256": "592c56d5ff6265409f8ccaebf5f8137b102dca43e74b690e7571b2ea6fad38b6",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:38:04.000Z",
        "sourceBlobPath": "incoming/test/ndustrial Water Service, Inc-2.pdf",
        "rawBlobPath": "raw/524d70b2-b32a-41b3-b611-632cf9849d20/ndustrial Water Service, Inc-2.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 2315414,
        "etag": "\"0x8DE9926A21C749C\"",
        "_rid": "23IPAIehKspOAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspOAAAAAAAAAA==/",
        "_etag": "\"160004f9-0000-1800-0000-69dc8f4c0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 26,
            "timestamp": "2026-04-13T06:38:03.000Z",
            "candidatesPath": "candidates/524d70b2-b32a-41b3-b611-632cf9849d20/candidates.json"
        },
        "_ts": 1776062284
    },
    {
        "id": "c6364355-e66c-40c9-80fe-a00ecdd012bb",
        "docId": "c6364355-e66c-40c9-80fe-a00ecdd012bb",
        "filename": "cc-Friedman & Feiger, LLPFF_Chubb_EPLI_Application_11.21.25_print.pdf",
        "uploadedAtUtc": "2026-04-13T06:34:43.000Z",
        "policyType": "test",
        "sha256": "78a7144c6bc9e54b0cbae797fa4587ec9f241a3f9bd4de73eec187ef1a9933d5",
        "status": "CANDIDATES_GENERATED",
        "statusUpdatedAtUtc": "2026-04-13T06:37:14.000Z",
        "sourceBlobPath": "incoming/test/cc-Friedman & Feiger, LLPFF_Chubb_EPLI_Application_11.21.25_print.pdf",
        "rawBlobPath": "raw/c6364355-e66c-40c9-80fe-a00ecdd012bb/cc-Friedman & Feiger, LLPFF_Chubb_EPLI_Application_11.21.25_print.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 3947105,
        "etag": "\"0x8DE99269F413E28\"",
        "_rid": "23IPAIehKspPAAAAAAAAAA==",
        "_self": "dbs/23IPAA==/colls/23IPAIehKso=/docs/23IPAIehKspPAAAAAAAAAA==/",
        "_etag": "\"1600d6f8-0000-1800-0000-69dc8f1a0000\"",
        "_attachments": "attachments/",
        "stageDetails": {
            "stage": "candidates",
            "extractedFieldCount": 10,
            "timestamp": "2026-04-13T06:37:14.000Z",
            "candidatesPath": "candidates/c6364355-e66c-40c9-80fe-a00ecdd012bb/candidates.json"
        },
        "_ts": 1776062234
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

