"""
Canonical Field Registry: source of truth for which fields the pipeline extracts.

Exposes get_all_fields(), get_field_by_id(), and get_field_ids() for use by
Candidate Builder, Embedding Generator, and Top K Field Retriever.
"""

from .manager import get_all_fields, get_field_by_id, get_field_ids

__all__ = ["get_all_fields", "get_field_by_id", "get_field_ids"]