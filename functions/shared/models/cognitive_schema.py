"""Structured extraction schema for cognitive / LLM outputs."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class CognitiveExtraction(BaseModel):
    """Schema for structured LLM extraction from insurance application tables. Values must be returned exactly as they appear in the source text (e.g., '46', '$1,000,000')."""

    model_config = ConfigDict(coerce_numbers_to_str=True)

    emp_full_time: Optional[Any] = Field(
        default=None, description="Current total full-time employees."
    )
    emp_part_time: Optional[Any] = Field(
        default=None, description="Current total part-time employees."
    )
    emp_independent_contractors: Optional[Any] = Field(
        default=None, description="Current total independent contractors."
    )
    emp_temporary_leased: Optional[Any] = Field(
        default=None,
        description="Current total temporary or leased employees.",
    )
    emp_full_time_ca: Optional[Any] = Field(
        default=None,
        description="Full-time employees specifically located in California.",
    )
    emp_part_time_ca: Optional[Any] = Field(
        default=None,
        description="Part-time employees specifically located in California.",
    )
    total_assets: Optional[Any] = Field(
        default=None,
        description="Total assets from the most recent fiscal year end.",
    )
    net_income: Optional[Any] = Field(
        default=None,
        description="Net income or net loss from the most recent fiscal year end.",
    )
    revenue: Optional[Any] = Field(
        default=None,
        description="Revenue or gross revenue from the most recent fiscal year end.",
    )
    profit: Optional[Any] = Field(
        default=None,
        description="Profit, operating income, or similar bottom-line measure (most recent FYE).",
    )
