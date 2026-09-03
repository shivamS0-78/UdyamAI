from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import BeneficiaryCategory, SchemeMatchStatus


class SchemeResponse(BaseModel):
    id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    agency_name: str | None = Field(default=None, max_length=255)
    state: str | None = Field(default=None, max_length=100)
    active: bool = True
    official_url: str | None = Field(default=None, max_length=500)
    source: str | None = Field(default=None, max_length=255)
    created_at: datetime

    model_config = {"from_attributes": True}


class SchemeMatchRequest(BaseModel):
    analysis_run_id: UUID | None = None
    applicant_age: int | None = Field(
        default=None, ge=18, le=100, description="Applicant age in years (18 to 100)"
    )
    category: BeneficiaryCategory | None = Field(
        default=None, description="Beneficiary social category (SC, ST, OBC, General, Women, etc.)"
    )
    annual_income: float | None = Field(
        default=None, ge=0, le=100_000_000.0, description="Annual household income in INR"
    )
    location_id: UUID | None = Field(default=None, description="Target village location ID")
    business_category_id: UUID | None = Field(
        default=None, description="Target business category ID"
    )
    desired_project_cost: float | None = Field(
        default=None, gt=0, le=100_000_000.0, description="Total project investment cost in INR"
    )
    available_capital: float | None = Field(
        default=None, ge=0, le=100_000_000.0, description="Available capital/own investment in INR"
    )


class SchemeMatchResultResponse(BaseModel):
    scheme_id: UUID
    scheme_name: str
    match_status: SchemeMatchStatus
    match_score: float | None = Field(default=None, ge=0.0, le=1.0)
    matched_conditions: dict[str, Any] | None = None
    failed_conditions: dict[str, Any] | None = None
    missing_information: dict[str, Any] | None = None
    estimated_subsidy_amount: float | None = Field(default=None, ge=0.0, le=100_000_000.0)
    estimated_loan_amount: float | None = Field(default=None, ge=0.0, le=100_000_000.0)
    estimated_project_cost: float | None = Field(default=None, ge=0.0, le=100_000_000.0)
    verification_required: bool = True
    authoritative_approval_status: str | None = Field(
        default=None,
        description="Official approval status if provided authoritatively by scheme authority",
    )

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def validate_no_unauthoritative_guarantees(self) -> "SchemeMatchResultResponse":
        if not self.authoritative_approval_status:
            prohibited = ["approved", "guaranteed loan", "guaranteed eligibility"]
            text_sources: list[str] = [self.scheme_name]
            for cond in (self.matched_conditions, self.failed_conditions, self.missing_information):
                if cond:
                    text_sources.append(str(cond))

            combined_text = " ".join(text_sources).lower()
            for term in prohibited:
                if term in combined_text:
                    raise ValueError(
                        f"Prohibited term '{term}' found in scheme match text fields without an authoritative approval status."
                    )
        return self
