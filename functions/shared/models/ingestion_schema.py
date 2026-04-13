"""Exact Pydantic schema matching your Data Elements for Ingestion Excel."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class GeneralInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Applicant: Optional[str] = None
    Address_Street: Optional[str] = None
    Address_City: Optional[str] = None
    Address_State: Optional[str] = None
    Address_ZipCode: Optional[str] = None
    ApplicantsWebsite: Optional[str] = None
    NAICSCode: Optional[str] = None
    DateOfFormation: Optional[str] = None
    NatureOfOperations: Optional[str] = None
    Contact_Name: Optional[str] = None
    Contact_Title: Optional[str] = None
    Contact_Telephone: Optional[str] = None
    Contact_Email: Optional[str] = None
    RiskMgmtContact_Name: Optional[str] = None
    RiskMgmtContact_Title: Optional[str] = None
    RiskMgmtContact_Telephone: Optional[str] = None
    RiskMgmtContact_Email: Optional[str] = None
    TaxStatus: Optional[str] = None
    OrganizationalStructure: Optional[str] = None
    TotalNumberOfLocations: Optional[int] = None
    TotalNumberOfEmployees: Optional[int] = None
    Employees_US: Optional[int] = None
    Employees_California: Optional[int] = None
    Employees_Canada: Optional[int] = None
    Employees_OutsideUSandCAN: Optional[int] = None
    CountriesOfOperationOutsideUS: Optional[str] = None
    RequestedEffectiveDate: Optional[str] = None


class CoverageDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    CoverageType: Optional[str] = None
    LimitRequested: Optional[str] = None
    RetentionRequested: Optional[str] = None
    SharedLimit: Optional[bool] = None
    DutyToDefend: Optional[str] = None
    CurrentLimit: Optional[str] = None
    CurrentRetention: Optional[str] = None
    CurrentPremium: Optional[str] = None
    CurrentCarrier: Optional[str] = None


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    NoticeOfClaimOrPotentialClaim: Optional[bool] = None
    Explanation: Optional[str] = None


class EmployeeCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    FullTimeEmployees_CurrentYearTotal: Optional[int] = None
    FullTimeEmployees_CurrentYearCA: Optional[int] = None
    FullTimeEmployees_PriorYearTotal: Optional[int] = None
    FullTimeEmployees_PriorYearCA: Optional[int] = None
    PartTimeEmployees_CurrentYearTotal: Optional[int] = None
    PartTimeEmployees_CurrentYearCA: Optional[int] = None
    PartTimeEmployees_PriorYearTotal: Optional[int] = None
    PartTimeEmployees_PriorYearCA: Optional[int] = None
    IndependentContractors_CurrentYearTotal: Optional[int] = None
    IndependentContractors_CurrentYearCA: Optional[int] = None
    Volunteers_CurrentYearTotal: Optional[int] = None
    Volunteers_CurrentYearCA: Optional[int] = None
    Top3StatesByEmployeeCount_State1: Optional[str] = None
    Top3StatesByEmployeeCount_State2: Optional[str] = None
    Top3StatesByEmployeeCount_State3: Optional[str] = None
    SalaryRanges_GreaterThan125k: Optional[str] = None
    SalaryRanges_LessThan125k: Optional[str] = None


class EPLISpecificQuestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    WorkforceReduction_Impacted: Optional[bool] = None
    ConsultedOutsideCounsel: Optional[bool] = None
    ReviewedExemptNonExemptClassifications: Optional[bool] = None
    CompletedWageAndHourAudit: Optional[bool] = None
    EmploymentDisputeLitigationOver10k: Optional[bool] = None
    EEOCOrSimilarProceeding: Optional[bool] = None
    CrisisExpenseCoverage: Optional[bool] = None
    WorkplaceViolenceExpenseCoverage: Optional[bool] = None
    WageAndHourDefenseExpensesCoverage: Optional[bool] = None
    AdditionalDefenseExpenseLimitCoverage: Optional[bool] = None


class StructuredIngestionPackage(BaseModel):
    """Final structured output that matches the Excel schema."""

    model_config = ConfigDict(extra="forbid")

    GeneralInformation: GeneralInformation
    CoverageDetails: CoverageDetails
    RiskAssessment: RiskAssessment
    EmployeeCategory: EmployeeCategory
    EPLISpecificQuestions: EPLISpecificQuestions
