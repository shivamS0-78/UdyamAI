from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import Profile


class SavingsGoal(SQLModel, table=True):
    __tablename__ = "savings_goals"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    name: str = Field(
        nullable=False, description="e.g. Emergency Fund, Equipment Purchase, Working Capital"
    )
    target_amount: float = Field(nullable=False, ge=0)
    current_amount: float = Field(default=0.0, ge=0)
    target_date: datetime | None = Field(default=None)
    priority: str = Field(default="medium", description="high, medium, low")
    status: str = Field(default="active", description="active, completed, paused, cancelled")
    notes: str | None = Field(default=None)
    deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="savings_goals")
    transactions: list["SavingsTransaction"] = Relationship(back_populates="savings_goal")


class SavingsTransaction(SQLModel, table=True):
    __tablename__ = "savings_transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    goal_id: UUID = Field(foreign_key="savings_goals.id", nullable=False, index=True)
    amount: float = Field(nullable=False, ge=0)
    transaction_type: str = Field(nullable=False, description="deposit or withdrawal")
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    savings_goal: "SavingsGoal" = Relationship(back_populates="transactions")
