"""
Break-Even calculation module for UdyamAI Finance Engine.
Calculates break-even period (in months) based on capital investment, net profit,
and optional subsidy / debt service deductions.
"""


def calculate_break_even_period(
    project_cost: float,
    monthly_profit: float,
    subsidy_amount: float = 0.0,
    monthly_emi: float = 0.0,
    use_cash_surplus: bool = False,
) -> float | None:
    """
    Calculates the break-even period in months for an enterprise investment.

    Net capital invested = max(0.0, project_cost - subsidy_amount)
    If use_cash_surplus is True and monthly_emi > 0:
        net_monthly_recovery = monthly_profit - monthly_emi
    else:
        net_monthly_recovery = monthly_profit

    Returns:
        Break-even duration in months rounded to 1 decimal place, or None if net recovery is <= 0.
    """
    if project_cost <= 0 or monthly_profit <= 0:
        return None

    net_investment = max(0.0, project_cost - max(0.0, subsidy_amount))
    if net_investment <= 0:
        return 0.0

    monthly_recovery = monthly_profit
    if use_cash_surplus and monthly_emi > 0:
        surplus = monthly_profit - monthly_emi
        if surplus > 0:
            monthly_recovery = surplus

    if monthly_recovery <= 0:
        return None

    months = round(net_investment / monthly_recovery, 1)
    return months
