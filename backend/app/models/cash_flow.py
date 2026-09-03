from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import Profile


class CashFlowEntry(SQLModel, table=True):
    __tablename__ = "cash_flow_entries"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    entry_type: str = Field(nullable=False, description="income or expense")
    category: str = Field(
        nullable=False,
        description="e.g. sales, loan_disbursement, rent, salaries, inventory_purchase, utilities",
    )
    description: str | None = Field(default=None)
    amount: float = Field(nullable=False, ge=0)
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = Field(default=None)
    deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="cash_flow_entries")


class CashFlowSummary(SQLModel, table=True):
    """Periodic aggregated cash flow summary"""

    __tablename__ = "cash_flow_summaries"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    period_start: datetime = Field(nullable=False)
    period_end: datetime = Field(nullable=False)
    total_income: float = Field(default=0.0, ge=0)
    total_expenses: float = Field(default=0.0, ge=0)
    net_cash_flow: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="cash_flow_summaries")
