"""
EMI calculation module for UdyamAI Finance Engine.
Handles standard loan amortization formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
Supports scheme payment frequencies (monthly, quarterly, semi_annually, annually)
and stored moratorium interest treatments (interest_only, capitalized, waived, or requiring verification).
"""

import math

from app.schemas.finance import RepaymentScheduleItemResponse


def get_periods_per_year(payment_frequency: str | None) -> int:
    """
    Returns the number of payment periods per year for the given scheme payment frequency.
    """
    if not payment_frequency:
        return 12

    freq = payment_frequency.lower().strip()
    if freq in ("monthly", "month", "m"):
        return 12
    elif freq in ("quarterly", "quarter", "q"):
        return 4
    elif freq in ("semi_annually", "semi-annually", "half_yearly", "half-yearly", "sa"):
        return 2
    elif freq in ("annually", "annual", "yearly", "a", "y"):
        return 1
    return 12


def calculate_amortization_emi(
    principal: float, periodic_interest_rate: float, active_repayment_periods: int
) -> float:
    """
    Calculates installment payment for active repayment periods using standard amortization formula:
    EMI = P * [r(1+r)^n] / [(1+r)^n - 1]
    """
    if principal <= 0 or active_repayment_periods <= 0:
        return 0.0

    if periodic_interest_rate == 0:
        return principal / active_repayment_periods

    r = periodic_interest_rate
    n = active_repayment_periods
    factor = (1 + r) ** n
    return principal * (r * factor) / (factor - 1)


def generate_amortization_schedule(
    loan_amount: float,
    annual_interest_rate: float,
    tenure_months: int,
    moratorium_months: int = 0,
    payment_frequency: str | None = "monthly",
    moratorium_interest_treatment: str | None = None,
) -> tuple[float, float, float, bool, list[RepaymentScheduleItemResponse]]:
    """
    Generates period-by-period amortization schedule adhering strictly to scheme payment frequency
    and stored moratorium interest treatment rules. Uses ceiling logic for period count so partial
    months map correctly to complete payment periods.

    Moratorium Flow:
    Loan sanctioned -> Moratorium -> Repayment begins

    Returns (installment_amount, total_interest, total_repayment, verification_required, schedule).
    """
    if loan_amount <= 0 or tenure_months <= 0:
        return 0.0, 0.0, 0.0, False, []

    periods_per_year = get_periods_per_year(payment_frequency)
    months_per_period = max(1, 12 // periods_per_year)

    # Use math.ceil so partial periods count (e.g. 10 months quarterly = 4 quarters)
    total_periods = max(1, math.ceil(tenure_months / months_per_period))
    moratorium_periods = 0
    if moratorium_months > 0:
        moratorium_periods = min(
            math.ceil(moratorium_months / months_per_period), max(0, total_periods - 1)
        )
    active_repayment_periods = max(1, total_periods - moratorium_periods)

    periodic_rate = (annual_interest_rate / periods_per_year) / 100.0

    # Determine moratorium interest treatment rule
    verification_required = False
    treatment = "interest_only"
    if moratorium_periods > 0:
        if not moratorium_interest_treatment:
            verification_required = True
            treatment = "interest_only"
        else:
            t_lower = moratorium_interest_treatment.lower().strip()
            if "capital" in t_lower:
                treatment = "capitalized"
            elif "waiv" in t_lower or "subsid" in t_lower:
                treatment = "waived"
            elif "interest" in t_lower or "pay" in t_lower:
                treatment = "interest_only"
            else:
                verification_required = True
                treatment = "interest_only"

    schedule: list[RepaymentScheduleItemResponse] = []
    current_balance = loan_amount
    total_interest = 0.0
    total_repayment = 0.0

    # 1. Moratorium Phase
    for period_idx in range(1, moratorium_periods + 1):
        opening_bal = current_balance
        interest_accrued = opening_bal * periodic_rate

        if treatment == "interest_only":
            principal_paid = 0.0
            interest_paid = interest_accrued
            payment_amount = interest_paid
            closing_bal = opening_bal
        elif treatment == "capitalized":
            principal_paid = 0.0
            interest_paid = interest_accrued
            payment_amount = 0.0
            closing_bal = opening_bal + interest_accrued
            current_balance = closing_bal
        elif treatment == "waived":
            principal_paid = 0.0
            interest_paid = 0.0
            payment_amount = 0.0
            closing_bal = opening_bal

        total_interest += interest_paid
        total_repayment += payment_amount

        schedule.append(
            RepaymentScheduleItemResponse(
                period_number=period_idx,
                opening_balance=round(opening_bal, 2),
                payment_amount=round(payment_amount, 2),
                principal_amount=round(principal_paid, 2),
                interest_amount=round(interest_paid, 2),
                closing_balance=round(max(0.0, closing_bal), 2),
                remaining_principal=round(max(0.0, closing_bal), 2),
                is_moratorium=True,
                verification_required=verification_required,
            )
        )

    # 2. Calculate Active Repayment Installment
    repayment_principal_base = current_balance
    periodic_installment = calculate_amortization_emi(
        repayment_principal_base, periodic_rate, active_repayment_periods
    )

    # 3. Active Repayment Phase
    for period_idx in range(moratorium_periods + 1, total_periods + 1):
        if current_balance <= 0:
            opening_bal = 0.0
            interest_paid = 0.0
            principal_paid = 0.0
            payment_amount = 0.0
            closing_bal = 0.0
        else:
            opening_bal = current_balance
            interest_paid = opening_bal * periodic_rate
            payment_amount = min(periodic_installment, opening_bal + interest_paid)
            principal_paid = max(0.0, payment_amount - interest_paid)
            closing_bal = opening_bal - principal_paid

            # Reconcile tiny rounding differences in final payment
            if closing_bal < 0.01:
                principal_paid += closing_bal
                payment_amount += closing_bal
                closing_bal = 0.0

            current_balance = closing_bal

        total_interest += interest_paid
        total_repayment += payment_amount

        schedule.append(
            RepaymentScheduleItemResponse(
                period_number=period_idx,
                opening_balance=round(opening_bal, 2),
                payment_amount=round(payment_amount, 2),
                principal_amount=round(principal_paid, 2),
                interest_amount=round(interest_paid, 2),
                closing_balance=round(max(0.0, closing_bal), 2),
                remaining_principal=round(max(0.0, closing_bal), 2),
                is_moratorium=False,
                verification_required=False,
            )
        )

    return (
        round(periodic_installment, 2),
        round(total_interest, 2),
        round(total_repayment, 2),
        verification_required,
        schedule,
    )
