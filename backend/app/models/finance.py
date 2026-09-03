from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.analysis import AnalysisRun
    from app.models.scheme import Scheme


class FinancialAnalysis(SQLModel, table=True):
    __tablename__ = "financial_analyses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    analysis_run_id: UUID = Field(foreign_key="analysis_runs.id", nullable=False)
    scheme_id: UUID | None = Field(default=None, foreign_key="schemes.id", nullable=True)

    available_capital: float | None = Field(default=None)
    required_contribution: float | None = Field(default=None)
    desired_project_cost: float | None = Field(default=None)
    feasible_project_cost: float | None = Field(default=None)

    margin_gap: float | None = Field(default=None)
    calculated_loan: float | None = Field(default=None)
    interest_rate: float | None = Field(default=None)
    tenure_months: int | None = Field(default=None)
    moratorium_months: int | None = Field(default=None)

    monthly_emi: float | None = Field(default=None)
    total_interest: float | None = Field(default=None)
    total_repayment: float | None = Field(default=None)

    working_capital: float | None = Field(default=None)
    monthly_revenue: float | None = Field(default=None)
    monthly_operating_cost: float | None = Field(default=None)
    monthly_profit: float | None = Field(default=None)

    break_even_months: float | None = Field(default=None)
    repayment_capacity: float | None = Field(default=None)
    calculation_version: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    analysis_run: "AnalysisRun" = Relationship(back_populates="financial_analyses")
    scheme: Optional["Scheme"] = Relationship(back_populates="financial_analyses")
    repayment_schedules: list["RepaymentSchedule"] = Relationship(
        back_populates="financial_analysis"
    )
    financial_scenarios: list["FinancialScenario"] = Relationship(
        back_populates="financial_analysis"
    )


class RepaymentSchedule(SQLModel, table=True):
    __tablename__ = "repayment_schedules"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    financial_analysis_id: UUID = Field(foreign_key="financial_analyses.id", nullable=False)

    period_number: int = Field(nullable=False)
    period_start: date | None = Field(default=None)
    period_end: date | None = Field(default=None)

    opening_balance: float | None = Field(default=None)
    principal_amount: float | None = Field(default=None)
    interest_amount: float | None = Field(default=None)
    payment_amount: float | None = Field(default=None)
    remaining_principal: float | None = Field(default=None)
    is_moratorium: bool = Field(default=False)
    verification_required: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    financial_analysis: FinancialAnalysis = Relationship(back_populates="repayment_schedules")


class FinancialScenario(SQLModel, table=True):
    __tablename__ = "financial_scenarios"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    financial_analysis_id: UUID = Field(foreign_key="financial_analyses.id", nullable=False)
    scenario_type: str = Field(nullable=False)  # worst_case, expected_case, best_case

    monthly_revenue: float | None = Field(default=None)
    monthly_expenses: float | None = Field(default=None)
    monthly_profit: float | None = Field(default=None)
    cash_flow: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    repayment_coverage: float | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    financial_analysis: FinancialAnalysis = Relationship(back_populates="financial_scenarios")
