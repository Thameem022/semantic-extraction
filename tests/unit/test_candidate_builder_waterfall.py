"""Tests for CandidateBuilder 3-call LLM extraction."""

from __future__ import annotations

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.candidate_builder import CandidateBuilder
from shared.models.ingestion_schema import (
    CoverageDetails,
    EmployeeCategory,
    EPLISpecificQuestions,
    GeneralInformation,
    RiskAssessment,
    StructuredIngestionPackage,
)


def _sample_layout() -> dict:
    return {
        "keyValuePairs": [
            {
                "key": {
                    "content": "Name of Applicant:",
                    "boundingRegions": [{"pageNumber": 1, "polygon": [0] * 8}],
                    "spans": [],
                },
                "value": {
                    "content": "Acme Corp",
                    "boundingRegions": [{"pageNumber": 1, "polygon": [0] * 8}],
                    "spans": [],
                },
            },
            {
                "key": {
                    "content": "Employment Practices Liability",
                    "boundingRegions": [{"pageNumber": 2, "polygon": [0] * 8}],
                    "spans": [],
                },
                "value": {
                    "content": ":selected:",
                    "boundingRegions": [{"pageNumber": 2, "polygon": [0] * 8}],
                    "spans": [],
                },
            },
        ],
        "pages": [
            {
                "pageNumber": 1,
                "lines": [
                    {"content": "Name of Applicant: Acme Corp"},
                    {"content": "City: Dallas"},
                ],
            },
            {
                "pageNumber": 2,
                "lines": [
                    {"content": "Employment Practices Liability: selected"},
                ],
            },
        ],
        "documentTables": [
            {
                "rowCount": 2,
                "columnCount": 2,
                "cells": [
                    {
                        "rowIndex": 0,
                        "columnIndex": 0,
                        "content": "Coverage",
                        "boundingRegions": [{"pageNumber": 1, "polygon": [0] * 8}],
                    },
                    {
                        "rowIndex": 0,
                        "columnIndex": 1,
                        "content": "Limit",
                        "boundingRegions": [{"pageNumber": 1, "polygon": [0] * 8}],
                    },
                    {
                        "rowIndex": 1,
                        "columnIndex": 0,
                        "content": "Employment Practices",
                        "boundingRegions": [{"pageNumber": 1, "polygon": [0] * 8}],
                    },
                    {
                        "rowIndex": 1,
                        "columnIndex": 1,
                        "content": "$1,000,000",
                        "boundingRegions": [{"pageNumber": 1, "polygon": [0] * 8}],
                    },
                ],
            }
        ],
    }


def _mock_general_coverage_response() -> str:
    return json.dumps(
        {
            "GeneralInformation": {
                "Applicant": "Acme Corp",
                "Address_Street": "123 Main St",
                "Address_City": "Dallas",
                "Address_State": "TX",
                "Address_ZipCode": "75001",
                "ApplicantsWebsite": None,
                "NAICSCode": "8111",
                "DateOfFormation": None,
                "NatureOfOperations": None,
                "Contact_Name": None,
                "Contact_Title": None,
                "Contact_Telephone": None,
                "Contact_Email": None,
                "RiskMgmtContact_Name": None,
                "RiskMgmtContact_Title": None,
                "RiskMgmtContact_Telephone": None,
                "RiskMgmtContact_Email": None,
                "TaxStatus": None,
                "OrganizationalStructure": None,
                "TotalNumberOfLocations": None,
                "TotalNumberOfEmployees": 33,
                "Employees_US": None,
                "Employees_California": None,
                "Employees_Canada": None,
                "Employees_OutsideUSandCAN": None,
                "CountriesOfOperationOutsideUS": None,
                "RequestedEffectiveDate": None,
            },
            "CoverageDetails": {
                "CoverageType": "Employment Practices Liability",
                "LimitRequested": "1000000",
                "RetentionRequested": None,
                "SharedLimit": None,
                "DutyToDefend": None,
                "CurrentLimit": None,
                "CurrentRetention": None,
                "CurrentPremium": None,
                "CurrentCarrier": None,
            },
        }
    )


def _mock_employee_risk_response() -> str:
    return json.dumps(
        {
            "EmployeeCategory": {
                "FullTimeEmployees_CurrentYearTotal": 33,
                "FullTimeEmployees_CurrentYearCA": None,
                "FullTimeEmployees_PriorYearTotal": None,
                "FullTimeEmployees_PriorYearCA": None,
                "PartTimeEmployees_CurrentYearTotal": 5,
                "PartTimeEmployees_CurrentYearCA": None,
                "PartTimeEmployees_PriorYearTotal": None,
                "PartTimeEmployees_PriorYearCA": None,
                "IndependentContractors_CurrentYearTotal": 2,
                "IndependentContractors_CurrentYearCA": None,
                "Volunteers_CurrentYearTotal": None,
                "Volunteers_CurrentYearCA": None,
                "Top3StatesByEmployeeCount_State1": "Texas",
                "Top3StatesByEmployeeCount_State2": None,
                "Top3StatesByEmployeeCount_State3": None,
                "SalaryRanges_GreaterThan125k": None,
                "SalaryRanges_LessThan125k": None,
            },
            "RiskAssessment": {
                "NoticeOfClaimOrPotentialClaim": False,
                "Explanation": None,
            },
        }
    )


def _mock_epli_response() -> str:
    return json.dumps(
        {
            "EPLISpecificQuestions": {
                "WorkforceReduction_Impacted": False,
                "ConsultedOutsideCounsel": True,
                "ReviewedExemptNonExemptClassifications": None,
                "CompletedWageAndHourAudit": None,
                "EmploymentDisputeLitigationOver10k": False,
                "EEOCOrSimilarProceeding": False,
                "CrisisExpenseCoverage": None,
                "WorkplaceViolenceExpenseCoverage": None,
                "WageAndHourDefenseExpensesCoverage": None,
                "AdditionalDefenseExpenseLimitCoverage": None,
            }
        }
    )


def _patch_openai_client_close(mock_azure: MagicMock) -> None:
    """AsyncAzureOpenAI is closed after each LLM call; tests must mock ``close()``."""
    mock_azure.return_value.close = AsyncMock()


def _make_mock_completion(payload: str) -> MagicMock:
    mock_choice = MagicMock()
    mock_choice.message.content = payload
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion


_OPENAI_ENV = {
    "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
    "AZURE_OPENAI_API_KEY": "test-key",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-test",
}


@patch.dict(os.environ, _OPENAI_ENV, clear=False)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_returns_structured_package(mock_azure: MagicMock) -> None:
    """All 3 LLM calls succeed and build() assembles a full StructuredIngestionPackage."""
    responses = [
        _make_mock_completion(_mock_general_coverage_response()),
        _make_mock_completion(_mock_employee_risk_response()),
        _make_mock_completion(_mock_epli_response()),
    ]
    mock_azure.return_value.chat.completions.create = AsyncMock(side_effect=responses)
    _patch_openai_client_close(mock_azure)

    builder = CandidateBuilder(_sample_layout())
    result = asyncio.run(builder.build())

    assert isinstance(result, StructuredIngestionPackage)
    assert result.GeneralInformation.Applicant == "Acme Corp"
    assert result.GeneralInformation.TotalNumberOfEmployees == 33
    assert result.CoverageDetails.CoverageType == "Employment Practices Liability"
    assert result.EmployeeCategory.FullTimeEmployees_CurrentYearTotal == 33
    assert result.EmployeeCategory.PartTimeEmployees_CurrentYearTotal == 5
    assert result.RiskAssessment.NoticeOfClaimOrPotentialClaim is False
    assert result.EPLISpecificQuestions.ConsultedOutsideCounsel is True
    assert result.EPLISpecificQuestions.WorkforceReduction_Impacted is False


@patch.dict(os.environ, _OPENAI_ENV, clear=False)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_makes_three_sequential_llm_calls(mock_azure: MagicMock) -> None:
    """Verify exactly 3 LLM calls are made."""
    responses = [
        _make_mock_completion(_mock_general_coverage_response()),
        _make_mock_completion(_mock_employee_risk_response()),
        _make_mock_completion(_mock_epli_response()),
    ]
    mock_create = AsyncMock(side_effect=responses)
    mock_azure.return_value.chat.completions.create = mock_create
    _patch_openai_client_close(mock_azure)

    builder = CandidateBuilder(_sample_layout())
    asyncio.run(builder.build())

    assert mock_create.call_count == 3


@patch.dict(os.environ, _OPENAI_ENV, clear=False)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_graceful_fallback_on_call1_failure(mock_azure: MagicMock) -> None:
    """If call 1 fails, GeneralInformation + CoverageDetails are empty; others still populated."""
    responses = [
        RuntimeError("call 1 quota exceeded"),
        _make_mock_completion(_mock_employee_risk_response()),
        _make_mock_completion(_mock_epli_response()),
    ]
    mock_azure.return_value.chat.completions.create = AsyncMock(side_effect=responses)
    _patch_openai_client_close(mock_azure)

    builder = CandidateBuilder(_sample_layout())
    result = asyncio.run(builder.build())

    assert isinstance(result, StructuredIngestionPackage)
    assert result.GeneralInformation.Applicant is None
    assert result.CoverageDetails.CoverageType is None
    assert result.EmployeeCategory.FullTimeEmployees_CurrentYearTotal == 33
    assert result.EPLISpecificQuestions.ConsultedOutsideCounsel is True


@patch.dict(os.environ, _OPENAI_ENV, clear=False)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_graceful_fallback_on_call2_failure(mock_azure: MagicMock) -> None:
    """If call 2 fails, EmployeeCategory + RiskAssessment are empty; others still populated."""
    responses = [
        _make_mock_completion(_mock_general_coverage_response()),
        RuntimeError("call 2 timeout"),
        _make_mock_completion(_mock_epli_response()),
    ]
    mock_azure.return_value.chat.completions.create = AsyncMock(side_effect=responses)
    _patch_openai_client_close(mock_azure)

    builder = CandidateBuilder(_sample_layout())
    result = asyncio.run(builder.build())

    assert result.GeneralInformation.Applicant == "Acme Corp"
    assert result.EmployeeCategory.FullTimeEmployees_CurrentYearTotal is None
    assert result.RiskAssessment.NoticeOfClaimOrPotentialClaim is None
    assert result.EPLISpecificQuestions.ConsultedOutsideCounsel is True


@patch.dict(os.environ, _OPENAI_ENV, clear=False)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_graceful_fallback_on_call3_failure(mock_azure: MagicMock) -> None:
    """If call 3 fails, EPLISpecificQuestions is empty; others still populated."""
    responses = [
        _make_mock_completion(_mock_general_coverage_response()),
        _make_mock_completion(_mock_employee_risk_response()),
        RuntimeError("call 3 failed"),
    ]
    mock_azure.return_value.chat.completions.create = AsyncMock(side_effect=responses)
    _patch_openai_client_close(mock_azure)

    builder = CandidateBuilder(_sample_layout())
    result = asyncio.run(builder.build())

    assert result.GeneralInformation.Applicant == "Acme Corp"
    assert result.EmployeeCategory.FullTimeEmployees_CurrentYearTotal == 33
    assert result.EPLISpecificQuestions.WorkforceReduction_Impacted is None


def test_build_returns_empty_package_when_no_openai_env() -> None:
    """Without Azure OpenAI env vars, build() returns an all-null package."""
    builder = CandidateBuilder({"keyValuePairs": [], "pages": [], "documentTables": []})
    result = asyncio.run(builder.build())

    assert isinstance(result, StructuredIngestionPackage)
    assert result.GeneralInformation.Applicant is None
    assert result.CoverageDetails.CoverageType is None
    assert result.EmployeeCategory.FullTimeEmployees_CurrentYearTotal is None
    assert result.RiskAssessment.NoticeOfClaimOrPotentialClaim is None
    assert result.EPLISpecificQuestions.WorkforceReduction_Impacted is None


@patch.dict(os.environ, _OPENAI_ENV, clear=False)
@patch("shared.candidate_builder.AsyncAzureOpenAI")
def test_build_all_calls_fail_returns_empty_package(mock_azure: MagicMock) -> None:
    """If all 3 calls raise, build() still returns a valid (all-null) package."""
    mock_azure.return_value.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("total failure")
    )
    _patch_openai_client_close(mock_azure)

    builder = CandidateBuilder(_sample_layout())
    result = asyncio.run(builder.build())

    assert isinstance(result, StructuredIngestionPackage)
    assert result.GeneralInformation.Applicant is None
    assert result.EmployeeCategory.FullTimeEmployees_CurrentYearTotal is None
    assert result.EPLISpecificQuestions.WorkforceReduction_Impacted is None
