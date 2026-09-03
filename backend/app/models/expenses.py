from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import Profile


class Expense(SQLModel, table=True):
    __tablename__ = "expenses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    category: str = Field(
        nullable=False,
        description="e.g. rent, utilities, inventory, salaries, marketing, transport, other",
    )
    description: str | None = Field(default=None)
    amount: float = Field(nullable=False, ge=0)
    date: datetime = Field(default_factory=datetime.utcnow)
    is_recurring: bool = Field(default=False)
    recurring_frequency: str | None = Field(default=None, description="monthly, weekly, yearly")
    notes: str | None = Field(default=None)
    deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="expenses")
