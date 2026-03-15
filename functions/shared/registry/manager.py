"""
Canonical Field Registry manager.

Loads canonical field definitions from canonical_fields.json and exposes
get_all_fields(), get_field_by_id(), and get_field_ids() for use by the
Candidate Builder, Embedding Generator, and Top K Field Retriever.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Path to the JSON file, relative to this module (works in dev and when deployed).
_REGISTRY_PATH = Path(__file__).resolve().parent / "canonical_fields.json"

# In-memory cache so we only read the file once.
_cached_fields: list[dict[str, Any]] | None = None


def _load_fields() -> list[dict[str, Any]]:
    """Load and parse canonical_fields.json. Raises if file is missing or invalid."""
    global _cached_fields
    if _cached_fields is not None:
        return _cached_fields

    if not _REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Canonical fields file not found: {_REGISTRY_PATH}")

    with open(_REGISTRY_PATH, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("canonical_fields.json must contain a JSON array of field objects")

    _cached_fields = data
    return _cached_fields


def get_all_fields() -> list[dict[str, Any]]:
    """
    Return all canonical field definitions.

    Each item is a dict with keys: id, name, description, dataType (optional), aliases (optional).
    """
    return _load_fields()


def get_field_by_id(field_id: str) -> dict[str, Any] | None:
    """
    Return the canonical field with the given id, or None if not found.
    """
    for field in _load_fields():
        if field.get("id") == field_id:
            return field
    return None


def get_field_ids() -> list[str]:
    """
    Return the list of all canonical field ids (for Top K retriever or validation).
    """
    return [f.get("id") for f in _load_fields() if f.get("id")]