"""
Project Cost calculation module for UdyamAI Finance Engine.
Handles raw project cost estimation, contribution requirements, and project cost cap evaluation.
"""


def calculate_raw_project_cost(
    available_capital: float, beneficiary_contribution_percent: float
) -> float:
    """
    Calculates raw maximum project cost affordable based on available capital and contribution %.
    Example: Available capital ₹1,00,000, Contribution 10% -> ₹1,00,000 / 0.10 = ₹10,00,000
    """
    if beneficiary_contribution_percent <= 0:
        raise ValueError("Beneficiary contribution percentage must be greater than 0.")
    return available_capital / (beneficiary_contribution_percent / 100.0)


def calculate_required_contribution(
    project_cost: float, beneficiary_contribution_percent: float
) -> float:
    """
    Calculates required beneficiary contribution for a given project cost and contribution %.
    Example: Project cost ₹10,00,000, Contribution 10% -> ₹1,00,000
    """
    return project_cost * (beneficiary_contribution_percent / 100.0)


def apply_project_cost_caps(
    raw_cost: float,
    min_project_cost: float | None = None,
    max_project_cost: float | None = None,
) -> tuple[float, bool]:
    """
    Applies scheme project cost caps to raw project cost.
    Returns (feasible_project_cost, cap_applied).
    """
    feasible_cost = raw_cost
    cap_applied = False

    if max_project_cost is not None and max_project_cost > 0:
        if feasible_cost > max_project_cost:
            feasible_cost = max_project_cost
            cap_applied = True

    return feasible_cost, cap_applied
