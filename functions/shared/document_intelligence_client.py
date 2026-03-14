"""Thin wrapper around Azure Document Intelligence (prebuilt-layout).

This module centralizes how we talk to Document Intelligence so that OCR
functions can call a single helper and stay decoupled from SDK details.

Configuration (app settings)
----------------------------

Required:
- DOCUMENT_INTELLIGENCE_ENDPOINT
    The endpoint of the Document Intelligence resource, e.g.
    https://<resource-name>.cognitiveservices.azure.com

Authentication (choose ONE of):
- DOCUMENT_INTELLIGENCE_API_KEY
    If set, the client uses API key authentication.
- Otherwise, DefaultAzureCredential is used against the endpoint.

Optional:
- DOCUMENT_INTELLIGENCE_MODEL_ID
    Model identifier to use. Defaults to "prebuilt-layout".
"""

from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass
from typing import Any, BinaryIO, Optional

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient as DocumentIntelligenceClientAio
from azure.ai.documentintelligence.models import DocumentAnalysisFeature
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential


@dataclass
class DocumentIntelligenceConfig:
    """Configuration for connecting to Azure Document Intelligence."""

    endpoint: str
    model_id: str = "prebuilt-layout"
    api_key: Optional[str] = None


class DocumentIntelligenceWrapper:
    """Reusable client wrapper for running Document Intelligence analysis."""

    def __init__(self, *, config: DocumentIntelligenceConfig):
        if not config.endpoint:
            raise ValueError("DocumentIntelligenceConfig.endpoint must be set")

        self._config = config

        if config.api_key:
            credential = AzureKeyCredential(config.api_key)
        else:
            credential = DefaultAzureCredential()

        # Synchronous client for non-async callers.
        self._client = DocumentIntelligenceClient(
            endpoint=config.endpoint,
            credential=credential,
        )

        # Lazily created async client for reuse across invocations.
        self._async_client: Optional[DocumentIntelligenceClientAio] = None

    @classmethod
    def from_env(cls) -> "DocumentIntelligenceWrapper":
        """Create a wrapper instance from environment / app settings."""
        import os

        endpoint = os.environ.get("DOCUMENT_INTELLIGENCE_ENDPOINT", "").strip()
        if not endpoint:
            raise RuntimeError(
                "DOCUMENT_INTELLIGENCE_ENDPOINT app setting is required for Document Intelligence."
            )

        api_key = os.environ.get("DOCUMENT_INTELLIGENCE_API_KEY")
        model_id = os.environ.get("DOCUMENT_INTELLIGENCE_MODEL_ID", "prebuilt-layout").strip() or "prebuilt-layout"

        cfg = DocumentIntelligenceConfig(endpoint=endpoint, api_key=api_key, model_id=model_id)
        return cls(config=cfg)

    def analyze_document_bytes(self, data: bytes) -> dict[str, Any]:
        """Run analysis on a document provided as bytes using the configured model.

        Returns a JSON-serializable dict suitable for storage in blob / Cosmos.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")

        stream = io.BytesIO(data)
        return self.analyze_document_stream(stream)

    def analyze_document_stream(self, stream: BinaryIO) -> dict[str, Any]:
        """Run analysis on a readable stream using the configured model.

        The caller is responsible for positioning the stream at the beginning.
        """
        if stream is None or not hasattr(stream, "read"):
            raise TypeError("stream must be a readable binary file-like object")

        poller = self._client.begin_analyze_document(
            model_id=self._config.model_id,
            body=stream,
            content_type="application/octet-stream",
            features=[DocumentAnalysisFeature.KEY_VALUE_PAIRS],
        )
        result = poller.result()
        return result.as_dict()

    @property
    def model_id(self) -> str:
        """Return the model id used for analysis."""
        return self._config.model_id

    async def analyze_document_stream_async(self, stream: BinaryIO) -> dict[str, Any]:
        """Run analysis on a readable stream using the async Document Intelligence client.

        The caller must position the stream at the beginning.
        """
        if stream is None or not hasattr(stream, "read"):
            raise TypeError("stream must be a readable binary file-like object")

        # Lazily create a shared async client so connections can be reused.
        if self._async_client is None:
            if self._config.api_key:
                credential = AzureKeyCredential(self._config.api_key)
            else:
                credential = DefaultAzureCredential()

            self._async_client = DocumentIntelligenceClientAio(
                endpoint=self._config.endpoint,
                credential=credential,
            )

        poller = await self._async_client.begin_analyze_document(
            model_id=self._config.model_id,
            body=stream,
            content_type="application/octet-stream",
            features=[DocumentAnalysisFeature.KEY_VALUE_PAIRS],
        )
        result = await poller.result()
        return result.as_dict()

    async def close_async(self) -> None:
        """Close the underlying async client, if it has been created."""
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None

    async def __aenter__(self) -> "DocumentIntelligenceWrapper":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close_async()

