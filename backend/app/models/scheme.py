from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

from app.schemas.common import SchemeMatchStatus

if TYPE_CHECKING:
    from app.models.analysis import AnalysisRun
    from app.models.finance import FinancialAnalysis
    from app.models.rag import Document, DocumentChunk


class Scheme(SQLModel, table=True):
    __tablename__ = "schemes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    description: str | None = Field(default=None)
    agency_name: str | None = Field(default=None)
    state: str | None = Field(default=None)
    active: bool = Field(default=True)
    official_url: str | None = Field(default=None)
    source: str | None = Field(default=None)
    last_verified_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    rules: list["SchemeRule"] = Relationship(back_populates="scheme")
    eligibility_rules: list["SchemeEligibilityRule"] = Relationship(back_populates="scheme")
    matches: list["SchemeMatch"] = Relationship(back_populates="scheme")
    financial_analyses: list["FinancialAnalysis"] = Relationship(back_populates="scheme")
    document_chunks: list["DocumentChunk"] = Relationship(back_populates="scheme")


class SchemeRule(SQLModel, table=True):
    __tablename__ = "scheme_rules"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scheme_id: UUID = Field(foreign_key="schemes.id", nullable=False)

    min_project_cost: float | None = Field(default=None)
    max_project_cost: float | None = Field(default=None)
    beneficiary_contribution_percent: float | None = Field(default=None)
    loan_percent: float | None = Field(default=None)
    max_loan_amount: float | None = Field(default=None)

    interest_rate: float | None = Field(default=None)
    tenure_months: int | None = Field(default=None)
    moratorium_months: int | None = Field(default=None)
    payment_frequency: str | None = Field(default="monthly")
    moratorium_interest_treatment: str | None = Field(default=None)
    working_capital_percent: float | None = Field(default=None)

    min_age: int | None = Field(default=None)
    max_age: int | None = Field(default=None)
    income_limit: float | None = Field(default=None)

    # JSON conditions
    eligible_business_categories: list[str] | None = Field(default=None, sa_column=Column(JSON))
    eligible_locations: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    eligible_beneficiary_categories: list[str] | None = Field(default=None, sa_column=Column(JSON))
    other_conditions: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    effective_from: date | None = Field(default=None)
    effective_until: date | None = Field(default=None)
    source_document_id: UUID | None = Field(default=None, foreign_key="documents.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    scheme: Scheme = Relationship(back_populates="rules")
    source_document: Optional["Document"] = Relationship(back_populates="scheme_rules")


class SchemeEligibilityRule(SQLModel, table=True):
    __tablename__ = "scheme_eligibility_rules"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    scheme_id: UUID = Field(foreign_key="schemes.id", nullable=False)
    rule_type: str | None = Field(default=None)
    field_name: str | None = Field(default=None)
    operator: str | None = Field(default=None)
    expected_value: Any | None = Field(default=None, sa_column=Column(JSON))
    description: str | None = Field(default=None)
    source_document_id: UUID | None = Field(default=None, foreign_key="documents.id", nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    scheme: Scheme = Relationship(back_populates="eligibility_rules")
    source_document: Optional["Document"] = Relationship(back_populates="scheme_eligibility_rules")


class SchemeMatch(SQLModel, table=True):
    __tablename__ = "scheme_matches"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    analysis_run_id: UUID = Field(foreign_key="analysis_runs.id", nullable=False)
    scheme_id: UUID = Field(foreign_key="schemes.id", nullable=False)

    match_status: SchemeMatchStatus = Field(
        sa_column=Column(
            SQLEnum(SchemeMatchStatus, values_callable=lambda x: [e.value for e in x]),
            nullable=False,
        )
    )
    match_score: float | None = Field(default=None)

    # JSON details
    matched_conditions: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    failed_conditions: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    missing_information: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    estimated_loan_amount: float | None = Field(default=None)
    estimated_project_cost: float | None = Field(default=None)
    verification_required: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    scheme: Scheme = Relationship(back_populates="matches")
    analysis_run: "AnalysisRun" = Relationship(back_populates="scheme_matches")
