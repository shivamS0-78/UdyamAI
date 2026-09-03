"""
Loan calculation module for UdyamAI Finance Engine.
Handles raw potential loan estimation and loan caps application.
"""


def calculate_raw_loan(feasible_project_cost: float, loan_percent: float) -> float:
    """
    Calculates raw potential loan based on feasible project cost and scheme loan percentage.
    Example: Project cost ₹10,00,000, Loan 90% -> ₹9,00,000
    """
    return feasible_project_cost * (loan_percent / 100.0)


def apply_loan_cap(raw_loan: float, max_loan_amount: float | None = None) -> tuple[float, bool]:
    """
    Applies scheme max loan cap to raw loan.
    Returns (potential_loan, cap_applied).
    """
    potential_loan = raw_loan
    cap_applied = False

    if max_loan_amount is not None and max_loan_amount > 0:
        if potential_loan > max_loan_amount:
            potential_loan = max_loan_amount
            cap_applied = True

    return potential_loan, cap_applied
