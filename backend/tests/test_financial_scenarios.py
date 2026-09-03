"""
Unit tests for Financial Scenarios (Worst Case, Expected Case, Best Case).
Verifies:
1. Worst case, Expected case, Best case calculation.
2. 5 required fields: revenue, operating costs, surplus, loan repayment, cash surplus.
3. Strict rule: Do not invent local revenue numbers (sufficient_assumptions_exist=False when missing).
4. Data sources: verified data, explicit user assumptions, configurable assumptions.
5. Marked assumptions transparency.
6. Markdown report generation.
"""

import pytest

from app.finance.profitability import generate_financial_scenarios
from app.reports.financial_report import format_financial_scenario_report
from app.schemas.finance import (
    FinanceCalculateRequest,
    ScenarioConfigInput,
    ScenarioMultiplierInput,
)
from app.services.finance_service import FinanceService


def test_scenarios_explicit_user_assumptions():
    """Test scenario calculations using explicit user assumptions."""
    scenarios = generate_financial_scenarios(
        monthly_revenue=100000.0,
        monthly_operating_cost=60000.0,
        monthly_emi=15000.0,
    )

    assert len(scenarios) == 3
    scenarios_by_type = {s.scenario_type: s for s in scenarios}

    # Expected Case (100% rev, 100% cost)
    expected = scenarios_by_type["expected_case"]
    assert expected.sufficient_assumptions_exist is True
    assert expected.data_source == "explicit_user_assumptions"
    assert expected.revenue == pytest.approx(100000.0)
    assert expected.operating_costs == pytest.approx(60000.0)
    assert expected.surplus == pytest.approx(40000.0)
    assert expected.loan_repayment == pytest.approx(15000.0)
    assert expected.cash_surplus == pytest.approx(25000.0)
    assert expected.marked_assumptions["local_revenue_invented"] is False

    # Worst Case (80% rev, 110% cost)
    worst = scenarios_by_type["worst_case"]
    assert worst.sufficient_assumptions_exist is True
    assert worst.revenue == pytest.approx(80000.0)
    assert worst.operating_costs == pytest.approx(66000.0)
    assert worst.surplus == pytest.approx(14000.0)
    assert worst.loan_repayment == pytest.approx(15000.0)
    assert worst.cash_surplus == pytest.approx(-1000.0)

    # Best Case (120% rev, 90% cost)
    best = scenarios_by_type["best_case"]
    assert best.sufficient_assumptions_exist is True
    assert best.revenue == pytest.approx(120000.0)
    assert best.operating_costs == pytest.approx(54000.0)
    assert best.surplus == pytest.approx(66000.0)
    assert best.loan_repayment == pytest.approx(15000.0)
    assert best.cash_surplus == pytest.approx(51000.0)


def test_scenarios_verified_data_priority():
    """Test that verified data takes priority over explicit user assumptions."""
    scenarios = generate_financial_scenarios(
        monthly_revenue=80000.0,
        monthly_operating_cost=50000.0,
        monthly_emi=10000.0,
        verified_revenue=150000.0,
        verified_operating_cost=90000.0,
    )

    expected = next(s for s in scenarios if s.scenario_type == "expected_case")
    assert expected.data_source == "verified_data"
    assert expected.revenue == pytest.approx(150000.0)
    assert expected.operating_costs == pytest.approx(90000.0)
    assert expected.surplus == pytest.approx(60000.0)
    assert expected.cash_surplus == pytest.approx(50000.0)


def test_scenarios_no_revenue_invention():
    """Test strict rule: Do not invent local revenue numbers when no revenue assumption is provided."""
    scenarios = generate_financial_scenarios(
        monthly_revenue=None,
        monthly_operating_cost=50000.0,
        monthly_emi=12000.0,
    )

    assert len(scenarios) == 3
    for s in scenarios:
        assert s.sufficient_assumptions_exist is False
        assert s.revenue is None
        assert s.operating_costs is None
        assert s.surplus is None
        assert s.loan_repayment == pytest.approx(12000.0)
        assert s.cash_surplus is None
        assert s.marked_assumptions["local_revenue_invented"] is False
        assert "Insufficient revenue data" in s.marked_assumptions["status"]


def test_scenarios_configurable_assumptions():
    """Test custom scenario multiplier configuration."""
    custom_config = ScenarioConfigInput(
        worst_case=ScenarioMultiplierInput(revenue_multiplier=0.70, operating_cost_multiplier=1.20),
        expected_case=ScenarioMultiplierInput(
            revenue_multiplier=1.00, operating_cost_multiplier=1.00
        ),
        best_case=ScenarioMultiplierInput(revenue_multiplier=1.30, operating_cost_multiplier=0.85),
    )

    scenarios = generate_financial_scenarios(
        monthly_revenue=100000.0,
        monthly_operating_cost=50000.0,
        monthly_emi=10000.0,
        scenario_config=custom_config,
    )

    scenarios_by_type = {s.scenario_type: s for s in scenarios}
    worst = scenarios_by_type["worst_case"]
    assert worst.revenue == pytest.approx(70000.0)  # 70%
    assert worst.operating_costs == pytest.approx(60000.0)  # 120%
    assert worst.surplus == pytest.approx(10000.0)
    assert worst.cash_surplus == pytest.approx(0.0)

    best = scenarios_by_type["best_case"]
    assert best.revenue == pytest.approx(130000.0)  # 130%
    assert best.operating_costs == pytest.approx(42500.0)  # 85%
    assert best.surplus == pytest.approx(87500.0)
    assert best.cash_surplus == pytest.approx(77500.0)


def test_finance_service_end_to_end_scenarios():
    """Test FinanceService endpoint calculation with verified data and scenario outputs."""
    rule_override = {
        "beneficiary_contribution_percent": 10.0,
        "loan_percent": 90.0,
        "interest_rate": 10.0,
        "tenure_months": 60,
    }
    req = FinanceCalculateRequest(
        available_capital=100000.0,
        scheme_rule_override=rule_override,
        verified_revenue=200000.0,
        verified_operating_cost=120000.0,
    )

    res = FinanceService.calculate_finance(req)
    assert res.status == "success"
    assert len(res.financial_scenarios) == 3

    exp_scen = next(s for s in res.financial_scenarios if s.scenario_type == "expected_case")
    assert exp_scen.sufficient_assumptions_exist is True
    assert exp_scen.data_source == "verified_data"
    assert exp_scen.revenue == pytest.approx(200000.0)
    assert exp_scen.operating_costs == pytest.approx(120000.0)
    assert exp_scen.surplus == pytest.approx(80000.0)
    assert exp_scen.loan_repayment == pytest.approx(res.monthly_emi)
    assert exp_scen.cash_surplus == pytest.approx(80000.0 - res.monthly_emi)


def test_format_financial_scenario_report():
    """Test generating Markdown report from financial scenarios."""
    scenarios = generate_financial_scenarios(
        monthly_revenue=100000.0,
        monthly_operating_cost=60000.0,
        monthly_emi=15000.0,
    )
    report = format_financial_scenario_report(
        scenarios=scenarios, project_cost=1000000.0, loan_amount=900000.0
    )

    assert "# Financial Scenario Analysis Report" in report
    assert "Worst Case" in report
    assert "Expected Case" in report
    assert "Best Case" in report
    assert "₹100,000.00" in report
    assert "Marked Assumptions" in report
