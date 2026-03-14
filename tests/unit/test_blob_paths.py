"""Tests for shared.blob_paths."""

import pytest

from shared.blob_paths import (
    get_ocr_layout_blob_path,
    get_ocr_raw_blob_path,
    LAYOUT_FILENAME,
    OCR_LAYOUT_CONTAINER,
    OCR_RAW_CONTAINER,
    RAW_OCR_FILENAME,
)


class TestGetOcrRawBlobPath:
    def test_returns_expected_path(self):
        assert get_ocr_raw_blob_path("1234") == "ocr-raw/1234/document_intelligence.json"

    def test_strips_whitespace(self):
        assert get_ocr_raw_blob_path("  ab-cd  ") == "ocr-raw/ab-cd/document_intelligence.json"

    def test_raises_on_empty(self):
        with pytest.raises(ValueError, match="non-empty"):
            get_ocr_raw_blob_path("")

    def test_raises_on_whitespace_only(self):
        with pytest.raises(ValueError, match="non-empty"):
            get_ocr_raw_blob_path("   ")

    def test_raises_on_none(self):
        with pytest.raises(ValueError, match="must not be None"):
            get_ocr_raw_blob_path(None)  # type: ignore[arg-type]


class TestGetOcrLayoutBlobPath:
    def test_returns_expected_path(self):
        assert get_ocr_layout_blob_path("1234") == "ocr-layout/1234/layout.json"

    def test_strips_whitespace(self):
        assert get_ocr_layout_blob_path("  doc-id  ") == "ocr-layout/doc-id/layout.json"

    def test_raises_on_empty(self):
        with pytest.raises(ValueError, match="non-empty"):
            get_ocr_layout_blob_path("")

    def test_raises_on_none(self):
        with pytest.raises(ValueError, match="must not be None"):
            get_ocr_layout_blob_path(None)  # type: ignore[arg-type]


class TestConstants:
    def test_containers_and_filenames(self):
        assert OCR_RAW_CONTAINER == "ocr-raw"
        assert OCR_LAYOUT_CONTAINER == "ocr-layout"
        assert RAW_OCR_FILENAME == "document_intelligence.json"
        assert LAYOUT_FILENAME == "layout.json"
