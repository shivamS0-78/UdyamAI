from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.base import (
    LocationValidatedModel,
    normalize_swot_dict_keys,
)
from app.schemas.common import AnalysisStatus, SchemeMatchStatus, SupportedLanguage


class SWOTIndicators(BaseModel):
    strength_indicators: list[str] = Field(default_factory=list)
    weakness_indicators: list[str] = Field(default_factory=list)
    opportunity_indicators: list[str] = Field(default_factory=list)
    threat_indicators: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_swot_keys(cls, data: Any) -> Any:
        return normalize_swot_dict_keys(data)

    @property
    def strengths(self) -> list[str]:
        return self.strength_indicators

    @property
    def weaknesses(self) -> list[str]:
        return self.weakness_indicators

    @property
    def opportunities(self) -> list[str]:
        return self.opportunity_indicators

    @property
    def threats(self) -> list[str]:
        return self.threat_indicators


class FeasibilityScoreResult(BaseModel):
    market_score: float = Field(
        ..., ge=0.0, le=100.0, description="Market reach & access sub-score"
    )
    financial_score: float = Field(
        ..., ge=0.0, le=100.0, description="Capital equity & subsidy sub-score"
    )
    competition_score: float = Field(
        ..., ge=0.0, le=100.0, description="Competitor density inverse sub-score"
    )
    infrastructure_score: float = Field(
        ..., ge=0.0, le=100.0, description="Facility & logistics availability sub-score"
    )
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Inverted risk safety sub-score")
    overall_score: float = Field(
        ..., ge=0.0, le=100.0, description="Weighted overall feasibility score"
    )
    swot: SWOTIndicators = Field(default_factory=SWOTIndicators)
    data_confidence: str = Field(
        default="high",
        description="Data sufficiency & confidence level ('high', 'medium', 'low', 'insufficient')",
    )
    market_data_available: bool = Field(default=True)
    financial_data_available: bool = Field(default=True)
    competition_data_available: bool = Field(default=True)
    infrastructure_data_available: bool = Field(default=True)
    risk_data_available: bool = Field(default=True)


class FeasibilityCalculationRequest(LocationValidatedModel):
    village_id: UUID | None = Field(default=None, description="Optional target village UUID")
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    radius_km: float = Field(default=10.0, ge=0.1, le=50.0)
    business_category_id: UUID | None = Field(default=None)
    available_capital: float = Field(default=0.0, ge=0.0)
    desired_project_cost: float = Field(default=0.0, ge=0.0)


class AnalysisRunCreate(BaseModel):
    user_id: UUID | None = Field(default=None, description="Entrepreneur user profile ID")
    location_id: UUID | str | None = Field(
        default=None, description="Village ID (UUID) or LGD location code"
    )
    village_id: UUID | str | None = Field(
        default=None, description="Alias for location_id (LGD ID or UUID)"
    )
    business_category_id: UUID | str | None = Field(
        default=None, description="Business category ID (UUID) or category slug (e.g., 'dairy')"
    )
    available_capital: float | None = Field(
        default=None,
        ge=0.0,
        le=100_000_000.0,
        description="Available capital/own investment in INR (>= 0)",
    )
    desired_project_cost: float | None = Field(
        default=None,
        gt=0.0,
        le=100_000_000.0,
        description="Desired total project setup cost in INR (> 0)",
    )
    language: SupportedLanguage = Field(
        default=SupportedLanguage.EN, description="Preferred report language ('en', 'hi', 'mr')"
    )


class AnalysisCreateResponse(BaseModel):
    analysis_id: UUID
    status: AnalysisStatus = Field(default=AnalysisStatus.CREATED)
    id: UUID | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.id is None:
            self.id = self.analysis_id


class AnalysisRunResponse(BaseModel):
    id: UUID
    analysis_id: UUID | None = None
    user_id: UUID | None = None
    location_id: UUID | None = None
    business_category_id: UUID | None = None
    available_capital: float | None = Field(default=None, ge=0)
    status: AnalysisStatus = Field(default=AnalysisStatus.CREATED)
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: Any) -> None:
        if self.analysis_id is None:
            self.analysis_id = self.id


class AnalysisStatusResponse(BaseModel):
    id: UUID
    analysis_id: UUID | None = None
    status: AnalysisStatus
    progress_percentage: int = Field(
        default=0, ge=0, le=100, description="Task execution progress percentage (0-100)"
    )
    current_step: str | None = Field(default=None, max_length=150)
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = Field(default=None, max_length=1000)

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: Any) -> None:
        if self.analysis_id is None:
            self.analysis_id = self.id


class FeasibilityAnalysisResponse(BaseModel):
    id: UUID
    analysis_run_id: UUID
    market_score: float | None = Field(default=None, ge=0.0, le=100.0)
    financial_score: float | None = Field(default=None, ge=0.0, le=100.0)
    competition_score: float | None = Field(default=None, ge=0.0, le=100.0)
    infrastructure_score: float | None = Field(default=None, ge=0.0, le=100.0)
    risk_score: float | None = Field(default=None, ge=0.0, le=100.0)
    overall_score: float | None = Field(default=None, ge=0.0, le=100.0)
    recommendation: str | None = Field(default=None, max_length=1000)
    strengths: list[str] | dict[str, Any] | None = None
    weaknesses: list[str] | dict[str, Any] | None = None
    opportunities: list[str] | dict[str, Any] | None = None
    threats: list[str] | dict[str, Any] | None = None
    risks: list[str] | dict[str, Any] | None = None
    warnings: list[str] | dict[str, Any] | None = None
    confidence: str | None = Field(default=None, max_length=50)
    data_confidence: str | None = Field(default=None, max_length=50)
    market_data_available: bool = True
    financial_data_available: bool = True
    competition_data_available: bool = True
    infrastructure_data_available: bool = True
    risk_data_available: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class FinancialSummaryResponse(BaseModel):
    estimated_project_cost: float = Field(..., gt=0, le=100_000_000.0)
    recommended_loan: float = Field(..., ge=0, le=100_000_000.0)
    estimated_subsidy: float = Field(default=0.0, ge=0, le=100_000_000.0)
    estimated_monthly_emi: float = Field(default=0.0, ge=0, le=10_000_000.0)


class SchemeMatchSummaryResponse(BaseModel):
    scheme_id: UUID
    scheme_name: str
    match_status: SchemeMatchStatus
    match_score: float | None = Field(default=None, ge=0.0, le=1.0)
    estimated_subsidy_amount: float | None = Field(default=None, ge=0.0, le=100_000_000.0)


class ReportSummaryResponse(BaseModel):
    id: UUID
    title: str | None = None
    report_file_path: str | None = None


class AnalysisFullResponse(BaseModel):
    id: UUID
    user_id: UUID
    location_id: UUID | None = None
    business_category_id: UUID | None = None
    available_capital: float | None = Field(default=None, ge=0)
    status: AnalysisStatus
    created_at: datetime
    completed_at: datetime | None = None
    feasibility_analysis: FeasibilityAnalysisResponse | None = None
    financial_summary: FinancialSummaryResponse | None = None
    matched_schemes: list[SchemeMatchSummaryResponse] = Field(default_factory=list)
    reports: list[ReportSummaryResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ConsolidatedAnalysisResponse(BaseModel):
    analysis_id: UUID
    status: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    location: dict[str, Any] | None = None
    business: dict[str, Any] | None = None
    financial: dict[str, Any] | None = None
    market: dict[str, Any] | None = None
    competition: dict[str, Any] | None = None
    schemes: list[dict[str, Any]] = Field(default_factory=list)
    feasibility: dict[str, Any] | None = None
    risks: list[dict[str, Any]] = Field(default_factory=list)
    ai_advice: dict[str, Any] | None = None

    model_config = {"from_attributes": True}
