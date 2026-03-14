"""Central status definitions for the semantic extraction pipeline."""

RECEIVED = "RECEIVED"
OCR_STARTED = "OCR_STARTED"
OCR_COMPLETE = "OCR_COMPLETE"
OCR_FAILED = "OCR_FAILED"

# Future pipeline placeholders
CANDIDATES_BUILT = "CANDIDATES_BUILT"
RETRIEVAL_COMPLETE = "RETRIEVAL_COMPLETE"
RESOLVED = "RESOLVED"
ROUTED_TO_HITL = "ROUTED_TO_HITL"

ALL_STATUSES = {
    RECEIVED,
    OCR_STARTED,
    OCR_COMPLETE,
    OCR_FAILED,
    CANDIDATES_BUILT,
    RETRIEVAL_COMPLETE,
    RESOLVED,
    ROUTED_TO_HITL,
}


def is_valid_status(status: str) -> bool:
    """Return True when the provided value is a known pipeline status."""
    return status in ALL_STATUSES
