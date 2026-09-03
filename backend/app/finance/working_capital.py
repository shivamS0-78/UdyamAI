"""
Working Capital module for UdyamAI Finance Engine.
Calculates working capital allocation where supported by scheme rules.
"""


def calculate_working_capital(
    project_cost: float, working_capital_percent: float | None = None
) -> float | None:
    """
    Calculates working capital amount if supported by scheme rules (e.g. 20% of project cost).
    """
    if working_capital_percent is None or working_capital_percent <= 0:
        return None
    return round(project_cost * (working_capital_percent / 100.0), 2)
