from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import Profile


class Budget(SQLModel, table=True):
    __tablename__ = "budgets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    name: str = Field(nullable=False, description="e.g. Monthly Budget Q1 2026")
    period_type: str = Field(default="monthly", description="weekly, monthly, quarterly, yearly")
    start_date: datetime = Field(nullable=False)
    end_date: datetime = Field(nullable=False)
    total_income_target: float = Field(default=0.0, ge=0)
    total_expense_target: float = Field(default=0.0, ge=0)
    notes: str | None = Field(default=None)
    status: str = Field(default="active", description="active, completed, archived")
    deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="budgets")
    items: list["BudgetItem"] = Relationship(back_populates="budget")


class BudgetItem(SQLModel, table=True):
    __tablename__ = "budget_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    budget_id: UUID = Field(foreign_key="budgets.id", nullable=False, index=True)
    category: str = Field(nullable=False, description="e.g. rent, salaries, inventory, marketing")
    item_type: str = Field(nullable=False, description="income or expense")
    planned_amount: float = Field(nullable=False, ge=0)
    actual_amount: float = Field(default=0.0, ge=0)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    budget: "Budget" = Relationship(back_populates="items")
