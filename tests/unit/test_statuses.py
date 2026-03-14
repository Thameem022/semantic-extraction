"""Tests for shared.statuses."""

import pytest

from shared.statuses import (
    ALL_STATUSES,
    is_valid_status,
    OCR_COMPLETE,
    OCR_FAILED,
    OCR_STARTED,
    RECEIVED,
)


class TestIsValidStatus:
    def test_received(self):
        assert is_valid_status(RECEIVED) is True

    def test_ocr_started(self):
        assert is_valid_status(OCR_STARTED) is True

    def test_ocr_complete(self):
        assert is_valid_status(OCR_COMPLETE) is True

    def test_ocr_failed(self):
        assert is_valid_status(OCR_FAILED) is True

    def test_invalid_returns_false(self):
        assert is_valid_status("UNKNOWN") is False
        assert is_valid_status("") is False
        assert is_valid_status("received") is False  # case-sensitive


class TestAllStatuses:
    def test_contains_expected_statuses(self):
        assert RECEIVED in ALL_STATUSES
        assert OCR_STARTED in ALL_STATUSES
        assert OCR_COMPLETE in ALL_STATUSES
        assert OCR_FAILED in ALL_STATUSES

    def test_all_statuses_are_non_empty_strings(self):
        for s in ALL_STATUSES:
            assert isinstance(s, str)
            assert len(s) > 0
