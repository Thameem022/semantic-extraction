"""Centralized helpers for blob paths used by OCR and related artifacts."""

from typing import Final


OCR_RAW_CONTAINER: Final[str] = "ocr-raw"
OCR_LAYOUT_CONTAINER: Final[str] = "ocr-layout"

RAW_OCR_FILENAME: Final[str] = "document_intelligence.json"
LAYOUT_FILENAME: Final[str] = "layout.json"


def _validate_doc_id(doc_id: str) -> str:
    """
    Perform minimal validation/sanitization of doc_id for use in blob paths.

    The ingestion pipeline uses UUIDs for docId, so this primarily protects
    against accidental leading/trailing whitespace or empty values.
    """
    if doc_id is None:
        raise ValueError("doc_id must not be None")

    trimmed = str(doc_id).strip()
    if not trimmed:
        raise ValueError("doc_id must be a non-empty string")

    return trimmed


def get_ocr_raw_blob_path(doc_id: str) -> str:
    """
    Return the blob path for vendor/raw OCR output for a given document.

    Example:
        >>> get_ocr_raw_blob_path("1234")
        'ocr-raw/1234/document_intelligence.json'
    """
    safe_doc_id = _validate_doc_id(doc_id)
    return f"{OCR_RAW_CONTAINER}/{safe_doc_id}/{RAW_OCR_FILENAME}"


def get_ocr_layout_blob_path(doc_id: str) -> str:
    """
    Return the blob path for normalized OCR layout output for a given document.

    Example:
        >>> get_ocr_layout_blob_path("1234")
        'ocr-layout/1234/layout.json'
    """
    safe_doc_id = _validate_doc_id(doc_id)
    return f"{OCR_LAYOUT_CONTAINER}/{safe_doc_id}/{LAYOUT_FILENAME}"

