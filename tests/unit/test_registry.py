"""Tests for shared.registry (canonical field registry)."""

import pytest

from shared.registry import get_all_fields, get_field_by_id, get_field_ids


class TestGetAllFields:
    def test_returns_non_empty_list(self):
        fields = get_all_fields()
        assert isinstance(fields, list)
        assert len(fields) >= 1

    def test_each_field_has_id(self):
        fields = get_all_fields()
        for field in fields:
            assert "id" in field, f"Field missing 'id': {field}"


class TestGetFieldById:
    def test_invoice_date_returns_dict_with_name(self):
        field = get_field_by_id("invoice_date")
        assert field is not None
        assert isinstance(field, dict)
        assert field.get("name") == "Invoice Date"

    def test_nonexistent_returns_none(self):
        assert get_field_by_id("nonexistent") is None


class TestGetFieldIds:
    def test_returns_list_with_invoice_date(self):
        ids = get_field_ids()
        assert isinstance(ids, list)
        assert "invoice_date" in ids

    def test_length_at_least_one(self):
        assert len(get_field_ids()) >= 1