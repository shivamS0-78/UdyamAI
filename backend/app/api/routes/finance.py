"""FinCompass Finance Feature Routes - Expenses, Cash Flow, Savings, Budget, Debt, Borrowing, Credit.

All routes require a valid Supabase session (``get_current_profile``).
Identity always comes from the verified session token — client-supplied
``profile_id`` values are ignored, so users can only read/write their own
profile's data.
"""

import json
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import get_current_profile
from app.database import get_session
from app.models.budget import Budget, BudgetItem
from app.models.cash_flow import CashFlowEntry, CashFlowSummary
from app.models.credit import Borrowing, CreditScore
from app.models.debt import Debt, DebtPayment
from app.models.expenses import Expense
from app.models.savings import SavingsGoal, SavingsTransaction
from app.models.system import PrivacyConsent, RecycleBinItem, UserSettings
from app.models.user import Profile
from app.schemas.expenses import (
    BorrowingCreate,
    BorrowingOverview,
    BorrowingResponse,
    BorrowingUpdate,
    BudgetCreate,
    BudgetItemResponse,
    BudgetOverview,
    BudgetResponse,
    BudgetUpdate,
    CashFlowEntryCreate,
    CashFlowEntryResponse,
    CashFlowOverview,
    CashFlowSummaryResponse,
    CreditOverview,
    CreditScoreCreate,
    CreditScoreResponse,
    DebtCreate,
    DebtOverview,
    DebtPaymentCreate,
    DebtPaymentResponse,
    DebtResponse,
    DebtUpdate,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseUpdate,
    PrivacyConsentCreate,
    PrivacyConsentResponse,
    PrivacyOverview,
    ProfileResponse,
    ProfileUpdate,
    RecycleBinResponse,
    RecycleBinRestoreRequest,
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
    SavingsOverview,
    SavingsTransactionCreate,
    SavingsTransactionResponse,
    SettingsResponse,
    SettingsUpdate,
)
from app.schemas.finance import FinanceCalculateRequest, FinanceCalculateResponse
from app.services.finance_service import FinanceService

router = APIRouter()


@router.post("/calculate", response_model=FinanceCalculateResponse)
def calculate_finance(request: FinanceCalculateRequest, session: Session = Depends(get_session)):
    return FinanceService.calculate_finance(request, session=session)


def _owned_or_404(session: Session, model: type, entity_id: UUID, profile: Profile, label: str):
    """Fetch a profile-owned entity, rejecting missing or foreign rows."""
    obj = session.get(model, entity_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    owner_id = getattr(obj, "profile_id", None)
    if owner_id is not None and owner_id != profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    return obj


# ============================================================
# EXPENSES
# ============================================================


@router.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    category: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    q = select(Expense).where(Expense.profile_id == profile.id, ~Expense.deleted)
    if category:
        q = q.where(Expense.category == category)
    if start_date:
        q = q.where(Expense.date >= start_date)
    if end_date:
        q = q.where(Expense.date <= end_date)
    q = q.order_by(Expense.date.desc())
    return session.exec(q).all()


@router.post("/expenses", response_model=ExpenseResponse)
def create_expense(
    data: ExpenseCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    expense = Expense(profile_id=profile.id, **data.model_dump(exclude_unset=True))
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@router.get("/expenses/summary", response_model=ExpenseSummary)
def get_expense_summary(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    q = select(Expense).where(Expense.profile_id == profile.id, ~Expense.deleted)
    if start_date:
        q = q.where(Expense.date >= start_date)
    if end_date:
        q = q.where(Expense.date <= end_date)
    expenses = session.exec(q).all()
    total = sum(e.amount for e in expenses)
    by_cat: dict[str, float] = {}
    recurring = 0.0
    for e in expenses:
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
        if e.is_recurring:
            recurring += e.amount
    return ExpenseSummary(
        total_expenses=total, by_category=by_cat, recurring_total=recurring, count=len(expenses)
    )


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: UUID,
    data: ExpenseUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    expense = _owned_or_404(session, Expense, expense_id, profile, "Expense")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(expense, k, v)
    expense.updated_at = datetime.utcnow()
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: UUID,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    expense = _owned_or_404(session, Expense, expense_id, profile, "Expense")
    # Move to recycle bin
    item = RecycleBinItem(
        profile_id=profile.id,
        item_type="expense",
        item_id=expense.id,
        item_data=json.dumps(
            {
                "category": expense.category,
                "description": expense.description,
                "amount": expense.amount,
                "date": str(expense.date),
                "is_recurring": expense.is_recurring,
                "notes": expense.notes,
            }
        ),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    session.add(item)
    expense.deleted = True
    session.add(expense)
    session.commit()
    return {"status": "deleted"}


# ============================================================
# CASH FLOW
# ============================================================


@router.get("/cashflow", response_model=CashFlowOverview)
def get_cashflow_overview(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    q = select(CashFlowEntry).where(CashFlowEntry.profile_id == profile.id, ~CashFlowEntry.deleted)
    if start_date:
        q = q.where(CashFlowEntry.date >= start_date)
    if end_date:
        q = q.where(CashFlowEntry.date <= end_date)
    q = q.order_by(CashFlowEntry.date.desc())
    entries = session.exec(q).all()
    total_income = sum(e.amount for e in entries if e.entry_type == "income")
    total_expenses = sum(e.amount for e in entries if e.entry_type == "expense")
    return CashFlowOverview(
        total_income=total_income,
        total_expenses=total_expenses,
        net_cash_flow=total_income - total_expenses,
        entries=[CashFlowEntryResponse.model_validate(e) for e in entries],
    )


@router.post("/cashflow", response_model=CashFlowEntryResponse)
def create_cashflow_entry(
    data: CashFlowEntryCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    entry = CashFlowEntry(profile_id=profile.id, **data.model_dump(exclude_unset=True))
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/cashflow/summaries", response_model=list[CashFlowSummaryResponse])
def get_cashflow_summaries(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    q = (
        select(CashFlowSummary)
        .where(CashFlowSummary.profile_id == profile.id)
        .order_by(CashFlowSummary.period_start.desc())
    )
    return session.exec(q).all()


@router.delete("/cashflow/{entry_id}")
def delete_cashflow_entry(
    entry_id: UUID,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    entry = _owned_or_404(session, CashFlowEntry, entry_id, profile, "Cash flow entry")
    entry.deleted = True
    session.add(entry)
    session.commit()
    return {"status": "deleted"}


# ============================================================
# SAVINGS
# ============================================================


@router.get("/savings", response_model=SavingsOverview)
def get_savings_overview(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    q = select(SavingsGoal).where(SavingsGoal.profile_id == profile.id, ~SavingsGoal.deleted)
    goals = session.exec(q).all()
    goals_resp = []
    total_saved = 0.0
    total_target = 0.0
    for g in goals:
        progress = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
        resp = SavingsGoalResponse.model_validate(g)
        resp.progress_percent = round(progress, 1)
        goals_resp.append(resp)
        total_saved += g.current_amount
        total_target += g.target_amount
    overall = (total_saved / total_target * 100) if total_target > 0 else 0
    return SavingsOverview(
        goals=goals_resp,
        total_saved=total_saved,
        total_target=total_target,
        overall_progress=round(overall, 1),
    )


@router.post("/savings/goals", response_model=SavingsGoalResponse)
def create_savings_goal(
    data: SavingsGoalCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    goal = SavingsGoal(profile_id=profile.id, **data.model_dump(exclude_unset=True))
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@router.put("/savings/goals/{goal_id}", response_model=SavingsGoalResponse)
def update_savings_goal(
    goal_id: UUID,
    data: SavingsGoalUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    goal = _owned_or_404(session, SavingsGoal, goal_id, profile, "Savings goal")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(goal, k, v)
    goal.updated_at = datetime.utcnow()
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@router.post("/savings/goals/{goal_id}/transactions", response_model=SavingsTransactionResponse)
def create_savings_transaction(
    goal_id: UUID,
    data: SavingsTransactionCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    goal = _owned_or_404(session, SavingsGoal, goal_id, profile, "Savings goal")
    if data.transaction_type == "deposit":
        goal.current_amount += data.amount
    elif data.transaction_type == "withdrawal":
        if data.amount > goal.current_amount:
            raise HTTPException(status_code=400, detail="Withdrawal exceeds available amount")
        goal.current_amount -= data.amount
    goal.updated_at = datetime.utcnow()
    session.add(goal)
    txn = SavingsTransaction(
        goal_id=goal_id,
        amount=data.amount,
        transaction_type=data.transaction_type,
        notes=data.notes,
    )
    session.add(txn)
    session.commit()
    session.refresh(txn)
    return txn


@router.get(
    "/savings/goals/{goal_id}/transactions", response_model=list[SavingsTransactionResponse]
)
def list_savings_transactions(
    goal_id: UUID,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    _owned_or_404(session, SavingsGoal, goal_id, profile, "Savings goal")
    return session.exec(
        select(SavingsTransaction)
        .where(SavingsTransaction.goal_id == goal_id)
        .order_by(SavingsTransaction.date.desc())
    ).all()


# ============================================================
# BUDGET & PLANNING
# ============================================================


@router.get("/budgets", response_model=BudgetOverview)
def list_budgets(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    q = (
        select(Budget)
        .where(Budget.profile_id == profile.id, ~Budget.deleted)
        .order_by(Budget.created_at.desc())
    )
    budgets = session.exec(q).all()
    budgets_resp = []
    total_inc = 0.0
    total_exp = 0.0
    active = 0
    for b in budgets:
        items = session.exec(select(BudgetItem).where(BudgetItem.budget_id == b.id)).all()
        items_resp = []
        for it in items:
            ir = BudgetItemResponse.model_validate(it)
            ir.variance = it.planned_amount - it.actual_amount
            items_resp.append(ir)
        br = BudgetResponse.model_validate(b)
        br.items = items_resp
        br.total_actual_income = sum(it.actual_amount for it in items if it.item_type == "income")
        br.total_actual_expenses = sum(
            it.actual_amount for it in items if it.item_type == "expense"
        )
        budgets_resp.append(br)
        total_inc += b.total_income_target
        total_exp += b.total_expense_target
        if b.status == "active":
            active += 1
    return BudgetOverview(
        budgets=budgets_resp,
        active_count=active,
        total_budgeted_income=total_inc,
        total_budgeted_expenses=total_exp,
    )


@router.post("/budgets", response_model=BudgetResponse)
def create_budget(
    data: BudgetCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    budget = Budget(
        profile_id=profile.id,
        name=data.name,
        period_type=data.period_type,
        start_date=data.start_date,
        end_date=data.end_date,
        total_income_target=data.total_income_target,
        total_expense_target=data.total_expense_target,
        notes=data.notes,
    )
    session.add(budget)
    session.flush()
    for item_data in data.items:
        bi = BudgetItem(budget_id=budget.id, **item_data.model_dump())
        session.add(bi)
    session.commit()
    session.refresh(budget)
    items = session.exec(select(BudgetItem).where(BudgetItem.budget_id == budget.id)).all()
    br = BudgetResponse.model_validate(budget)
    br.items = [BudgetItemResponse.model_validate(it) for it in items]
    return br


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    budget = _owned_or_404(session, Budget, budget_id, profile, "Budget")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(budget, k, v)
    budget.updated_at = datetime.utcnow()
    session.add(budget)
    session.commit()
    session.refresh(budget)
    items = session.exec(select(BudgetItem).where(BudgetItem.budget_id == budget.id)).all()
    br = BudgetResponse.model_validate(budget)
    br.items = [BudgetItemResponse.model_validate(it) for it in items]
    return br


@router.delete("/budgets/{budget_id}")
def delete_budget(
    budget_id: UUID,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    budget = _owned_or_404(session, Budget, budget_id, profile, "Budget")
    budget.deleted = True
    session.add(budget)
    session.commit()
    return {"status": "deleted"}


# ============================================================
# DEBT TRACKING
# ============================================================


@router.get("/debts", response_model=DebtOverview)
def list_debts(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    q = select(Debt).where(Debt.profile_id == profile.id, ~Debt.deleted)
    debts = session.exec(q).all()
    debts_resp = []
    total_outstanding = 0.0
    total_principal = 0.0
    total_emi = 0.0
    for d in debts:
        paid_pct = (
            ((d.principal_amount - d.outstanding_amount) / d.principal_amount * 100)
            if d.principal_amount > 0
            else 0
        )
        dr = DebtResponse.model_validate(d)
        dr.paid_percent = round(paid_pct, 1)
        debts_resp.append(dr)
        total_outstanding += d.outstanding_amount
        total_principal += d.principal_amount
        total_emi += d.emi_amount or 0
    return DebtOverview(
        debts=debts_resp,
        total_outstanding=total_outstanding,
        total_principal=total_principal,
        total_monthly_emi=total_emi,
    )


@router.post("/debts", response_model=DebtResponse)
def create_debt(
    data: DebtCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    debt = Debt(profile_id=profile.id, **data.model_dump(exclude_unset=True))
    session.add(debt)
    session.commit()
    session.refresh(debt)
    return debt


@router.put("/debts/{debt_id}", response_model=DebtResponse)
def update_debt(
    debt_id: UUID,
    data: DebtUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    debt = _owned_or_404(session, Debt, debt_id, profile, "Debt")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(debt, k, v)
    debt.updated_at = datetime.utcnow()
    session.add(debt)
    session.commit()
    session.refresh(debt)
    return debt


@router.post("/debts/{debt_id}/payments", response_model=DebtPaymentResponse)
def create_debt_payment(
    debt_id: UUID,
    data: DebtPaymentCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    debt = _owned_or_404(session, Debt, debt_id, profile, "Debt")
    debt.outstanding_amount = max(0, debt.outstanding_amount - data.principal_portion)
    if debt.outstanding_amount <= 0:
        debt.status = "paid_off"
    session.add(debt)
    payment = DebtPayment(debt_id=debt_id, **data.model_dump())
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


@router.get("/debts/{debt_id}/payments", response_model=list[DebtPaymentResponse])
def list_debt_payments(
    debt_id: UUID,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    _owned_or_404(session, Debt, debt_id, profile, "Debt")
    return session.exec(
        select(DebtPayment)
        .where(DebtPayment.debt_id == debt_id)
        .order_by(DebtPayment.payment_date.desc())
    ).all()


# ============================================================
# BORROWING ASSISTANCE
# ============================================================


@router.get("/borrowings", response_model=BorrowingOverview)
def list_borrowings(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    q = select(Borrowing).where(Borrowing.profile_id == profile.id, ~Borrowing.deleted)
    items = session.exec(q).all()
    items_resp = [BorrowingResponse.model_validate(b) for b in items]
    exploring = sum(1 for b in items if b.status == "exploring")
    applied = sum(1 for b in items if b.status in ("applied", "under_review"))
    approved = sum(1 for b in items if b.status in ("approved", "disbursed"))
    total_req = sum(b.requested_amount for b in items)
    total_appr = sum(b.approved_amount or 0 for b in items)
    return BorrowingOverview(
        borrowings=items_resp,
        exploring_count=exploring,
        applied_count=applied,
        approved_count=approved,
        total_requested=total_req,
        total_approved=total_appr,
    )


@router.post("/borrowings", response_model=BorrowingResponse)
def create_borrowing(
    data: BorrowingCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    borrowing = Borrowing(profile_id=profile.id, **data.model_dump(exclude_unset=True))
    session.add(borrowing)
    session.commit()
    session.refresh(borrowing)
    return borrowing


@router.put("/borrowings/{borrowing_id}", response_model=BorrowingResponse)
def update_borrowing(
    borrowing_id: UUID,
    data: BorrowingUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    borrowing = _owned_or_404(session, Borrowing, borrowing_id, profile, "Borrowing")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(borrowing, k, v)
    borrowing.updated_at = datetime.utcnow()
    session.add(borrowing)
    session.commit()
    session.refresh(borrowing)
    return borrowing


@router.delete("/borrowings/{borrowing_id}")
def delete_borrowing(
    borrowing_id: UUID,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    borrowing = _owned_or_404(session, Borrowing, borrowing_id, profile, "Borrowing")
    borrowing.deleted = True
    session.add(borrowing)
    session.commit()
    return {"status": "deleted"}


# ============================================================
# CREDIT SCORE MONITORING
# ============================================================


@router.get("/credit", response_model=CreditOverview)
def get_credit_overview(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    q = (
        select(CreditScore)
        .where(CreditScore.profile_id == profile.id)
        .order_by(CreditScore.recorded_date.desc())
    )
    scores = session.exec(q).all()
    history = [CreditScoreResponse.model_validate(s) for s in scores]
    latest = history[0] if history else None
    trend = "stable"
    if len(scores) >= 2:
        diff = scores[0].score - scores[1].score
        trend = "improving" if diff > 0 else "declining" if diff < 0 else "stable"
    rating = "not_rated"
    suggestions_list: list[str] = []
    if latest:
        rating = latest.rating or "not_rated"
        if latest.suggestions:
            try:
                suggestions_list = (
                    json.loads(latest.suggestions)
                    if isinstance(latest.suggestions, str)
                    else latest.suggestions
                )
            except Exception:
                suggestions_list = [latest.suggestions]
    return CreditOverview(
        latest_score=latest,
        history=history,
        trend=trend,
        rating=rating,
        suggestions=suggestions_list,
    )


@router.post("/credit", response_model=CreditScoreResponse)
def create_credit_score(
    data: CreditScoreCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    # Auto-assign rating based on score
    score = data.score
    if score >= 800:
        rating = "excellent"
    elif score >= 700:
        rating = "very_good"
    elif score >= 600:
        rating = "good"
    elif score >= 500:
        rating = "fair"
    else:
        rating = "poor"
    credit = CreditScore(
        profile_id=profile.id, rating=rating, **data.model_dump(exclude_unset=True)
    )
    session.add(credit)
    session.commit()
    session.refresh(credit)
    return credit


# ============================================================
# RECYCLE BIN
# ============================================================


@router.get("/recycle-bin", response_model=list[RecycleBinResponse])
def list_recycle_bin(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    q = (
        select(RecycleBinItem)
        .where(RecycleBinItem.profile_id == profile.id, ~RecycleBinItem.restored)
        .order_by(RecycleBinItem.deleted_at.desc())
    )
    return session.exec(q).all()


@router.post("/recycle-bin/restore")
def restore_from_recycle_bin(
    data: RecycleBinRestoreRequest,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    restored_count = 0
    for item_id in data.item_ids:
        item = session.get(RecycleBinItem, item_id)
        if item is None or item.profile_id != profile.id:
            continue  # ignore foreign recycle-bin rows
        if not item.restored:
            item.restored = True
            session.add(item)
            # Mark original as not deleted
            if item.item_type == "expense":
                expense = session.get(Expense, item.item_id)
                if expense:
                    expense.deleted = False
                    session.add(expense)
            restored_count += 1
    session.commit()
    return {"restored_count": restored_count}


@router.delete("/recycle-bin/{item_id}")
def permanent_delete_recycle_bin(
    item_id: UUID,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    item = _owned_or_404(session, RecycleBinItem, item_id, profile, "Recycle bin item")
    session.delete(item)
    session.commit()
    return {"status": "permanently_deleted"}


# ============================================================
# PRIVACY & CONSENT
# ============================================================


@router.get("/privacy", response_model=PrivacyOverview)
def get_privacy_overview(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    q = select(PrivacyConsent).where(PrivacyConsent.profile_id == profile.id)
    consents = session.exec(q).all()
    consents_resp = [PrivacyConsentResponse.model_validate(c) for c in consents]
    data_shared = any(c.granted and c.consent_type == "data_sharing" for c in consents)
    analytics = any(c.granted and c.consent_type == "analytics" for c in consents)
    ai_proc = any(c.granted and c.consent_type == "ai_processing" for c in consents)
    return PrivacyOverview(
        consents=consents_resp,
        all_data_shared=data_shared,
        analytics_enabled=analytics,
        ai_processing_enabled=ai_proc,
    )


@router.post("/privacy", response_model=PrivacyConsentResponse)
def update_privacy_consent(
    data: PrivacyConsentCreate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    # Find existing consent or create new
    existing = session.exec(
        select(PrivacyConsent).where(
            PrivacyConsent.profile_id == profile.id,
            PrivacyConsent.consent_type == data.consent_type,
        )
    ).first()
    if existing:
        existing.granted = data.granted
        if data.granted:
            existing.granted_at = datetime.utcnow()
            existing.revoked_at = None
        else:
            existing.revoked_at = datetime.utcnow()
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    consent = PrivacyConsent(
        profile_id=profile.id,
        consent_type=data.consent_type,
        granted=data.granted,
        granted_at=datetime.utcnow() if data.granted else None,
    )
    session.add(consent)
    session.commit()
    session.refresh(consent)
    return consent


# ============================================================
# SETTINGS
# ============================================================


@router.get("/settings", response_model=SettingsResponse)
def get_settings(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    settings = session.exec(
        select(UserSettings).where(UserSettings.profile_id == profile.id)
    ).first()
    if not settings:
        settings = UserSettings(profile_id=profile.id)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.put("/settings", response_model=SettingsResponse)
def update_settings(
    data: SettingsUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    settings = session.exec(
        select(UserSettings).where(UserSettings.profile_id == profile.id)
    ).first()
    if not settings:
        settings = UserSettings(profile_id=profile.id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(settings, k, v)
    settings.updated_at = datetime.utcnow()
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


# ============================================================
# PROFILE MANAGEMENT
# ============================================================


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    profile: Profile = Depends(get_current_profile), session: Session = Depends(get_session)
):
    return profile


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    data: ProfileUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.post("/profile", response_model=ProfileResponse)
def create_profile(
    data: ProfileUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
):
    """Upsert the authenticated user's profile.

    The profile row is resolved from the Supabase session (a database
    trigger creates it at signup; the dependency also creates it lazily),
    so clients never supply a ``profile_id``.
    """
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
