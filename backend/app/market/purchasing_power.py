"""Purchasing Power Estimation and Economic Proxies for UdyamAI."""

from typing import Any


def estimate_purchasing_power(
    population_reach: int,
    household_reach: int,
    working_population: int,
    economic_indicators: list[dict[str, Any]],
) -> dict[str, Any]:
    """Estimate purchasing power tier and per-household income indicators.

    Args:
        population_reach: Total population reach.
        household_reach: Total household reach.
        working_population: Total working population.
        economic_indicators: List of economic indicator records.

    Returns:
        Dict containing purchasing power tier (low/medium/high),
        working ratio proxy, and indicator details.
    """
    working_ratio = (working_population / population_reach) if population_reach > 0 else 0.4

    # Extract income per capita if present in economic_indicators
    per_capita_income = None
    for rec in economic_indicators:
        if rec.get("indicator_name") in (
            "per_capita_income",
            "gdpp_per_capita",
            "avg_monthly_income",
        ):
            per_capita_income = rec.get("indicator_value")
            break

    purchasing_power_tier = "medium"
    if per_capita_income is not None:
        if per_capita_income > 150000:
            purchasing_power_tier = "high"
        elif per_capita_income < 60000:
            purchasing_power_tier = "low"
    else:
        if working_ratio > 0.55:
            purchasing_power_tier = "medium-high"
        elif working_ratio < 0.35:
            purchasing_power_tier = "low"

    return {
        "purchasing_power_tier": purchasing_power_tier,
        "estimated_per_capita_income": per_capita_income,
        "working_ratio": round(working_ratio, 3),
    }
