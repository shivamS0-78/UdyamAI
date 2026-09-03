from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import Profile


class Borrowing(SQLModel, table=True):
    """Tracks borrowing opportunities and applications"""

    __tablename__ = "borrowings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    lender_name: str = Field(nullable=False, description="Bank or institution name")
    loan_type: str = Field(
        nullable=False, description="term_loan, working_capital, mudra, pmegp, gold_loan"
    )
    requested_amount: float = Field(nullable=False, ge=0)
    approved_amount: float | None = Field(default=None, ge=0)
    interest_rate: float | None = Field(default=None, ge=0, le=100)
    tenure_months: int | None = Field(default=None, ge=0)
    status: str = Field(
        default="exploring",
        description="exploring, applied, under_review, approved, disbursed, rejected",
    )
    application_date: datetime | None = Field(default=None)
    scheme_id: str | None = Field(default=None, description="If linked to a government scheme")
    eligibility_met: bool = Field(default=True)
    documents_required: str | None = Field(
        default=None, description="Comma-separated list of required documents"
    )
    notes: str | None = Field(default=None)
    deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="borrowings")


class CreditScore(SQLModel, table=True):
    """Business credit monitoring record"""

    __tablename__ = "credit_scores"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    score: int = Field(nullable=False, ge=0, le=1000, description="Credit score 0-1000")
    provider: str = Field(
        default="estimated", description="estimated, cibil, equifax, crif, experian"
    )
    factors: str | None = Field(default=None, description="JSON string of factors affecting score")
    rating: str | None = Field(default=None, description="poor, fair, good, very_good, excellent")
    suggestions: str | None = Field(
        default=None, description="JSON string of improvement suggestions"
    )
    recorded_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="credit_scores")
