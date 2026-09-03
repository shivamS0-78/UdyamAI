from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============ EXPENSE SCHEMAS ============
class ExpenseCreate(BaseModel):
    category: str = Field(
        ...,
        description="rent, utilities, inventory, salaries, marketing, transport, raw_materials, other",
    )
    description: str | None = None
    amount: float = Field(..., ge=0)
    date: datetime | None = None
    is_recurring: bool = False
    recurring_frequency: str | None = None
    notes: str | None = None


class ExpenseUpdate(BaseModel):
    category: str | None = None
    description: str | None = None
    amount: float | None = Field(default=None, ge=0)
    date: datetime | None = None
    is_recurring: bool | None = None
    recurring_frequency: str | None = None
    notes: str | None = None


class ExpenseResponse(BaseModel):
    id: UUID
    profile_id: UUID
    category: str
    description: str | None = None
    amount: float
    date: datetime
    is_recurring: bool
    recurring_frequency: str | None = None
    notes: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ExpenseSummary(BaseModel):
    total_expenses: float
    by_category: dict[str, float]
    recurring_total: float
    count: int


# ============ CASH FLOW SCHEMAS ============
class CashFlowEntryCreate(BaseModel):
    entry_type: str = Field(..., description="income or expense")
    category: str = Field(
        ...,
        description="sales, loan_disbursement, rent, salaries, inventory_purchase, utilities, other",
    )
    description: str | None = None
    amount: float = Field(..., ge=0)
    date: datetime | None = None
    notes: str | None = None


class CashFlowEntryResponse(BaseModel):
    id: UUID
    profile_id: UUID
    entry_type: str
    category: str
    description: str | None = None
    amount: float
    date: datetime
    notes: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class CashFlowSummaryResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_income: float
    total_expenses: float
    net_cash_flow: float


class CashFlowOverview(BaseModel):
    total_income: float
    total_expenses: float
    net_cash_flow: float
    entries: list[CashFlowEntryResponse]


# ============ SAVINGS SCHEMAS ============
class SavingsGoalCreate(BaseModel):
    name: str = Field(..., description="e.g. Emergency Fund, Equipment Purchase")
    target_amount: float = Field(..., ge=0)
    target_date: datetime | None = None
    priority: str = Field(default="medium", description="high, medium, low")
    notes: str | None = None


class SavingsGoalUpdate(BaseModel):
    name: str | None = None
    target_amount: float | None = Field(default=None, ge=0)
    target_date: datetime | None = None
    priority: str | None = None
    status: str | None = None
    notes: str | None = None


class SavingsGoalResponse(BaseModel):
    id: UUID
    profile_id: UUID
    name: str
    target_amount: float
    current_amount: float
    target_date: datetime | None = None
    priority: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    progress_percent: float = 0.0
    model_config = {"from_attributes": True}


class SavingsTransactionCreate(BaseModel):
    amount: float = Field(..., ge=0)
    transaction_type: str = Field(..., description="deposit or withdrawal")
    notes: str | None = None


class SavingsTransactionResponse(BaseModel):
    id: UUID
    goal_id: UUID
    amount: float
    transaction_type: str
    date: datetime
    notes: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class SavingsOverview(BaseModel):
    goals: list[SavingsGoalResponse]
    total_saved: float
    total_target: float
    overall_progress: float


# ============ BUDGET SCHEMAS ============
class BudgetItemCreate(BaseModel):
    category: str
    item_type: str = Field(..., description="income or expense")
    planned_amount: float = Field(..., ge=0)
    notes: str | None = None


class BudgetItemResponse(BaseModel):
    id: UUID
    budget_id: UUID
    category: str
    item_type: str
    planned_amount: float
    actual_amount: float
    notes: str | None = None
    variance: float = 0.0
    model_config = {"from_attributes": True}


class BudgetCreate(BaseModel):
    name: str
    period_type: str = Field(default="monthly")
    start_date: datetime
    end_date: datetime
    total_income_target: float = Field(default=0.0, ge=0)
    total_expense_target: float = Field(default=0.0, ge=0)
    items: list[BudgetItemCreate] = Field(default_factory=list)
    notes: str | None = None


class BudgetUpdate(BaseModel):
    name: str | None = None
    period_type: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    total_income_target: float | None = Field(default=None, ge=0)
    total_expense_target: float | None = Field(default=None, ge=0)
    status: str | None = None
    notes: str | None = None


class BudgetResponse(BaseModel):
    id: UUID
    profile_id: UUID
    name: str
    period_type: str
    start_date: datetime
    end_date: datetime
    total_income_target: float
    total_expense_target: float
    total_actual_income: float = 0.0
    total_actual_expenses: float = 0.0
    status: str
    notes: str | None = None
    items: list[BudgetItemResponse] = Field(default_factory=list)
    created_at: datetime
    model_config = {"from_attributes": True}


class BudgetOverview(BaseModel):
    budgets: list[BudgetResponse]
    active_count: int
    total_budgeted_income: float
    total_budgeted_expenses: float


# ============ DEBT SCHEMAS ============
class DebtCreate(BaseModel):
    lender_name: str
    loan_type: str = Field(
        ..., description="term_loan, working_capital, credit_card, personal, government_scheme"
    )
    principal_amount: float = Field(..., ge=0)
    outstanding_amount: float = Field(..., ge=0)
    interest_rate: float = Field(..., ge=0, le=100)
    emi_amount: float | None = Field(default=None, ge=0)
    tenure_months: int | None = Field(default=None, ge=0)
    start_date: datetime | None = None
    end_date: datetime | None = None
    next_emi_date: datetime | None = None
    scheme_name: str | None = None
    notes: str | None = None


class DebtUpdate(BaseModel):
    lender_name: str | None = None
    loan_type: str | None = None
    outstanding_amount: float | None = Field(default=None, ge=0)
    interest_rate: float | None = Field(default=None, ge=0, le=100)
    emi_amount: float | None = Field(default=None, ge=0)
    status: str | None = None
    next_emi_date: datetime | None = None
    notes: str | None = None


class DebtResponse(BaseModel):
    id: UUID
    profile_id: UUID
    lender_name: str
    loan_type: str
    principal_amount: float
    outstanding_amount: float
    interest_rate: float
    emi_amount: float | None = None
    tenure_months: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    next_emi_date: datetime | None = None
    status: str
    scheme_name: str | None = None
    notes: str | None = None
    paid_percent: float = 0.0
    created_at: datetime
    model_config = {"from_attributes": True}


class DebtPaymentCreate(BaseModel):
    amount: float = Field(..., ge=0)
    principal_portion: float = Field(default=0.0, ge=0)
    interest_portion: float = Field(default=0.0, ge=0)
    payment_mode: str | None = None
    notes: str | None = None


class DebtPaymentResponse(BaseModel):
    id: UUID
    debt_id: UUID
    amount: float
    principal_portion: float
    interest_portion: float
    payment_date: datetime
    payment_mode: str | None = None
    notes: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class DebtOverview(BaseModel):
    debts: list[DebtResponse]
    total_outstanding: float
    total_principal: float
    total_monthly_emi: float
    debt_to_income_ratio: float | None = None


# ============ BORROWING ASSISTANCE SCHEMAS ============
class BorrowingCreate(BaseModel):
    lender_name: str
    loan_type: str = Field(..., description="term_loan, working_capital, mudra, pmegp, gold_loan")
    requested_amount: float = Field(..., ge=0)
    approved_amount: float | None = Field(default=None, ge=0)
    interest_rate: float | None = Field(default=None, ge=0, le=100)
    tenure_months: int | None = Field(default=None, ge=0)
    status: str = Field(default="exploring")
    scheme_id: str | None = None
    eligibility_met: bool = True
    documents_required: str | None = None
    notes: str | None = None


class BorrowingUpdate(BaseModel):
    lender_name: str | None = None
    loan_type: str | None = None
    requested_amount: float | None = Field(default=None, ge=0)
    approved_amount: float | None = Field(default=None, ge=0)
    interest_rate: float | None = Field(default=None, ge=0, le=100)
    tenure_months: int | None = Field(default=None, ge=0)
    status: str | None = None
    eligibility_met: bool | None = None
    notes: str | None = None


class BorrowingResponse(BaseModel):
    id: UUID
    profile_id: UUID
    lender_name: str
    loan_type: str
    requested_amount: float
    approved_amount: float | None = None
    interest_rate: float | None = None
    tenure_months: int | None = None
    status: str
    application_date: datetime | None = None
    scheme_id: str | None = None
    eligibility_met: bool
    documents_required: str | None = None
    notes: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class BorrowingOverview(BaseModel):
    borrowings: list[BorrowingResponse]
    exploring_count: int
    applied_count: int
    approved_count: int
    total_requested: float
    total_approved: float


# ============ CREDIT SCORE SCHEMAS ============
class CreditScoreCreate(BaseModel):
    score: int = Field(..., ge=0, le=1000)
    provider: str = Field(default="estimated")
    factors: str | None = None
    rating: str | None = None
    suggestions: str | None = None


class CreditScoreResponse(BaseModel):
    id: UUID
    profile_id: UUID
    score: int
    provider: str
    factors: str | None = None
    rating: str | None = None
    suggestions: str | None = None
    recorded_date: datetime
    created_at: datetime
    model_config = {"from_attributes": True}


class CreditOverview(BaseModel):
    latest_score: CreditScoreResponse | None = None
    history: list[CreditScoreResponse]
    trend: str = Field(default="stable", description="improving, declining, stable")
    rating: str = Field(default="not_rated")
    suggestions: list[str] = Field(default_factory=list)


# ============ RECYCLE BIN SCHEMAS ============
class RecycleBinResponse(BaseModel):
    id: UUID
    item_type: str
    item_id: UUID
    item_data: str
    deleted_at: datetime
    expires_at: datetime | None = None
    restored: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class RecycleBinRestoreRequest(BaseModel):
    item_ids: list[UUID]


# ============ PRIVACY & CONSENT SCHEMAS ============
class PrivacyConsentCreate(BaseModel):
    consent_type: str = Field(
        ..., description="data_sharing, analytics, marketing, ai_processing, third_party_sharing"
    )
    granted: bool


class PrivacyConsentResponse(BaseModel):
    id: UUID
    profile_id: UUID
    consent_type: str
    granted: bool
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
    version: str
    created_at: datetime
    model_config = {"from_attributes": True}


class PrivacyOverview(BaseModel):
    consents: list[PrivacyConsentResponse]
    all_data_shared: bool
    analytics_enabled: bool
    ai_processing_enabled: bool


# ============ SETTINGS SCHEMAS ============
class SettingsUpdate(BaseModel):
    currency: str | None = None
    date_format: str | None = None
    notification_email: bool | None = None
    notification_sms: bool | None = None
    notification_push: bool | None = None
    language: str | None = None
    theme: str | None = None
    default_view: str | None = None
    auto_backup: bool | None = None


class SettingsResponse(BaseModel):
    id: UUID
    profile_id: UUID
    currency: str
    date_format: str
    notification_email: bool
    notification_sms: bool
    notification_push: bool
    language: str
    theme: str
    default_view: str
    auto_backup: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ============ PROFILE MANAGEMENT SCHEMAS ============
class ProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    business_name: str | None = None
    business_type: str | None = None
    preferred_language: str | None = None


class ProfileResponse(BaseModel):
    id: UUID
    auth_user_id: UUID
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    business_name: str | None = None
    business_type: str | None = None
    preferred_language: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
