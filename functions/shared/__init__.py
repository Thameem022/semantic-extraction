"""Shared exports for semantic extraction Azure Functions."""

from .candidate_builder import CandidateBuilder
from .field_registry import CANONICAL_FIELD_REGISTRY, normalize_value
from .models.candidate import Candidate
from .statuses import CANDIDATES_FAILED, CANDIDATES_GENERATED

__all__ = [
    "Candidate",
    "CANONICAL_FIELD_REGISTRY",
    "normalize_value",
    "CandidateBuilder",
    "CANDIDATES_GENERATED",
    "CANDIDATES_FAILED",
]

