"""
Orchestrates scheme-rule driven financial calculations, caps, shortfall detection, schedule generation, and scenarios.
"""

from typing import Any

from app.config import settings
from app.finance.emi import generate_amortization_schedule
from app.finance.loan import apply_loan_cap, calculate_raw_loan
from app.finance.moratorium import validate_moratorium
from app.finance.profitability import generate_financial_scenarios
from app.finance.project_cost import (
    apply_project_cost_caps,
    calculate_raw_project_cost,
    calculate_required_contribution,
)
from app.finance.working_capital import calculate_working_capital
from app.schemas.finance import FinanceCalculateRequest, FinanceCalculateResponse

# Module-level defaults populated from application configuration settings
DEFAULT_BENEFICIARY_CONTRIBUTION_PERCENT: float = settings.DEFAULT_BENEFICIARY_CONTRIBUTION_PERCENT
DEFAULT_INTEREST_RATE: float = settings.DEFAULT_INTEREST_RATE
DEFAULT_TENURE_MONTHS: int = settings.DEFAULT_TENURE_MONTHS
DEFAULT_PAYMENT_FREQUENCY: str = settings.DEFAULT_PAYMENT_FREQUENCY


def calculate_finance_engine(
    request: FinanceCalculateRequest, scheme_rule: Any
) -> FinanceCalculateResponse:
    """
    Executes Phase 5 Finance Engine calculations strictly based on provided scheme_rule.
    """
    available_capital = request.available_capital
    desired_project_cost = request.desired_project_cost

    # Extract scheme parameters with explicit module-level default fallbacks
    b_percent = getattr(scheme_rule, "beneficiary_contribution_percent", None)
    if b_percent is None or b_percent <= 0:
        b_percent = DEFAULT_BENEFICIARY_CONTRIBUTION_PERCENT

    l_percent = getattr(scheme_rule, "loan_percent", None)
    if l_percent is None:
        l_percent = max(0.0, 100.0 - b_percent)

    min_pc = getattr(scheme_rule, "min_project_cost", None)
    max_pc = getattr(scheme_rule, "max_project_cost", None)
    max_loan = getattr(scheme_rule, "max_loan_amount", None)

    interest_rate = getattr(scheme_rule, "interest_rate", None)
    if interest_rate is None:
        interest_rate = DEFAULT_INTEREST_RATE

    tenure_months = getattr(scheme_rule, "tenure_months", None)
    if tenure_months is None or tenure_months <= 0:
        tenure_months = DEFAULT_TENURE_MONTHS

    moratorium_months = getattr(scheme_rule, "moratorium_months", 0) or 0
    moratorium_months = validate_moratorium(moratorium_months, tenure_months)

    payment_frequency = getattr(scheme_rule, "payment_frequency", None) or DEFAULT_PAYMENT_FREQUENCY
    moratorium_interest_treatment = getattr(scheme_rule, "moratorium_interest_treatment", None)
    working_cap_percent = getattr(scheme_rule, "working_capital_percent", None)

    # 1. Shortfall Check on Desired Project Cost
    if desired_project_cost is not None and desired_project_cost > 0:
        req_contrib_for_desired = calculate_required_contribution(desired_project_cost, b_percent)
        if available_capital < req_contrib_for_desired:
            shortfall = req_contrib_for_desired - available_capital
            return FinanceCalculateResponse(
                status="insufficient_margin",
                available_capital=available_capital,
                required_contribution=round(req_contrib_for_desired, 2),
                shortfall=round(shortfall, 2),
                desired_project_cost=round(desired_project_cost, 2),
                message=f"Insufficient available capital (₹{available_capital:,.2f}) for desired project cost ₹{desired_project_cost:,.2f}. Shortfall is ₹{shortfall:,.2f}.",
            )

    # 2. Project Cost Calculations
    raw_project_cost = calculate_raw_project_cost(available_capital, b_percent)
    if desired_project_cost is not None and desired_project_cost > 0:
        target_cost = min(raw_project_cost, desired_project_cost)
    else:
        target_cost = raw_project_cost

    feasible_project_cost, project_cap_applied = apply_project_cost_caps(
        target_cost, min_pc, max_pc
    )

    # 3. Minimum Project Cost Check
    if min_pc is not None and target_cost < min_pc:
        req_contrib_for_min = calculate_required_contribution(min_pc, b_percent)
        shortfall = max(0.0, req_contrib_for_min - available_capital)
        return FinanceCalculateResponse(
            status="below_minimum_cost",
            available_capital=available_capital,
            required_contribution=round(req_contrib_for_min, 2),
            shortfall=round(shortfall, 2),
            feasible_project_cost=round(feasible_project_cost, 2),
            max_project_cost_limit=max_pc,
            message=f"Feasible project cost ₹{feasible_project_cost:,.2f} is below minimum allowed scheme cost ₹{min_pc:,.2f}.",
        )

    # 4. Required Contribution & Shortfall
    required_contribution = calculate_required_contribution(feasible_project_cost, b_percent)
    margin_shortfall = max(0.0, required_contribution - available_capital)

    # 5. Potential Loan Calculations
    raw_loan = calculate_raw_loan(feasible_project_cost, l_percent)
    potential_loan, loan_cap_applied = apply_loan_cap(raw_loan, max_loan)

    # 6. Amortization & Repayment Schedule
    (
        monthly_emi,
        total_interest,
        total_repayment,
        verification_required,
        schedule,
    ) = generate_amortization_schedule(
        loan_amount=potential_loan,
        annual_interest_rate=interest_rate,
        tenure_months=tenure_months,
        moratorium_months=moratorium_months,
        payment_frequency=payment_frequency,
        moratorium_interest_treatment=moratorium_interest_treatment,
    )

    # 7. Working Capital Support
    working_capital = calculate_working_capital(feasible_project_cost, working_cap_percent)

    # 8. Financial Scenarios
    scenarios = generate_financial_scenarios(
        monthly_revenue=request.monthly_revenue,
        monthly_operating_cost=request.monthly_operating_cost,
        monthly_emi=monthly_emi,
        verified_revenue=request.verified_revenue,
        verified_operating_cost=request.verified_operating_cost,
        scenario_config=request.scenario_config,
    )

    return FinanceCalculateResponse(
        status="success",
        available_capital=round(available_capital, 2),
        required_contribution=round(required_contribution, 2),
        shortfall=round(margin_shortfall, 2),
        desired_project_cost=round(desired_project_cost, 2) if desired_project_cost else None,
        feasible_project_cost=round(feasible_project_cost, 2),
        potential_loan=round(potential_loan, 2),
        project_cost_cap_applied=project_cap_applied,
        loan_cap_applied=loan_cap_applied,
        max_project_cost_limit=max_pc,
        max_loan_amount_limit=max_loan,
        beneficiary_contribution_percent=b_percent,
        loan_percent=l_percent,
        interest_rate=interest_rate,
        tenure_months=tenure_months,
        moratorium_months=moratorium_months,
        payment_frequency=payment_frequency,
        moratorium_interest_treatment=moratorium_interest_treatment,
        verification_required=verification_required,
        monthly_emi=monthly_emi,
        total_interest=total_interest,
        total_repayment=total_repayment,
        working_capital=working_capital,
        repayment_schedule=schedule,
        financial_scenarios=scenarios,
        message="Financial calculations completed successfully.",
    )
