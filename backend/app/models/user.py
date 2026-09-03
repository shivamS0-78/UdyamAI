from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.ai import Conversation
    from app.models.analysis import AnalysisRun
    from app.models.budget import Budget
    from app.models.cash_flow import CashFlowEntry, CashFlowSummary
    from app.models.credit import Borrowing, CreditScore
    from app.models.debt import Debt
    from app.models.expenses import Expense
    from app.models.location import Village
    from app.models.report import Report
    from app.models.savings import SavingsGoal
    from app.models.system import PrivacyConsent, RecycleBinItem, UserSettings


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    auth_user_id: UUID = Field(unique=True, index=True, nullable=False)
    name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    business_name: str | None = Field(default=None)
    business_type: str | None = Field(default=None)
    preferred_language: str | None = Field(default=None)
    location_id: UUID | None = Field(default=None, foreign_key="villages.id", nullable=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    location: Optional["Village"] = Relationship(back_populates="profiles")
    analysis_runs: list["AnalysisRun"] = Relationship(back_populates="profile")
    conversations: list["Conversation"] = Relationship(back_populates="user")
    reports: list["Report"] = Relationship(back_populates="user")
    # Finance feature relationships
    expenses: list["Expense"] = Relationship(back_populates="profile")
    cash_flow_entries: list["CashFlowEntry"] = Relationship(back_populates="profile")
    cash_flow_summaries: list["CashFlowSummary"] = Relationship(back_populates="profile")
    savings_goals: list["SavingsGoal"] = Relationship(back_populates="profile")
    budgets: list["Budget"] = Relationship(back_populates="profile")
    debts: list["Debt"] = Relationship(back_populates="profile")
    borrowings: list["Borrowing"] = Relationship(back_populates="profile")
    credit_scores: list["CreditScore"] = Relationship(back_populates="profile")
    # System feature relationships
    recycle_bin_items: list["RecycleBinItem"] = Relationship(back_populates="profile")
    privacy_consents: list["PrivacyConsent"] = Relationship(back_populates="profile")
    settings: Optional["UserSettings"] = Relationship(back_populates="profile")
