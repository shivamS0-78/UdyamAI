from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import Profile


class Debt(SQLModel, table=True):
    __tablename__ = "debts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.id", nullable=False, index=True)
    lender_name: str = Field(nullable=False, description="Name of bank/institution/person")
    loan_type: str = Field(
        nullable=False,
        description="e.g. term_loan, working_capital, credit_card, personal, government_scheme",
    )
    principal_amount: float = Field(nullable=False, ge=0)
    outstanding_amount: float = Field(nullable=False, ge=0)
    interest_rate: float = Field(nullable=False, ge=0, le=100, description="Annual interest rate %")
    emi_amount: float | None = Field(default=None, ge=0)
    tenure_months: int | None = Field(default=None, ge=0)
    start_date: datetime | None = Field(default=None)
    end_date: datetime | None = Field(default=None)
    next_emi_date: datetime | None = Field(default=None)
    status: str = Field(default="active", description="active, paid_off, defaulted, restructured")
    scheme_name: str | None = Field(default=None, description="If linked to a government scheme")
    notes: str | None = Field(default=None)
    deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    profile: "Profile" = Relationship(back_populates="debts")
    payments: list["DebtPayment"] = Relationship(back_populates="debt")


class DebtPayment(SQLModel, table=True):
    __tablename__ = "debt_payments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    debt_id: UUID = Field(foreign_key="debts.id", nullable=False, index=True)
    amount: float = Field(nullable=False, ge=0)
    principal_portion: float = Field(default=0.0, ge=0)
    interest_portion: float = Field(default=0.0, ge=0)
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    payment_mode: str | None = Field(default=None, description="neft, upi, cash, cheque")
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    debt: "Debt" = Relationship(back_populates="payments")
