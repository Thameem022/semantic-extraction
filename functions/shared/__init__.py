"""Shared exports for semantic extraction Azure Functions."""

from .candidate_builder import CandidateBuilder
from .models.candidate import Candidate
from .models.ingestion_schema import StructuredIngestionPackage
from .statuses import CANDIDATES_FAILED, CANDIDATES_GENERATED

__all__ = [
    "Candidate",
    "CandidateBuilder",
    "StructuredIngestionPackage",
    "CANDIDATES_GENERATED",
    "CANDIDATES_FAILED",
]
