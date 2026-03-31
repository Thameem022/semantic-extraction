"""Candidate model for semantic extraction field values."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Candidate(BaseModel):
    """Represents one extracted candidate value for a canonical field."""

    fieldId: str
    rawValue: str
    normalizedValue: str
    confidence: float
    source: str
    pageNumber: int
    boundingBox: list[float] = Field(
        ...,
        min_length=8,
        max_length=8,
        description="8-point polygon [x1, y1, x2, y2, x3, y3, x4, y4].",
    )
    contextChunk: str

    @field_validator("boundingBox")
    @classmethod
    def _validate_bounding_box_length(cls, value: list[float]) -> list[float]:
        if len(value) != 8:
            raise ValueError("boundingBox must contain exactly 8 float values.")
        return value

    @field_validator("source")
    @classmethod
    def _validate_source(cls, value: str) -> str:
        tokens = [token.strip() for token in str(value).split("|") if token.strip()]
        allowed = {"KV", "Table", "Pattern", "LLM-TABLE"}
        if not tokens or any(token not in allowed for token in tokens):
            raise ValueError("source must contain one or more of: KV, Table, Pattern, LLM-TABLE")
        return " | ".join(dict.fromkeys(tokens))
