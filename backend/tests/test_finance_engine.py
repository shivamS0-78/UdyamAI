"""
Unit tests for UdyamAI Phase 5 Finance Engine logic & services.
"""

from uuid import uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.models.analysis import AnalysisRun
from app.models.finance import FinancialAnalysis, FinancialScenario, RepaymentSchedule
from app.models.scheme import Scheme, SchemeRule
from app.models.user import Profile
from app.schemas.finance import FinanceCalculateRequest, SchemeRuleInput
from app.services.finance_service import FinanceService


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    tables = [
        Profile.__table__,
        AnalysisRun.__table__,
        Scheme.__table__,
        SchemeRule.__table__,
        FinancialAnalysis.__table__,
        RepaymentSchedule.__table__,
        FinancialScenario.__table__,
    ]
    SQLModel.metadata.create_all(engine, tables=tables)
    with Session(engine) as session:
        yield session


def test_finance_engine_prompt_example():
    """
    Test exact prompt example:
    Available capital = ₹1,00,000
    Required contribution = 10%
    Raw project cost = ₹1,00,000 / 0.10 = ₹10,00,000
    Raw loan = ₹10,00,000 × 0.90 = ₹9,00,000
    """
    rule = SchemeRuleInput(
        beneficiary_contribution_percent=10.0,
        loan_percent=90.0,
        interest_rate=8.5,
        tenure_months=84,
        moratorium_months=6,
        moratorium_interest_treatment="interest_only",
    )
    req = FinanceCalculateRequest(
        available_capital=100000.0,
        scheme_rule_override=rule,
    )
    res = FinanceService.calculate_finance(req)

    assert res.status == "success"
    assert res.available_capital == pytest.approx(100000.0)
    assert res.feasible_project_cost == pytest.approx(1000000.0)
    assert res.potential_loan == pytest.approx(900000.0)
    assert res.required_contribution == pytest.approx(100000.0)
    assert res.shortfall == pytest.approx(0.0)
    assert len(res.repayment_schedule) == 84

    # First 6 months are moratorium
    for item in res.repayment_schedule[:6]:
        assert item.is_moratorium is True
        assert item.principal_amount == pytest.approx(0.0)
        assert item.opening_balance == pytest.approx(900000.0)
        assert item.closing_balance == pytest.approx(900000.0)

    # Subsequent months repayment begins
    for item in res.repayment_schedule[6:]:
        assert item.is_moratorium is False


def test_finance_engine_quarterly_frequency_and_capitalized_moratorium():
    """Test quarterly payment frequency and capitalized moratorium interest treatment."""
    rule = SchemeRuleInput(
        beneficiary_contribution_percent=10.0,
        loan_percent=90.0,
        interest_rate=12.0,  # 12% per year -> 3% per quarter
        tenure_months=24,  # 8 quarters total
        moratorium_months=6,  # 2 quarters moratorium
        payment_frequency="quarterly",
        moratorium_interest_treatment="capitalized",
    )
    req = FinanceCalculateRequest(
        available_capital=100000.0,
        scheme_rule_override=rule,
    )
    res = FinanceService.calculate_finance(req)

    assert res.status == "success"
    assert res.payment_frequency == "quarterly"
    assert len(res.repayment_schedule) == 8

    # Quarter 1: opening 900,000, interest 3% = 27,000, capitalized closing = 927,000
    q1 = res.repayment_schedule[0]
    assert q1.period_number == 1
    assert q1.is_moratorium is True
    assert q1.opening_balance == pytest.approx(900000.0)
    assert q1.interest_amount == pytest.approx(27000.0)
    assert q1.payment_amount == pytest.approx(0.0)
    assert q1.closing_balance == pytest.approx(927000.0)

    # Quarter 2: opening 927,000, interest 3% = 27,810, capitalized closing = 954,810
    q2 = res.repayment_schedule[1]
    assert q2.period_number == 2
    assert q2.is_moratorium is True
    assert q2.opening_balance == pytest.approx(927000.0)
    assert q2.closing_balance == pytest.approx(954810.0)

    # Quarter 3: repayment begins on capitalized principal of 954,810
    q3 = res.repayment_schedule[2]
    assert q3.period_number == 3
    assert q3.is_moratorium is False
    assert q3.opening_balance == pytest.approx(954810.0)
    assert q3.payment_amount > 0


def test_finance_engine_tenure_not_divisible_by_period_and_short_moratorium():
    """Test tenure 10 months with quarterly frequency (math.ceil -> 4 periods) and moratorium 1 month (math.ceil -> 1 period)."""
    rule = SchemeRuleInput(
        beneficiary_contribution_percent=10.0,
        loan_percent=90.0,
        interest_rate=12.0,
        tenure_months=10,  # 10 months / 3 = 3.33 -> 4 quarters
        moratorium_months=1,  # 1 month / 3 = 0.33 -> 1 quarter moratorium
        payment_frequency="quarterly",
        moratorium_interest_treatment="interest_only",
    )
    req = FinanceCalculateRequest(
        available_capital=100000.0,
        scheme_rule_override=rule,
    )
    res = FinanceService.calculate_finance(req)

    assert res.status == "success"
    assert len(res.repayment_schedule) == 4
    assert res.repayment_schedule[0].is_moratorium is True
    assert res.repayment_schedule[1].is_moratorium is False


def test_finance_engine_zero_interest_loan_quarterly():
    """Test zero interest rate calculation with quarterly repayment frequency."""
    rule = SchemeRuleInput(
        beneficiary_contribution_percent=10.0,
        loan_percent=90.0,
        interest_rate=0.0,
        tenure_months=12,
        payment_frequency="quarterly",
    )
    req = FinanceCalculateRequest(
        available_capital=100000.0,
        scheme_rule_override=rule,
    )
    res = FinanceService.calculate_finance(req)

    assert res.status == "success"
    assert len(res.repayment_schedule) == 4
    # Potential loan 900,000 / 4 quarters = 225,000 per quarter
    for item in res.repayment_schedule:
        assert item.interest_amount == pytest.approx(0.0)
        assert item.payment_amount == pytest.approx(225000.0)


def test_finance_engine_unspecified_moratorium_requires_verification():
    """Test that unspecified moratorium interest treatment sets verification_required=True."""
    rule = SchemeRuleInput(
        beneficiary_contribution_percent=10.0,
        loan_percent=90.0,
        interest_rate=8.0,
        tenure_months=60,
        moratorium_months=6,
        moratorium_interest_treatment=None,  # Unspecified
    )
    req = FinanceCalculateRequest(
        available_capital=100000.0,
        scheme_rule_override=rule,
    )
    res = FinanceService.calculate_finance(req)

    assert res.status == "success"
    assert res.verification_required is True
    assert res.repayment_schedule[0].verification_required is True


def test_finance_engine_below_minimum_cost():
    """Test returning status='below_minimum_cost' when feasible cost is below scheme min_project_cost."""
    rule = SchemeRuleInput(
        beneficiary_contribution_percent=10.0,
        loan_percent=90.0,
        interest_rate=8.0,
        tenure_months=60,
        min_project_cost=500000.0,  # Minimum 5 Lakh project cost
    )
    req = FinanceCalculateRequest(
        available_capital=20000.0,  # 20k supports only 2 Lakh project cost (< 5 Lakh min)
        scheme_rule_override=rule,
    )
    res = FinanceService.calculate_finance(req)

    assert res.status == "below_minimum_cost"
    assert res.available_capital == pytest.approx(20000.0)
    assert res.required_contribution == pytest.approx(50000.0)
    assert res.shortfall == pytest.approx(30000.0)


def test_finance_engine_shortfall_prompt_example():
    """
    Test exact prompt shortfall example:
    Available capital = 50,000
    Desired project cost = 10,00,000 (Required contribution = 1,00,000)
    Expected status = 'insufficient_margin', shortfall = 50,000
    """
    rule = SchemeRuleInput(
        beneficiary_contribution_percent=10.0,
        loan_percent=90.0,
        interest_rate=8.0,
        tenure_months=60,
    )
    req = FinanceCalculateRequest(
        available_capital=50000.0,
        desired_project_cost=1000000.0,
        scheme_rule_override=rule,
    )
    res = FinanceService.calculate_finance(req)

    assert res.status == "insufficient_margin"
    assert res.available_capital == pytest.approx(50000.0)
    assert res.required_contribution == pytest.approx(100000.0)
    assert res.shortfall == pytest.approx(50000.0)


def test_finance_engine_database_rule_and_persistence(session: Session):
    """Test fetching SchemeRule from DB and persisting FinancialAnalysis & RepaymentSchedule results."""
    profile = Profile(auth_user_id=uuid4(), name="Test Entrepreneur")
    session.add(profile)
    session.commit()

    run = AnalysisRun(user_id=profile.id, available_capital=150000.0)
    session.add(run)
    session.commit()

    scheme = Scheme(name="PMEGP Micro Scheme", active=True)
    session.add(scheme)
    session.commit()

    rule = SchemeRule(
        scheme_id=scheme.id,
        beneficiary_contribution_percent=15.0,
        loan_percent=85.0,
        min_project_cost=50000.0,
        max_project_cost=1000000.0,
        max_loan_amount=800000.0,
        interest_rate=9.5,
        tenure_months=60,
        moratorium_months=3,
        payment_frequency="monthly",
        moratorium_interest_treatment="interest_only",
    )
    session.add(rule)
    session.commit()

    req = FinanceCalculateRequest(
        available_capital=150000.0,
        scheme_id=scheme.id,
        analysis_run_id=run.id,
        monthly_revenue=80000.0,
        monthly_operating_cost=45000.0,
    )
    res = FinanceService.calculate_finance(req, session=session)

    assert res.status == "success"
    assert res.beneficiary_contribution_percent == pytest.approx(15.0)
    assert res.loan_percent == pytest.approx(85.0)
    assert res.feasible_project_cost == pytest.approx(1000000.0)
    assert res.potential_loan == pytest.approx(800000.0)

    # Verify DB persistence
    db_analysis = session.exec(
        select(FinancialAnalysis).where(FinancialAnalysis.analysis_run_id == run.id)
    ).first()
    assert db_analysis is not None
    assert db_analysis.calculated_loan == pytest.approx(800000.0)

    schedules = session.exec(
        select(RepaymentSchedule).where(RepaymentSchedule.financial_analysis_id == db_analysis.id)
    ).all()
    assert len(schedules) == 60
    assert schedules[0].opening_balance == pytest.approx(800000.0)
    assert schedules[0].is_moratorium is True


def test_finance_engine_database_error_handling(monkeypatch):
    """Test that a database exception returns a graceful database_error response."""

    class BrokenSession:
        def exec(self, statement):
            raise RuntimeError("Database connection lost")

    req = FinanceCalculateRequest(
        available_capital=100000.0,
        scheme_id=uuid4(),
    )
    res = FinanceService.calculate_finance(req, session=BrokenSession())
    assert res.status == "database_error"
    assert "database error" in res.message.lower()
