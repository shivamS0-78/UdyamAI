"""Feasibility Scoring Engine for UdyamAI.

Computes deterministic sub-scores and overall score (0 to 100 scale)
combining Market, Finance, Competition, Infrastructure, and Risk indicators.
Zero LLM calls are made during score calculations.
"""

import os
from typing import Any

# ------------------------------------------------------------------ #
# Configurable Scoring Weights (Must sum to 1.0)
# ------------------------------------------------------------------ #

MARKET_WEIGHT = float(os.getenv("FEASIBILITY_MARKET_WEIGHT", "0.25"))
FINANCIAL_WEIGHT = float(os.getenv("FEASIBILITY_FINANCIAL_WEIGHT", "0.25"))
COMPETITION_WEIGHT = float(os.getenv("FEASIBILITY_COMPETITION_WEIGHT", "0.20"))
INFRASTRUCTURE_WEIGHT = float(os.getenv("FEASIBILITY_INFRASTRUCTURE_WEIGHT", "0.15"))
RISK_WEIGHT = float(os.getenv("FEASIBILITY_RISK_WEIGHT", "0.15"))


def calculate_market_score(
    population_reach: int = 0,
    household_reach: int = 0,
    nearest_market_distance_km: float | None = None,
    nearby_markets_count: int = 0,
    data_available: bool = True,
) -> float:
    """Calculate deterministic market score (0.0 to 100.0)."""
    if not data_available:
        return 0.0

    pop = max(0, int(population_reach or 0))
    hh = max(0, int(household_reach or 0))

    if pop == 0 and hh == 0 and nearby_markets_count <= 0 and nearest_market_distance_km is None:
        return 0.0

    # Population reach component (max 40 pts, benchmark 25,000 population)
    pop_score = min(40.0, (pop / 25000.0) * 40.0)

    # Household reach component (max 30 pts, benchmark 5,000 households)
    hh_score = min(30.0, (hh / 5000.0) * 30.0)

    # Market access & proximity component (max 30 pts)
    if nearby_markets_count <= 0:
        access_score = 0.0
    elif nearest_market_distance_km is not None:
        dist = float(nearest_market_distance_km)
        if dist <= 5.0:
            access_score = 30.0
        elif dist <= 15.0:
            access_score = 22.0
        elif dist <= 30.0:
            access_score = 14.0
        else:
            access_score = 8.0
    else:
        access_score = 15.0

    score = pop_score + hh_score + access_score
    return round(min(100.0, max(0.0, score)), 1)


def calculate_financial_score(
    available_capital: float = 0.0,
    desired_project_cost: float = 0.0,
    estimated_subsidy: float = 0.0,
    data_available: bool = True,
) -> float:
    """Calculate deterministic financial score (0.0 to 100.0)."""
    if not data_available:
        return 0.0

    cap = max(0.0, float(available_capital or 0.0))
    cost = max(0.0, float(desired_project_cost or 0.0))
    sub = max(0.0, float(estimated_subsidy or 0.0))

    if cost <= 0.0:
        return 0.0

    equity_ratio = cap / cost

    # Equity contribution component (max 60 pts)
    # 30%+ equity contribution = 60 pts; linear scaling down to 0
    equity_score = min(60.0, (equity_ratio / 0.30) * 60.0)

    # Subsidy support component (max 40 pts)
    subsidy_ratio = sub / cost
    subsidy_score = min(40.0, (subsidy_ratio / 0.35) * 40.0)

    score = equity_score + subsidy_score
    return round(min(100.0, max(0.0, score)), 1)


def calculate_competition_score(
    competition_density: float = 0.0,
    competitor_count: int | None = None,
    data_available: bool = True,
) -> float:
    """Calculate deterministic competition score (0.0 to 100.0).

    Higher score indicates higher safety margin / lower competitive saturation.
    When data_available is False (no business records found in radius), returns 0.0.
    When data_available is True and measured competitors is 0, returns high safety score.
    """
    if not data_available:
        return 0.0

    if competitor_count is not None:
        count = max(0, int(competitor_count))
        if count == 0:
            return 95.0
        elif count == 1:
            return 85.0
        elif count == 2:
            return 75.0
        elif count == 3:
            return 65.0
        elif count <= 5:
            return round(55.0 - (count - 4) * 6.0, 1)
        elif count <= 10:
            return round(max(30.0, 48.0 - (count - 6) * 3.5), 1)
        else:
            return round(max(15.0, 30.0 - (count - 10) * 1.5), 1)

    density = max(0.0, float(competition_density or 0.0))
    if density <= 0.0:
        return 100.0
    elif density <= 2.0:
        score = 100.0 - (density / 2.0) * 15.0
    elif density <= 5.0:
        score = 85.0 - ((density - 2.0) / 3.0) * 20.0
    elif density <= 10.0:
        score = 65.0 - ((density - 5.0) / 5.0) * 25.0
    else:
        score = max(10.0, 40.0 - ((density - 10.0) / 10.0) * 25.0)

    return round(min(100.0, max(0.0, score)), 1)


def calculate_infrastructure_score(
    facility_counts: dict[str, int] | None = None,
    data_available: bool = True,
) -> float:
    """Calculate deterministic infrastructure score (0.0 to 100.0)."""
    if not data_available:
        return 0.0

    if not isinstance(facility_counts, dict):
        facility_counts = {}

    financial_count = max(0, int(facility_counts.get("bank", 0) or 0)) + max(
        0, int(facility_counts.get("atm", 0) or 0)
    )
    logistics_count = max(0, int(facility_counts.get("cold_storage", 0) or 0)) + max(
        0, int(facility_counts.get("warehouse", 0) or 0)
    )
    other_infra = max(0, int(facility_counts.get("mandi", 0) or 0)) + max(
        0, int(facility_counts.get("market", 0) or 0)
    )

    # Financial infrastructure (max 50 pts)
    fin_score = min(50.0, financial_count * 25.0)

    # Logistics & Storage infrastructure (max 40 pts)
    log_score = min(40.0, logistics_count * 20.0)

    # General market facilities (max 10 pts)
    other_score = min(10.0, other_infra * 5.0)

    score = fin_score + log_score + other_score
    return round(min(100.0, max(0.0, score)), 1)


def calculate_risk_safety_score(
    engine_risk_score: float = 0.0,
    data_available: bool = True,
) -> float:
    """Calculate deterministic risk safety score (0.0 to 100.0).

    Engine risk score is on 0.0 to 10.0 scale (higher = riskier).
    Risk safety score inverts this scale: 0.0 risk = 100.0 safety.
    When data_available is False, returns 0.0 (unsupported safety).
    """
    if not data_available:
        return 0.0

    risk = max(0.0, float(engine_risk_score or 0.0))
    safety = 100.0 - (min(10.0, risk) * 10.0)
    return round(safety, 1)


def calculate_feasibility_scores(
    population_reach: int = 0,
    household_reach: int = 0,
    nearest_market_distance_km: float | None = None,
    nearby_markets_count: int = 0,
    available_capital: float = 0.0,
    desired_project_cost: float = 0.0,
    estimated_subsidy: float = 0.0,
    competition_density: float = 0.0,
    facility_counts: dict[str, int] | None = None,
    engine_risk_score: float = 0.0,
    competitor_count: int | None = None,
    market_data_available: bool = True,
    financial_data_available: bool | None = None,
    competition_data_available: bool = True,
    infrastructure_data_available: bool = True,
    risk_data_available: bool = True,
) -> dict[str, Any]:
    """Calculate all sub-scores, data confidence, and deterministic overall feasibility score.

    Returns:
        Dict containing:
        - market_score (0.0 - 100.0)
        - financial_score (0.0 - 100.0)
        - competition_score (0.0 - 100.0)
        - infrastructure_score (0.0 - 100.0)
        - risk_score (0.0 - 100.0)
        - overall_score (0.0 - 100.0)
        - market_data_available (bool)
        - financial_data_available (bool)
        - competition_data_available (bool)
        - infrastructure_data_available (bool)
        - risk_data_available (bool)
        - data_confidence (str: 'high', 'medium', 'low', 'insufficient')
    """
    if financial_data_available is None:
        financial_data_available = float(desired_project_cost or 0.0) > 0.0

    mkt_s = calculate_market_score(
        population_reach=population_reach,
        household_reach=household_reach,
        nearest_market_distance_km=nearest_market_distance_km,
        nearby_markets_count=nearby_markets_count,
        data_available=market_data_available,
    )
    fin_s = calculate_financial_score(
        available_capital=available_capital,
        desired_project_cost=desired_project_cost,
        estimated_subsidy=estimated_subsidy,
        data_available=financial_data_available,
    )
    comp_s = calculate_competition_score(
        competition_density=competition_density,
        competitor_count=competitor_count,
        data_available=competition_data_available,
    )
    infra_s = calculate_infrastructure_score(
        facility_counts=facility_counts,
        data_available=infrastructure_data_available,
    )
    risk_s = calculate_risk_safety_score(
        engine_risk_score=engine_risk_score,
        data_available=risk_data_available,
    )

    available_flags = [
        market_data_available,
        financial_data_available,
        competition_data_available,
        infrastructure_data_available,
        risk_data_available,
    ]
    available_count = sum(1 for f in available_flags if f)
    if available_count == 5:
        data_confidence = "high"
    elif available_count >= 3:
        data_confidence = "medium"
    elif available_count >= 1:
        data_confidence = "low"
    else:
        data_confidence = "insufficient"

    overall = round(
        (mkt_s * MARKET_WEIGHT)
        + (fin_s * FINANCIAL_WEIGHT)
        + (comp_s * COMPETITION_WEIGHT)
        + (infra_s * INFRASTRUCTURE_WEIGHT)
        + (risk_s * RISK_WEIGHT),
        1,
    )

    return {
        "market_score": mkt_s,
        "financial_score": fin_s,
        "competition_score": comp_s,
        "infrastructure_score": infra_s,
        "risk_score": risk_s,
        "overall_score": min(100.0, max(0.0, overall)),
        "market_data_available": market_data_available,
        "financial_data_available": financial_data_available,
        "competition_data_available": competition_data_available,
        "infrastructure_data_available": infrastructure_data_available,
        "risk_data_available": risk_data_available,
        "data_confidence": data_confidence,
    }
