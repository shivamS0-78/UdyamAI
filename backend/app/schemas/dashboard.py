"""Schemas for the personalised user Dashboard overview."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ExpenseOverview(BaseModel):
    count: int = 0
    total: float = 0.0


class CashFlowOverview(BaseModel):
    count: int = 0
    total_income: float = 0.0
    total_expenses: float = 0.0
    net: float = 0.0


class SavingsOverview(BaseModel):
    goals: int = 0
    total_saved: float = 0.0
    total_target: float = 0.0
    progress_percent: float = 0.0


class BudgetOverview(BaseModel):
    count: int = 0
    active: int = 0
    total_income_target: float = 0.0
    total_expense_target: float = 0.0


class DebtOverview(BaseModel):
    count: int = 0
    total_outstanding: float = 0.0
    total_principal: float = 0.0
    total_monthly_emi: float = 0.0


class BorrowingOverview(BaseModel):
    count: int = 0
    exploring: int = 0
    applied: int = 0
    approved: int = 0
    total_requested: float = 0.0
    total_approved: float = 0.0


class CreditOverview(BaseModel):
    records: int = 0
    latest_score: int | None = None
    latest_rating: str | None = None


class RecycleBinOverview(BaseModel):
    count: int = 0


class FinanceToolsOverview(BaseModel):
    """Per-module summary of the FinCompass tools the user has used."""

    expenses: ExpenseOverview = ExpenseOverview()
    cash_flow: CashFlowOverview = CashFlowOverview()
    savings: SavingsOverview = SavingsOverview()
    budgets: BudgetOverview = BudgetOverview()
    debts: DebtOverview = DebtOverview()
    borrowings: BorrowingOverview = BorrowingOverview()
    credit: CreditOverview = CreditOverview()
    recycle_bin: RecycleBinOverview = RecycleBinOverview()


class AnalysisRunOverview(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    business_category_name: str | None = None
    village_name: str | None = None
    taluka_name: str | None = None
    district_name: str | None = None
    overall_score: float | None = None


class SchemeOverviewItem(BaseModel):
    scheme_id: UUID
    name: str
    agency_name: str | None = None
    match_status: str
    match_score: float | None = None
    estimated_loan_amount: float | None = None
    matched_analysis_run_id: UUID
    analyses_count: int = 1


class ReportOverviewItem(BaseModel):
    id: UUID
    analysis_run_id: UUID
    title: str | None = None
    language: str | None = None
    created_at: datetime


class DashboardOverview(BaseModel):
    analyses: list[AnalysisRunOverview] = []
    schemes: list[SchemeOverviewItem] = []
    reports: list[ReportOverviewItem] = []
    finance: FinanceToolsOverview = FinanceToolsOverview()
