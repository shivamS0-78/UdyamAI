"""
Moratorium module for UdyamAI Finance Engine.
Provides functions for validating and evaluating moratorium terms under scheme rules.
"""


def validate_moratorium(moratorium_months: int, tenure_months: int) -> int:
    """
    Validates moratorium months against total loan tenure.
    Moratorium cannot equal or exceed total loan tenure.
    """
    if moratorium_months < 0:
        return 0
    if moratorium_months >= tenure_months:
        return max(0, tenure_months - 1)
    return moratorium_months
