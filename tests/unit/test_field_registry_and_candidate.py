"""Tests for shared.field_registry.normalize_value and Candidate model validation."""

import pytest
from pydantic import ValidationError

from shared.field_registry import normalize_kv_key_label, normalize_value
from shared.models.candidate import Candidate


class TestNormalizeKvKeyLabel:
    def test_strips_list_prefix_and_parentheses(self):
        assert normalize_kv_key_label("1. Name of Applicant (see note):") == "name of applicant"
        assert normalize_kv_key_label("1. Name of Applicant") == "name of applicant"
        assert normalize_kv_key_label("a. Street Address:") == "street address"

    def test_exact_match_deterministic(self):
        assert normalize_kv_key_label("  NAICS Code: ") == normalize_kv_key_label("NAICS Code:")


class TestNormalizeValue:
    def test_date_conversion_m_d_yyyy_to_iso(self):
        assert normalize_value("3/9/2026", "effective_date") == "2026-03-09"

    def test_currency_cleanup_removes_dollar_commas_and_spaces(self):
        assert normalize_value("$ 1,234,567.89", "limit_employment_practices") == "1234567.89"

    def test_fallback_trim_behavior(self):
        assert normalize_value("  ABC-123  ", "policy_number") == "ABC-123"


class TestCandidateBoundingBox:
    def test_accepts_exactly_8_floats(self):
        candidate = Candidate(
            fieldId="policy_number",
            rawValue="P-12345",
            normalizedValue="P-12345",
            confidence=0.97,
            source="KV",
            pageNumber=1,
            boundingBox=[1.0, 2.0, 3.0, 2.0, 3.0, 3.0, 1.0, 3.0],
            contextChunk="Policy No: P-12345",
        )
        assert len(candidate.boundingBox) == 8

    def test_rejects_bounding_box_not_equal_to_8(self):
        with pytest.raises(ValidationError):
            Candidate(
                fieldId="policy_number",
                rawValue="P-12345",
                normalizedValue="P-12345",
                confidence=0.97,
                source="KV",
                pageNumber=1,
                boundingBox=[1.0, 2.0, 3.0, 2.0],
                contextChunk="Policy No: P-12345",
            )
