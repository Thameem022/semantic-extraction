"""Tests for CandidateBuilder KV + LLM waterfall."""

from __future__ import annotations

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import shared.candidate_builder as candidate_builder_module
from shared.candidate_builder import CandidateBuilder
from shared.models.candidate import Candidate


def _table_layout() -> dict:
    return {
        "keyValuePairs": [],
        "pages": [{"pageNumber": 1, "lines": []}],
        "documentTables": [
            {
                "rowCount": 2,
                "columnCount": 2,
                "cells": [
                    {
                        "rowIndex": 0,
                        "columnIndex": 0,
                        "content": "H1",
                        "boundingRegions": [{"pageNumber": 1, "polygon": [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]}],
                    },
                    {
                        "rowIndex": 0,
                        "columnIndex": 1,
                        "content": "H2",
                        "boundingRegions": [{"pageNumber": 1, "polygon": [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]}],
                    },
                    {
                        "rowIndex": 1,
                        "columnIndex": 0,
                        "content": "a",
                        "boundingRegions": [{"pageNumber": 1, "polygon": [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]}],
                    },
                    {
                        "rowIndex": 1,
                        "columnIndex": 1,
                        "content": "b",
                        "boundingRegions": [{"pageNumber": 1, "polygon": [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]}],
                    },
                ],
            }
        ],
    }


def _mock_completion_payload() -> str:
    return json.dumps(
        {
            "emp_full_time": None,
            "emp_part_time": "3",
            "emp_independent_contractors": None,
            "emp_temporary_leased": None,
            "emp_full_time_ca": None,
            "emp_part_time_ca": None,
            "total_assets": None,
            "net_income": None,
            "revenue": None,
            "profit": None,
        }
    )


@patch.dict(
    os.environ,
    {
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-test",
    },
    clear=False,
)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_adds_llm_candidates_when_kv_empty(mock_azure: MagicMock) -> None:
    mock_choice = MagicMock()
    mock_choice.message.content = _mock_completion_payload()
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_azure.return_value.chat.completions.create = AsyncMock(return_value=mock_completion)
    candidate_builder_module._OPENAI_CLIENT = None

    builder = CandidateBuilder(_table_layout())
    out = asyncio.run(builder.build())

    assert len(out) == 1
    assert out[0].fieldId == "emp_part_time"
    assert out[0].rawValue == "3"
    assert out[0].source == "LLM-TABLE"
    assert out[0].confidence == pytest.approx(0.85)


@patch.dict(
    os.environ,
    {
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-test",
    },
    clear=False,
)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_skips_llm_field_when_kv_already_present(mock_azure: MagicMock) -> None:
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(
        {
            "emp_full_time": "99",
            "emp_part_time": None,
            "emp_independent_contractors": None,
            "emp_temporary_leased": None,
            "emp_full_time_ca": None,
            "emp_part_time_ca": None,
            "total_assets": None,
            "net_income": None,
            "revenue": None,
            "profit": None,
        }
    )
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_azure.return_value.chat.completions.create = AsyncMock(return_value=mock_completion)
    candidate_builder_module._OPENAI_CLIENT = None

    kv_candidate = Candidate(
        fieldId="emp_full_time",
        rawValue="46",
        normalizedValue="46",
        confidence=0.95,
        source="KV",
        pageNumber=1,
        boundingBox=[0.0, 0.0, 10.0, 0.0, 10.0, 10.0, 0.0, 10.0],
        contextChunk="KV",
    )

    builder = CandidateBuilder(_table_layout())
    with patch.object(CandidateBuilder, "kv_hunter", return_value=[kv_candidate]):
        out = asyncio.run(builder.build())

    assert len(out) == 1
    assert out[0].fieldId == "emp_full_time"
    assert out[0].rawValue == "46"
    assert out[0].source == "KV"


@patch.dict(
    os.environ,
    {
        "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-test",
    },
    clear=False,
)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_returns_kv_only_when_llm_raises(mock_azure: MagicMock) -> None:
    mock_azure.return_value.chat.completions.create = AsyncMock(side_effect=RuntimeError("quota"))
    candidate_builder_module._OPENAI_CLIENT = None

    kv_candidate = Candidate(
        fieldId="website",
        rawValue="https://example.com",
        normalizedValue="https://example.com",
        confidence=0.95,
        source="KV",
        pageNumber=1,
        boundingBox=[0.0, 0.0, 10.0, 0.0, 10.0, 10.0, 0.0, 10.0],
        contextChunk="KV",
    )

    builder = CandidateBuilder(_table_layout())
    with patch.object(CandidateBuilder, "kv_hunter", return_value=[kv_candidate]):
        out = asyncio.run(builder.build())

    assert len(out) == 1
    assert out[0].fieldId == "website"


def test_build_skips_llm_when_no_tables_and_no_openai_env() -> None:
    candidate_builder_module._OPENAI_CLIENT = None
    builder = CandidateBuilder({"keyValuePairs": [], "pages": []})
    out = asyncio.run(builder.build())
    assert out == []
