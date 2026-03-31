"""Candidate builder for semantic extraction from normalized layout JSON."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from openai import AsyncAzureOpenAI

from shared.field_registry import (
    APPLICANT_KV_ALLOWED_PAGES,
    APPLICANT_KV_FIELD_IDS,
    CANONICAL_FIELD_REGISTRY,
    COMBINED_INSURED_ADDRESS_LABEL_NORMS,
    CURRENCY_PATTERN,
    DATE_PATTERN,
    normalize_kv_key_label,
    normalize_value,
)
from shared.models.candidate import Candidate
from shared.models.cognitive_schema import CognitiveExtraction
from shared.table_utils import serialize_tables_for_llm

logger = logging.getLogger(__name__)

_SHARED_DIR = Path(__file__).resolve().parent
_COGNITIVE_PROMPT_PATH = _SHARED_DIR / "prompts" / "cognitive_extraction.txt"
_OPENAI_CLIENT: AsyncAzureOpenAI | None = None

# LLM-only canonical fields (must match CognitiveExtraction); KV fills first, then LLM for gaps.
COGNITIVE_FIELD_IDS: tuple[str, ...] = (
    "emp_full_time",
    "emp_part_time",
    "emp_independent_contractors",
    "emp_temporary_leased",
    "emp_full_time_ca",
    "emp_part_time_ca",
    "total_assets",
    "net_income",
    "revenue",
    "profit",
)

_LLM_PROTECTED_FIELD_IDS: frozenset[str] = frozenset(
    {"applicant_name", "insured_address", "website", "email_address"}
)


def get_openai_client() -> AsyncAzureOpenAI:
    """Get a lazily initialized module-level Async Azure OpenAI client."""
    global _OPENAI_CLIENT
    if _OPENAI_CLIENT is None:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
        api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview").strip()
        _OPENAI_CLIENT = AsyncAzureOpenAI(
            api_version=api_version or "2024-08-01-preview",
            azure_endpoint=endpoint,
            api_key=api_key,
            timeout=60.0,
        )
    return _OPENAI_CLIENT


class CandidateBuilder:
    """Builds field candidates from normalized layout outputs."""

    def __init__(self, layout: dict[str, Any]) -> None:
        self.layout = layout or {}
        self._applicant_alias_index = self._build_applicant_alias_index()
        self._lines = self._build_line_index()

    def kv_hunter(self) -> list[Candidate]:
        """Find deterministic Applicant Info candidates from key-value pairs."""
        candidates: list[Candidate] = []

        # Pre-scan applicant City/State/Zip values so `insured_address` can be concatenated.
        applicant_city: str | None = None
        applicant_state: str | None = None
        applicant_zip: str | None = None
        for pair in self.layout.get("keyValuePairs", []) or []:
            if not isinstance(pair, dict):
                continue
            key_obj = pair.get("key") or {}
            value_obj = pair.get("value") or {}
            key_text = str(key_obj.get("content") or "").strip()
            raw_value = str(value_obj.get("content") or "").strip()
            if not key_text or not raw_value:
                continue

            label_norm = self._normalize_kv_key_label(key_text)
            if self._label_indicates_non_applicant(label_norm):
                continue
            page_number, _ = self._extract_polygon(value_obj)
            if int(page_number) not in APPLICANT_KV_ALLOWED_PAGES:
                continue
            if applicant_city is None and self._label_indicates_applicant_component(
                label_norm, "city", page_number
            ):
                applicant_city = raw_value
            elif applicant_state is None and self._label_indicates_applicant_component(
                label_norm, "state", page_number
            ):
                applicant_state = raw_value
            elif applicant_zip is None and self._label_indicates_applicant_component(
                label_norm, "zip", page_number
            ):
                applicant_zip = raw_value

        for pair in self.layout.get("keyValuePairs", []) or []:
            if not isinstance(pair, dict):
                continue
            key = pair.get("key") or {}
            value = pair.get("value") or {}
            key_text = str(key.get("content") or "").strip()
            raw_value = str(value.get("content") or "").strip()
            if not key_text or not raw_value:
                continue

            label_norm = self._normalize_kv_key_label(key_text)
            if self._label_indicates_non_applicant(label_norm):
                continue

            matched_applicant_field = self._match_applicant_field_id(key_text)
            if matched_applicant_field:
                page_number, polygon = self._extract_polygon(value)
                if int(page_number) not in APPLICANT_KV_ALLOWED_PAGES:
                    continue

                if matched_applicant_field == "applicant_name":
                    validated = self._validate_applicant_name(raw_value)
                    if validated is None:
                        continue
                    context_chunk = self._format_context_chunk(key_text, validated)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=validated,
                            normalizedValue=normalize_value(validated, self._field_type(matched_applicant_field, {})),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

                if matched_applicant_field == "insured_address":
                    if label_norm in COMBINED_INSURED_ADDRESS_LABEL_NORMS:
                        combined = self._validate_insured_combined_city_state_zip(raw_value)
                        if combined is None:
                            continue
                        context_chunk = self._format_context_chunk(key_text, combined)
                        candidates.append(
                            Candidate(
                                fieldId=matched_applicant_field,
                                rawValue=combined,
                                normalizedValue=normalize_value(
                                    combined, self._field_type(matched_applicant_field, {})
                                ),
                                confidence=0.95,
                                source="KV",
                                pageNumber=page_number,
                                boundingBox=polygon,
                                contextChunk=context_chunk,
                            )
                        )
                        continue

                    street = self._validate_insured_street_address(raw_value)
                    if street is None:
                        continue

                    components: list[str] = [street]
                    for comp_value in (applicant_city, applicant_state, applicant_zip):
                        if not comp_value:
                            continue
                        # Avoid duplicates when street value already contains city/state/zip.
                        if comp_value.lower() in street.lower():
                            continue
                        components.append(comp_value)
                    validated_address = ", ".join(components)
                    context_chunk = self._format_context_chunk(key_text, validated_address)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=validated_address,
                            normalizedValue=normalize_value(
                                validated_address, self._field_type(matched_applicant_field, {})
                            ),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

                if matched_applicant_field == "sic_naics_code":
                    digits = self._extract_sic_naics_code_digits(raw_value)
                    if digits is None:
                        continue
                    context_chunk = self._format_context_chunk(key_text, digits)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=digits,
                            normalizedValue=normalize_value(
                                digits, self._field_type(matched_applicant_field, {})
                            ),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

                if matched_applicant_field == "business_description":
                    description = self._validate_business_description(raw_value)
                    if description is None:
                        continue
                    context_chunk = self._format_context_chunk(key_text, description)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=description,
                            normalizedValue=normalize_value(
                                description, self._field_type(matched_applicant_field, {})
                            ),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    sic_from_description = self._extract_sic_naics_code_digits(raw_value)
                    if sic_from_description is not None:
                        sic_context = self._format_context_chunk(key_text, sic_from_description)
                        candidates.append(
                            Candidate(
                                fieldId="sic_naics_code",
                                rawValue=sic_from_description,
                                normalizedValue=normalize_value(
                                    sic_from_description, self._field_type("sic_naics_code", {})
                                ),
                                confidence=0.95,
                                source="KV",
                                pageNumber=page_number,
                                boundingBox=polygon,
                                contextChunk=sic_context,
                            )
                        )
                    continue

                if matched_applicant_field == "telephone_number":
                    phone = self._extract_telephone_number(raw_value)
                    if phone is None:
                        continue
                    context_chunk = self._format_context_chunk(key_text, phone)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=phone,
                            normalizedValue=normalize_value(
                                phone, self._field_type(matched_applicant_field, {})
                            ),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

                if matched_applicant_field == "website":
                    validated = self._validate_page_one_applicant_text(raw_value)
                    if validated is None:
                        continue
                    context_chunk = self._format_context_chunk(key_text, validated)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=validated,
                            normalizedValue=normalize_value(
                                validated, self._field_type(matched_applicant_field, {})
                            ),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

                if matched_applicant_field == "emp_full_time":
                    emp = self._extract_emp_full_time_digits(raw_value)
                    if emp is None:
                        continue
                    context_chunk = self._format_context_chunk(key_text, emp)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=emp,
                            normalizedValue=normalize_value(emp, self._field_type(matched_applicant_field, {})),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

                if matched_applicant_field == "email_address":
                    email = self._validate_email_address(raw_value)
                    if email is None:
                        continue
                    context_chunk = self._format_context_chunk(key_text, email)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=email,
                            normalizedValue=normalize_value(email, self._field_type(matched_applicant_field, {})),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

                if matched_applicant_field == "naics_code":
                    validated = raw_value.strip()
                    if not validated:
                        continue
                    context_chunk = self._format_context_chunk(key_text, validated)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=validated,
                            normalizedValue=normalize_value(validated, self._field_type(matched_applicant_field, {})),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

                if matched_applicant_field == "year_established":
                    validated_year = self._validate_year_established(raw_value)
                    if validated_year is None:
                        continue
                    context_chunk = self._format_context_chunk(key_text, validated_year)
                    candidates.append(
                        Candidate(
                            fieldId=matched_applicant_field,
                            rawValue=validated_year,
                            normalizedValue=normalize_value(
                                validated_year, self._field_type(matched_applicant_field, {})
                            ),
                            confidence=0.95,
                            source="KV",
                            pageNumber=page_number,
                            boundingBox=polygon,
                            contextChunk=context_chunk,
                        )
                    )
                    continue

        return candidates

    def table_hunter(self) -> list[Candidate]:
        """Find candidates from document-level tables."""
        candidates: list[Candidate] = []
        tables = self.layout.get("documentTables", []) or []

        for table in tables:
            if not isinstance(table, dict):
                continue
            cells = table.get("cells", []) or []
            if not cells:
                continue

            # Map table cells by (rowIndex, columnIndex).
            by_pos: dict[tuple[int, int], dict[str, Any]] = {}
            max_row = 0
            max_col = 0
            for cell in cells:
                if not isinstance(cell, dict):
                    continue
                r = int(cell.get("rowIndex", 0))
                c = int(cell.get("columnIndex", 0))
                by_pos[(r, c)] = cell
                max_row = max(max_row, r)
                max_col = max(max_col, c)

            # Look for "Limit"/"Retention" in header rows (first 2 rows).
            header_columns: dict[str, int] = {}
            for r in range(min(2, max_row + 1)):
                for c in range(max_col + 1):
                    cell = by_pos.get((r, c))
                    if not cell:
                        continue
                    text = str(cell.get("content") or "").strip().lower()
                    if "limit" in text:
                        header_columns["limit"] = c
                    if "retention" in text:
                        header_columns["retention"] = c

            if not header_columns:
                continue

            # Find row where first column references Employment Practices.
            target_row: int | None = None
            for r in range(max_row + 1):
                first_col = by_pos.get((r, 0))
                if not first_col:
                    continue
                label_text = str(first_col.get("content") or "").strip().lower()
                if "employment practices" in label_text:
                    target_row = r
                    break

            if target_row is None:
                continue

            for field_id, config in CANONICAL_FIELD_REGISTRY.items():
                if not isinstance(config, dict):
                    continue
                aliases = [str(a).lower() for a in config.get("aliases", []) if isinstance(a, str)]
                if "employment practices" not in aliases:
                    continue

                header_name = str(config.get("columnHeader") or "").strip().lower()
                if header_name not in header_columns:
                    continue
                col_idx = header_columns[header_name]
                value_cell = by_pos.get((target_row, col_idx))
                if not value_cell:
                    continue

                raw_value = str(value_cell.get("content") or "").strip()
                if not raw_value:
                    continue
                page_number, polygon = self._extract_polygon(value_cell)
                line_idx = self._find_line_index(page_number, raw_value, fallback="Employment Practices")

                candidates.append(
                    Candidate(
                        fieldId=field_id,
                        rawValue=raw_value,
                        normalizedValue=normalize_value(raw_value, self._field_type(field_id, config)),
                        confidence=0.75,
                        source="Table",
                        pageNumber=page_number,
                        boundingBox=polygon,
                        contextChunk=self._get_line_context(line_idx),
                    )
                )

        return candidates

    def _select_llm_table_anchor(
        self,
        field_id: str,
        raw_value: str,
        table_blocks: list[dict[str, Any]],
    ) -> tuple[int, list[float]]:
        """Pick the best table anchor for an LLM field candidate."""
        if not table_blocks:
            return 1, [0.0] * 8

        value_probe = str(raw_value).strip().lower()
        keyword_map: dict[str, tuple[str, ...]] = {
            "total_assets": ("total assets", "net assets", "assets", "financial summary"),
            "net_income": ("net income", "income", "revenue", "financial summary"),
            "revenue": ("revenue", "gross revenue", "sales", "financial summary"),
            "profit": ("profit", "operating income", "net profit", "financial summary"),
            "emp_full_time": ("full time", "employee", "headcount", "employees"),
            "emp_part_time": ("part time", "employee", "headcount", "employees"),
            "emp_independent_contractors": ("independent contractor", "contractor", "employee"),
            "emp_temporary_leased": ("temporary", "leased", "employee"),
            "emp_full_time_ca": ("california", "ca", "full time"),
            "emp_part_time_ca": ("california", "ca", "part time"),
        }
        keywords = keyword_map.get(field_id, ())

        for block in table_blocks:
            text = str(block.get("markdown") or "").lower()
            if value_probe and value_probe in text and (not keywords or any(k in text for k in keywords)):
                return int(block.get("pageNumber") or 1), self._coerce_polygon(block.get("boundingBox"))

        for block in table_blocks:
            text = str(block.get("markdown") or "").lower()
            if value_probe and value_probe in text:
                return int(block.get("pageNumber") or 1), self._coerce_polygon(block.get("boundingBox"))

        for block in table_blocks:
            text = str(block.get("markdown") or "").lower()
            if keywords and any(k in text for k in keywords):
                return int(block.get("pageNumber") or 1), self._coerce_polygon(block.get("boundingBox"))

        first = table_blocks[0]
        return int(first.get("pageNumber") or 1), self._coerce_polygon(first.get("boundingBox"))

    async def _resolve_complex_fields_via_llm(self) -> list[Candidate]:
        """Extract table-only fields via Azure OpenAI JSON mode; returns empty on skip or failure."""
        table_blocks = serialize_tables_for_llm(self.layout, max_pages=5)
        markdown = "\n\n".join(str(block.get("markdown") or "") for block in table_blocks)
        if not markdown.strip():
            return []

        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
        api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "").strip()
        if not endpoint or not api_key or not deployment:
            logger.warning(
                "Azure OpenAI environment not fully configured; skipping LLM table extraction",
            )
            return []

        try:
            system_prompt = _COGNITIVE_PROMPT_PATH.read_text(encoding="utf-8")
            client = get_openai_client()
            keys = ", ".join(COGNITIVE_FIELD_IDS)
            user_content = (
                "Extract values into a JSON object with exactly these keys "
                f"(use null for missing values): {keys}.\n\n"
                "Include headcount fields, total_assets, net_income, revenue, and profit from the tables "
                "when present.\n\n"
                "For net_income: if no row or column explicitly labeled Net Income (or net loss) is present, "
                "but Operating Income is shown, use Operating Income as the value for net_income.\n\n"
                "IMPORTANT: Return all numerical values as plain strings within the JSON object "
                '(e.g., "5000" not 5000). Do not include currency symbols or commas.\n\n'
                f"---\n\n{markdown}"
            )
            completion = await client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
            )
            raw_text = completion.choices[0].message.content
            if not raw_text:
                return []
            data = json.loads(raw_text)
            parsed = CognitiveExtraction.model_validate(data)
        except Exception:
            logger.exception("LLM cognitive table extraction failed")
            return []

        chunk = markdown if len(markdown) <= 2000 else f"{markdown[:2000]}…"

        candidates: list[Candidate] = []
        for field_id in COGNITIVE_FIELD_IDS:
            if field_id in _LLM_PROTECTED_FIELD_IDS:
                continue
            raw_val = getattr(parsed, field_id, None)
            if raw_val is None:
                continue
            raw_str = str(raw_val).strip()
            if not raw_str:
                continue
            lowered = raw_str.lower()
            if lowered in ("null", "none", "n/a"):
                continue
            cfg = CANONICAL_FIELD_REGISTRY.get(field_id, {})
            if not isinstance(cfg, dict):
                cfg = {}
            anchor_page, anchor_bbox = self._select_llm_table_anchor(field_id, raw_str, table_blocks)
            candidates.append(
                Candidate(
                    fieldId=field_id,
                    rawValue=raw_str,
                    normalizedValue=normalize_value(raw_str, self._field_type(field_id, cfg)),
                    confidence=0.85,
                    source="LLM-TABLE",
                    pageNumber=anchor_page,
                    boundingBox=anchor_bbox,
                    contextChunk=chunk,
                )
            )
        return candidates

    async def build(self) -> list[Candidate]:
        """Build Applicant Info candidates: deterministic KV first, then LLM table fill for gaps."""
        kv = self.kv_hunter()
        kv_ids = {c.fieldId for c in kv}
        llm = await self._resolve_complex_fields_via_llm()
        merged: list[Candidate] = list(kv)
        for candidate in llm:
            if candidate.fieldId in _LLM_PROTECTED_FIELD_IDS:
                continue
            if candidate.fieldId in kv_ids:
                continue
            merged.append(candidate)
        return merged

    def _get_line_context(self, line_index: int | None) -> str:
        """Return current line + two lines preceding, across page boundaries."""
        if line_index is None or line_index < 0 or line_index >= len(self._lines):
            return ""

        start = max(0, line_index - 2)
        chunk_lines = [self._lines[i]["content"] for i in range(start, line_index + 1)]
        return "\n".join(line for line in chunk_lines if line)

    def _build_applicant_alias_index(self) -> dict[str, str]:
        # Maps normalized alias label -> canonical field id (exact equality after `normalize_kv_key_label`).
        out: dict[str, str] = {}
        for field_id, config in CANONICAL_FIELD_REGISTRY.items():
            if field_id not in APPLICANT_KV_FIELD_IDS:
                continue
            if not isinstance(config, dict):
                continue
            for alias in config.get("aliases", []) or []:
                if not isinstance(alias, str):
                    continue
                out[normalize_kv_key_label(alias)] = field_id
        return out

    def _normalize_kv_key_label(self, text: str) -> str:
        """Delegate to `normalize_kv_key_label`: strip ``(...)``, list numbering, then trailing ``:`` / ``*``."""
        return normalize_kv_key_label(text)

    def _match_applicant_field_id(self, key_text: str) -> str | None:
        norm_key = normalize_kv_key_label(key_text)
        return self._applicant_alias_index.get(norm_key)

    def _format_context_chunk(self, label_text: str, value_text: str) -> str:
        label = str(label_text).strip()
        value = str(value_text).strip()
        if label.endswith(":"):
            return f"{label} {value}"
        return f"{label}: {value}"

    def _label_indicates_applicant_component(self, label_norm: str, component: str, page_number: int) -> bool:
        # Caller already filters out non-applicant (agent/broker/etc).
        on_early_page = int(page_number) in APPLICANT_KV_ALLOWED_PAGES
        applicant_or_insured = "applicant" in label_norm or "insured" in label_norm
        if component == "city":
            if applicant_or_insured and "city" in label_norm:
                return True
            return on_early_page and label_norm == "city"
        if component == "state":
            if applicant_or_insured and "state" in label_norm:
                return True
            return on_early_page and label_norm == "state"
        if component == "zip":
            if applicant_or_insured and ("zip" in label_norm or "postal" in label_norm):
                return True
            if not on_early_page:
                return False
            return label_norm in ("zip", "zip code")
        return False

    def _label_indicates_non_applicant(self, label_norm: str) -> bool:
        # Avoid accidentally selecting agent/broker/producer "city/state/zip" fields.
        return any(
            token in label_norm for token in ("agent", "broker", "producer", "agency", "underwriter")
        )

    def _validate_applicant_name(self, raw_value: str) -> str | None:
        candidate = str(raw_value).strip()
        if len(candidate) < 3:
            return None
        return candidate

    def _validate_insured_street_address(self, raw_value: str) -> str | None:
        candidate = str(raw_value).strip()
        if not candidate:
            return None
        return candidate

    def _validate_insured_combined_city_state_zip(self, raw_value: str) -> str | None:
        candidate = str(raw_value).strip()
        if not candidate:
            return None
        return candidate

    def _validate_page_one_applicant_text(self, raw_value: str) -> str | None:
        candidate = str(raw_value).strip()
        if not candidate:
            return None
        return candidate

    def _validate_business_description(self, raw_value: str) -> str | None:
        candidate = str(raw_value).strip()
        if len(candidate) < 3:
            return None
        return candidate

    def _extract_emp_full_time_digits(self, raw_value: str) -> str | None:
        """First digit run in the value (e.g. employee headcount)."""
        text = str(raw_value).strip()
        if not text:
            return None
        for token in re.findall(r"\d+", text):
            if token:
                return str(int(token))
        return None

    def _validate_email_address(self, raw_value: str) -> str | None:
        candidate = str(raw_value).strip()
        if len(candidate) < 5 or "@" not in candidate:
            return None
        if not re.search(r"^\S+@\S+\.\S+", candidate):
            return None
        return candidate

    def _extract_sic_naics_code_digits(self, raw_value: str) -> str | None:
        """First digit run (``re.findall`` on the raw value) with length 4, 5, or 6."""
        text = str(raw_value).strip()
        if not text:
            return None
        for token in re.findall(r"\d+", text):
            if len(token) in (4, 5, 6):
                return token
        return None

    def _extract_telephone_number(self, raw_value: str) -> str | None:
        """10-digit US phone from ``(xxx) xxx-xxxx`` or digit runs in the raw value."""
        value = str(raw_value).strip()
        if not value:
            return None
        m = re.search(r"\(\s*(\d{3})\s*\)\s*(\d{3})\s*[-.]?\s*(\d{4})\b", value)
        if m:
            return f"{m.group(1)}{m.group(2)}{m.group(3)}"
        for token in re.findall(r"\d+", value):
            if len(token) == 10:
                return token
        all_digits = "".join(re.findall(r"\d+", value))
        if len(all_digits) >= 10:
            return all_digits[:10]
        return None

    def _validate_year_established(self, raw_value: str) -> str | None:
        value = str(raw_value).strip()
        if not value:
            return None
        for token in re.findall(r"\d+", value):
            if len(token) == 4:
                return token
        return None

    def _extract_polygon(self, source_obj: dict[str, Any]) -> tuple[int, list[float]]:
        """Extract page number and 8-float polygon from bounding regions or bbox."""
        regions = source_obj.get("boundingRegions")
        if isinstance(regions, list) and regions:
            first = regions[0]
            if isinstance(first, dict):
                page_number = int(first.get("pageNumber", 1) or 1)
                polygon = self._coerce_polygon(first.get("polygon"))
                if polygon:
                    return page_number, polygon

        page_number = int(source_obj.get("pageNumber", 1) or 1)
        polygon = self._coerce_polygon(source_obj.get("boundingBox"))
        return page_number, polygon

    def _coerce_polygon(self, raw_polygon: Any) -> list[float]:
        if not isinstance(raw_polygon, list):
            return [0.0] * 8
        values: list[float] = []
        for item in raw_polygon[:8]:
            try:
                values.append(float(item))
            except (TypeError, ValueError):
                values.append(0.0)
        if len(values) < 8:
            values.extend([0.0] * (8 - len(values)))
        return values

    def _build_line_index(self) -> list[dict[str, Any]]:
        lines_out: list[dict[str, Any]] = []
        for page in self.layout.get("pages", []) or []:
            if not isinstance(page, dict):
                continue
            page_number = int(page.get("pageNumber", 1) or 1)
            for line in page.get("lines", []) or []:
                if not isinstance(line, dict):
                    continue
                lines_out.append(
                    {
                        "pageNumber": page_number,
                        "content": str(line.get("content") or ""),
                        "boundingBox": line.get("boundingBox"),
                    }
                )
        return lines_out

    def _find_line_index(self, page_number: int, needle: str, fallback: str = "") -> int | None:
        probe = needle.strip().lower()
        fallback_probe = fallback.strip().lower()
        for idx, line in enumerate(self._lines):
            if int(line["pageNumber"]) != int(page_number):
                continue
            text = line["content"].lower()
            if probe and probe in text:
                return idx
        for idx, line in enumerate(self._lines):
            if int(line["pageNumber"]) != int(page_number):
                continue
            text = line["content"].lower()
            if fallback_probe and fallback_probe in text:
                return idx
        return None

    def _field_type(self, field_id: str, config: dict[str, Any]) -> str:
        regex_raw = config.get("regex")
        regex = str(regex_raw or "")
        if regex == DATE_PATTERN or "date" in field_id:
            return "date"
        if (
            "currency" in regex.lower()
            or regex_raw == CURRENCY_PATTERN
            or any(token in field_id for token in ("limit", "retention", "amount"))
        ):
            return "currency"
        return field_id
