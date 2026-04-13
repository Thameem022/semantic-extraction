"""Candidate builder for semantic extraction from normalized layout JSON.

Makes 3 sequential LLM calls to extract all fields of the
StructuredIngestionPackage schema from different slices of the layout data.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from shared.models.ingestion_schema import (
    CoverageDetails,
    EmployeeCategory,
    EPLISpecificQuestions,
    GeneralInformation,
    RiskAssessment,
    StructuredIngestionPackage,
)
from shared.table_utils import (
    flatten_tables_to_markdown,
    serialize_kv_pairs_for_llm,
    serialize_pages_for_llm,
)

logger = logging.getLogger(__name__)

_SHARED_DIR = Path(__file__).resolve().parent
_PROMPT_DIR = _SHARED_DIR / "prompts"

_GENERAL_COVERAGE_PROMPT = _PROMPT_DIR / "general_and_coverage_extraction.txt"
_EMPLOYEE_RISK_PROMPT = _PROMPT_DIR / "employee_and_risk_extraction.txt"
_EPLI_PROMPT = _PROMPT_DIR / "epli_specific_extraction.txt"


def _create_async_http_client() -> httpx.AsyncClient:
    """Dedicated httpx transport for one Azure OpenAI invocation.

    Explicit limits and timeouts avoid leaving idle keep-alive connections that
    confuse SSL teardown when the Functions host recycles the worker.
    """
    request_s = float(os.environ.get("AZURE_OPENAI_HTTP_TIMEOUT_S", "60").strip() or "60")
    connect_s = float(os.environ.get("AZURE_OPENAI_HTTP_CONNECT_S", "10").strip() or "10")
    return httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=10,
            max_keepalive_connections=0,
        ),
        timeout=httpx.Timeout(request_s, connect=connect_s),
        http2=False,
    )


def _create_azure_openai_client() -> AsyncAzureOpenAI:
    """Build a new Async Azure OpenAI client for one invocation with explicit httpx.

    Do not cache the client at module scope: a long-lived singleton leaves httpx
    connections open and triggers ``Unclosed client session`` / SSL shutdown warnings
    when the Functions host freezes or recycles the worker before cleanup finishes.

    The OpenAI SDK closes the provided ``http_client`` when ``AsyncAzureOpenAI.close()`` runs.
    """
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview").strip()
    http_client = _create_async_http_client()
    return AsyncAzureOpenAI(
        api_version=api_version or "2024-08-01-preview",
        azure_endpoint=endpoint,
        api_key=api_key,
        http_client=http_client,
        timeout=float(os.environ.get("AZURE_OPENAI_HTTP_TIMEOUT_S", "60").strip() or "60"),
    )


def _check_azure_openai_env() -> str | None:
    """Return the deployment name if Azure OpenAI is fully configured, else None."""
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "").strip()
    if not endpoint or not api_key or not deployment:
        return None
    return deployment


class CandidateBuilder:
    """Builds a StructuredIngestionPackage from normalized layout outputs via 3 LLM calls."""

    def __init__(self, layout: dict[str, Any]) -> None:
        self.layout = layout or {}
        self._kv_markdown: str | None = None
        self._tables_markdown: str | None = None
        self._pages_markdown: str | None = None

    def _get_kv_markdown(self) -> str:
        if self._kv_markdown is None:
            self._kv_markdown = serialize_kv_pairs_for_llm(self.layout)
        return self._kv_markdown

    def _get_tables_markdown(self) -> str:
        if self._tables_markdown is None:
            self._tables_markdown = flatten_tables_to_markdown(self.layout, max_pages=30)
        return self._tables_markdown

    def _get_pages_markdown(self) -> str:
        if self._pages_markdown is None:
            self._pages_markdown = serialize_pages_for_llm(self.layout, max_pages=30)
        return self._pages_markdown

    def _compose_markdown(self, sources: list[str]) -> str:
        """Build the ``{{MARKDOWN}}`` payload from the requested data source keys.

        Supported keys: ``"kv"``, ``"tables"``, ``"pages"``.
        """
        sections: list[str] = []
        for source in sources:
            if source == "kv":
                text = self._get_kv_markdown()
                if text:
                    sections.append("## Key-Value Pairs\n" + text)
            elif source == "tables":
                text = self._get_tables_markdown()
                if text:
                    sections.append("## Document Tables\n" + text)
            elif source == "pages":
                text = self._get_pages_markdown()
                if text:
                    sections.append("## Page Text\n" + text)
        return "\n\n".join(sections)

    async def _call_llm(
        self,
        prompt_path: Path,
        data_sources: list[str],
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Generic LLM call: load prompt, substitute ``{{MARKDOWN}}``, parse response."""
        deployment = _check_azure_openai_env()
        if not deployment:
            raise EnvironmentError("Azure OpenAI environment not fully configured")

        system_prompt = prompt_path.read_text(encoding="utf-8")
        markdown_payload = self._compose_markdown(data_sources)
        user_content = system_prompt.replace("{{MARKDOWN}}", markdown_payload)

        client = _create_azure_openai_client()
        try:
            completion = await client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": user_content}],
                response_format={"type": "json_object"},
            )
            raw_text = completion.choices[0].message.content
            if not raw_text:
                raise ValueError("LLM returned empty response")
            data = json.loads(raw_text)
            return response_model.model_validate(data)
        finally:
            await client.close()

    async def _extract_general_and_coverage(
        self,
    ) -> tuple[GeneralInformation, CoverageDetails]:
        """Call 1: GeneralInformation + CoverageDetails from KV pairs and tables."""

        class _Response(BaseModel):
            GeneralInformation: GeneralInformation
            CoverageDetails: CoverageDetails

        result = await self._call_llm(
            _GENERAL_COVERAGE_PROMPT,
            data_sources=["kv", "tables"],
            response_model=_Response,
        )
        parsed = _Response.model_validate(result)
        return parsed.GeneralInformation, parsed.CoverageDetails

    async def _extract_employee_and_risk(
        self,
    ) -> tuple[EmployeeCategory, RiskAssessment]:
        """Call 2: EmployeeCategory + RiskAssessment from tables, KV, and pages."""

        class _Response(BaseModel):
            EmployeeCategory: EmployeeCategory
            RiskAssessment: RiskAssessment

        result = await self._call_llm(
            _EMPLOYEE_RISK_PROMPT,
            data_sources=["tables", "kv", "pages"],
            response_model=_Response,
        )
        parsed = _Response.model_validate(result)
        return parsed.EmployeeCategory, parsed.RiskAssessment

    async def _extract_epli_specific(self) -> EPLISpecificQuestions:
        """Call 3: EPLISpecificQuestions from KV, tables, and pages."""

        class _Response(BaseModel):
            EPLISpecificQuestions: EPLISpecificQuestions

        result = await self._call_llm(
            _EPLI_PROMPT,
            data_sources=["kv", "tables", "pages"],
            response_model=_Response,
        )
        parsed = _Response.model_validate(result)
        return parsed.EPLISpecificQuestions

    async def build(self) -> StructuredIngestionPackage:
        """Run 3 sequential LLM calls and assemble the StructuredIngestionPackage."""
        deployment = _check_azure_openai_env()
        if not deployment:
            logger.warning(
                "Azure OpenAI environment not fully configured; returning empty package",
            )
            return StructuredIngestionPackage(
                GeneralInformation=GeneralInformation(),
                CoverageDetails=CoverageDetails(),
                RiskAssessment=RiskAssessment(),
                EmployeeCategory=EmployeeCategory(),
                EPLISpecificQuestions=EPLISpecificQuestions(),
            )

        general_info = GeneralInformation()
        coverage = CoverageDetails()
        employee = EmployeeCategory()
        risk = RiskAssessment()
        epli = EPLISpecificQuestions()

        try:
            general_info, coverage = await self._extract_general_and_coverage()
        except Exception:
            logger.exception("LLM call 1 (general + coverage) failed")

        try:
            employee, risk = await self._extract_employee_and_risk()
        except Exception:
            logger.exception("LLM call 2 (employee + risk) failed")

        try:
            epli = await self._extract_epli_specific()
        except Exception:
            logger.exception("LLM call 3 (EPLI specific) failed")

        return StructuredIngestionPackage(
            GeneralInformation=general_info,
            CoverageDetails=coverage,
            RiskAssessment=risk,
            EmployeeCategory=employee,
            EPLISpecificQuestions=epli,
        )
