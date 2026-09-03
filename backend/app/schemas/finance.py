from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScenarioMultiplierInput(BaseModel):
    revenue_multiplier: float = Field(
        ..., ge=0.0, le=5.0, description="Multiplier for baseline revenue (e.g. 0.8 for 80%)"
    )
    operating_cost_multiplier: float = Field(
        ...,
        ge=0.0,
        le=5.0,
        description="Multiplier for baseline operating cost (e.g. 1.1 for 110%)",
    )


class ScenarioConfigInput(BaseModel):
    worst_case: ScenarioMultiplierInput = Field(
        default_factory=lambda: ScenarioMultiplierInput(
            revenue_multiplier=0.80, operating_cost_multiplier=1.10
        )
    )
    expected_case: ScenarioMultiplierInput = Field(
        default_factory=lambda: ScenarioMultiplierInput(
            revenue_multiplier=1.00, operating_cost_multiplier=1.00
        )
    )
    best_case: ScenarioMultiplierInput = Field(
        default_factory=lambda: ScenarioMultiplierInput(
            revenue_multiplier=1.20, operating_cost_multiplier=0.90
        )
    )


class SchemeRuleInput(BaseModel):
    beneficiary_contribution_percent: float = Field(
        ...,
        gt=0.0,
        le=100.0,
        description="Beneficiary contribution percentage required by scheme (e.g. 10.0 for 10%)",
    )
    loan_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Percentage of project cost funded by loan. If None, derived as (100 - beneficiary_contribution_percent)",
    )
    min_project_cost: float | None = Field(
        default=None, ge=0.0, description="Minimum project cost allowed under the scheme in INR"
    )
    max_project_cost: float | None = Field(
        default=None, ge=0.0, description="Maximum project cost allowed under the scheme in INR"
    )
    max_loan_amount: float | None = Field(
        default=None, ge=0.0, description="Maximum loan cap under the scheme in INR"
    )
    interest_rate: float = Field(
        ..., ge=0.0, le=100.0, description="Annual interest rate percentage (0-100%)"
    )
    tenure_months: int = Field(
        ..., gt=0, le=360, description="Repayment period in months (1 to 360 months)"
    )
    moratorium_months: int | None = Field(
        default=0, ge=0, le=60, description="Moratorium period in months (0 to 60 months)"
    )
    payment_frequency: str | None = Field(
        default="monthly",
        description="Payment frequency: 'monthly', 'quarterly', 'semi_annually', 'annually'",
    )
    moratorium_interest_treatment: str | None = Field(
        default=None,
        description="Treatment of interest during moratorium: 'interest_only', 'capitalized', 'waived', or None (requires verification)",
    )
    working_capital_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Percentage of project cost supported as working capital",
    )


class FinanceCalculateRequest(BaseModel):
    """
    Request schema for Finance Engine calculation endpoint.

    API Note (V2 Evolution):
    - available_capital is required (investor equity).
    - desired_project_cost is optional. If provided, calculates required contribution and potential shortfall for that target.
      If omitted, computes maximum feasible project cost and loan supportable by available_capital.
    - Scheme rules can be loaded from DB via scheme_id / scheme_rule_id or supplied directly via scheme_rule_override.
    """

    available_capital: float = Field(
        ...,
        ge=0,
        le=100_000_000.0,
        description="Available capital / equity investment in INR (required)",
    )
    desired_project_cost: float | None = Field(
        default=None,
        gt=0,
        le=100_000_000.0,
        description="Optional desired total project cost in INR",
    )
    scheme_id: UUID | None = Field(
        default=None, description="Optional DB Scheme ID to fetch applicable scheme rules"
    )
    scheme_rule_id: UUID | None = Field(
        default=None, description="Optional DB SchemeRule ID to fetch specific rule version"
    )
    scheme_rule_override: SchemeRuleInput | None = Field(
        default=None, description="Direct scheme rule specification when scheme_id is not provided"
    )
    # Direct fallback fields for backward compatibility when scheme_rule_override is omitted
    interest_rate: float | None = Field(default=None, ge=0.0, le=100.0)
    tenure_months: int | None = Field(default=None, gt=0, le=360)
    moratorium_months: int | None = Field(default=0, ge=0, le=60)
    loan_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    beneficiary_contribution_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    payment_frequency: str | None = Field(default=None)
    moratorium_interest_treatment: str | None = Field(default=None)

    # Financial performance inputs for scenario generation
    monthly_revenue: float | None = Field(default=None, ge=0.0)
    monthly_operating_cost: float | None = Field(default=None, ge=0.0)
    verified_revenue: float | None = Field(
        default=None, ge=0.0, description="Verified benchmark monthly revenue"
    )
    verified_operating_cost: float | None = Field(
        default=None, ge=0.0, description="Verified benchmark monthly operating cost"
    )
    scenario_config: ScenarioConfigInput | None = Field(
        default=None, description="Configurable scenario multipliers"
    )
    analysis_run_id: UUID | None = Field(
        default=None, description="Optional AnalysisRun ID for DB persistence"
    )


class RepaymentScheduleItemResponse(BaseModel):
    period_number: int = Field(..., gt=0, description="Period number (1-based index)")
    opening_balance: float = Field(..., ge=0, description="Opening balance before payment")
    payment_amount: float = Field(..., ge=0, description="Total payment amount for period")
    principal_amount: float = Field(..., ge=0, description="Principal paid in this period")
    interest_amount: float = Field(..., ge=0, description="Interest paid in this period")
    closing_balance: float = Field(..., ge=0, description="Closing balance after payment")
    remaining_principal: float = Field(
        ..., ge=0, description="Remaining loan principal after payment"
    )
    is_moratorium: bool = Field(..., description="Whether this period falls in moratorium")
    verification_required: bool = Field(
        default=False, description="Whether moratorium interest treatment requires verification"
    )


class FinancialScenarioResponse(BaseModel):
    scenario_type: str = Field(..., description="worst_case, expected_case, or best_case")
    sufficient_assumptions_exist: bool = Field(
        default=True, description="Whether sufficient data/assumptions exist to calculate scenario"
    )
    revenue: float | None = Field(
        default=None, ge=0.0, description="Monthly revenue under scenario"
    )
    operating_costs: float | None = Field(
        default=None, ge=0.0, description="Monthly operating costs under scenario"
    )
    surplus: float | None = Field(
        default=None, description="Monthly operating surplus (revenue - operating_costs)"
    )
    loan_repayment: float | None = Field(
        default=None, ge=0.0, description="Monthly loan repayment / EMI"
    )
    cash_surplus: float | None = Field(
        default=None, description="Net monthly cash surplus (surplus - loan_repayment)"
    )

    # Legacy fields maintained for backward compatibility
    monthly_revenue: float | None = Field(default=None, ge=0.0)
    monthly_expenses: float | None = Field(default=None, ge=0.0)
    monthly_profit: float | None = Field(default=None)
    repayment_coverage: float | None = Field(
        default=None, description="Debt Service Coverage Ratio (Surplus / Loan Repayment)"
    )
    data_source: str | None = Field(
        default=None,
        description="'verified_data', 'explicit_user_assumptions', or 'configurable_assumptions'",
    )
    marked_assumptions: dict[str, Any] | None = Field(
        default=None, description="Clearly marked assumptions and source transparency metadata"
    )
    cash_flow: dict[str, Any] | None = None


class FinanceCalculateResponse(BaseModel):
    status: str = Field(
        default="success",
        description="Calculation status: 'success', 'insufficient_margin', or 'below_minimum_cost'",
    )
    available_capital: float = Field(..., ge=0)
    required_contribution: float = Field(..., ge=0)
    shortfall: float = Field(
        default=0.0,
        ge=0.0,
        description="Margin shortfall if available_capital < required_contribution",
    )
    desired_project_cost: float | None = Field(default=None, ge=0)
    feasible_project_cost: float | None = Field(default=None, ge=0)
    potential_loan: float | None = Field(default=None, ge=0)

    # Caps applied flags & limits
    project_cost_cap_applied: bool = Field(default=False)
    loan_cap_applied: bool = Field(default=False)
    max_project_cost_limit: float | None = Field(default=None)
    max_loan_amount_limit: float | None = Field(default=None)

    # Scheme parameters applied
    beneficiary_contribution_percent: float | None = Field(default=None)
    loan_percent: float | None = Field(default=None)
    interest_rate: float | None = Field(default=None)
    tenure_months: int | None = Field(default=None)
    moratorium_months: int | None = Field(default=None)
    payment_frequency: str | None = Field(default="monthly")
    moratorium_interest_treatment: str | None = Field(default=None)
    verification_required: bool = Field(default=False)

    # Repayment outputs
    monthly_emi: float | None = Field(default=None, ge=0)
    total_interest: float | None = Field(default=None, ge=0)
    total_repayment: float | None = Field(default=None, ge=0)
    working_capital: float | None = Field(default=None, ge=0)

    # Schedule & Scenarios
    repayment_schedule: list[RepaymentScheduleItemResponse] = Field(default_factory=list)
    financial_scenarios: list[FinancialScenarioResponse] = Field(default_factory=list)
    message: str | None = Field(default=None)
