"""Market Risks Assessment Engine for UdyamAI.

Evaluates deterministic risk indicators supported by empirical data thresholds.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    """Safely parses float environment variable falling back to default on invalid inputs."""
    val = os.getenv(name)
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        logger.warning("Invalid float for %s: %r, using default %s", name, val, default)
        return default


def _env_int(name: str, default: int) -> int:
    """Safely parses int environment variable falling back to default on invalid inputs."""
    val = os.getenv(name)
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        logger.warning("Invalid int for %s: %r, using default %s", name, val, default)
        return default


# ------------------------------------------------------------------ #
# Empirical Threshold Constants (Configurable via Environment)
# ------------------------------------------------------------------ #

HIGH_COMPETITOR_DENSITY_THRESHOLD = _env_float("HIGH_COMPETITOR_DENSITY_THRESHOLD", 5.0)
VERY_HIGH_COMPETITOR_DENSITY_THRESHOLD = _env_float("VERY_HIGH_COMPETITOR_DENSITY_THRESHOLD", 10.0)

SEASONAL_VOLATILITY_THRESHOLD = _env_float("SEASONAL_VOLATILITY_THRESHOLD", 0.25)
VERY_HIGH_SEASONAL_VOLATILITY_THRESHOLD = _env_float(
    "VERY_HIGH_SEASONAL_VOLATILITY_THRESHOLD", 0.35
)

LOW_MARKET_ACCESS_DISTANCE_KM = _env_float("LOW_MARKET_ACCESS_DISTANCE_KM", 10.0)
VERY_LOW_MARKET_ACCESS_DISTANCE_KM = _env_float("VERY_LOW_MARKET_ACCESS_DISTANCE_KM", 20.0)

PRICE_VOLATILITY_THRESHOLD = _env_float("PRICE_VOLATILITY_THRESHOLD", 0.20)
VERY_HIGH_PRICE_VOLATILITY_THRESHOLD = _env_float("VERY_HIGH_PRICE_VOLATILITY_THRESHOLD", 0.35)

LOW_DEMOGRAPHIC_DEMAND_THRESHOLD = _env_int("LOW_DEMOGRAPHIC_DEMAND_THRESHOLD", 1000)

# Score thresholds for overall risk level classification (0.0 to 10.0 scale)
HIGH_RISK_SCORE_THRESHOLD = _env_float("HIGH_RISK_SCORE_THRESHOLD", 6.0)
MEDIUM_RISK_SCORE_THRESHOLD = _env_float("MEDIUM_RISK_SCORE_THRESHOLD", 3.0)


def _safe_value(v: Any) -> float | int | str | bool | None:
    """Canonicalizes risk metric values to guaranteed JSON-serializable primitives."""
    if v is None:
        return None
    if isinstance(v, (int, float, str, bool)):
        return v
    # Handle Decimal or numpy numeric types safely
    type_name = type(v).__name__.lower()
    if "decimal" in type_name or "float" in type_name:
        try:
            return float(v)
        except Exception:
            pass
    if "int" in type_name:
        try:
            return int(v)
        except Exception:
            pass
    try:
        return float(v)
    except Exception:
        try:
            return int(v)
        except Exception:
            return str(v)


def _safe_num(val: Any, default: float = 0.0) -> float:
    """Safely converts value to float falling back to default on invalid inputs or mocks."""
    if val is None or isinstance(val, bool):
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return default
    return default


def assess_market_risks(
    competition_density: float = 0.0,
    facility_counts: dict[str, int] | None = None,
    price_volatility: str = "low",
    population_reach: int = 0,
    nearby_markets_count: int = 0,
    nearest_market_distance_km: float | None = None,
    single_market_name: str | None = None,
    is_seasonal: bool = False,
    price_volatility_score: float | None = None,
    radius_km: float = 10.0,
    data_available: bool | None = None,
) -> dict[str, Any]:
    """Assess market risks based on competition, infrastructure, volatility, access, and population reach.

    Deterministic Risk Triggers:
    1. high_competitor_density: competition_density > 5.0
    2. seasonal_market: is_seasonal is True or price_volatility in ('seasonal', 'high_seasonal') or price_volatility_score >= 0.25
    3. low_market_access: nearest_market_distance_km > 10.0 or nearby_markets_count == 0
    4. single_market_dependency: nearby_markets_count == 1
    5. limited_infrastructure: zero financial (bank/atm) or zero logistics (cold_storage/warehouse) facilities
    6. price_volatility: price_volatility in ('high', 'very_high') or price_volatility_score >= 0.20
    7. low_demographic_demand: 0 < population_reach < 1000

    Returns:
        Dict containing:
        - overall_market_risk_level ('low', 'medium', 'high', 'insufficient_data')
        - risk_score (0.0 to 10.0)
        - sufficient_data (bool)
        - data_available (bool)
        - risks: List of {risk_type, severity, evidence, source, value} dicts
        - identified_risk_flags: List of summary strings
        - provenance: List of data sources evaluated
    """
    if facility_counts is None:
        facility_counts = {}

    pop_reach = int(_safe_num(population_reach, 0.0))
    comp_density = max(0.0, _safe_num(competition_density, 0.0))

    if data_available is False:
        return {
            "overall_market_risk_level": "insufficient_data",
            "risk_score": 0.0,
            "sufficient_data": False,
            "data_available": False,
            "risks": [],
            "identified_risk_flags": ["Insufficient data to evaluate market risk indicators."],
            "provenance": [],
        }

    risks: list[dict[str, Any]] = []
    overall_risk_score = 0.0

    # 1. high_competitor_density
    if comp_density > HIGH_COMPETITOR_DENSITY_THRESHOLD:
        severity = "high" if comp_density >= VERY_HIGH_COMPETITOR_DENSITY_THRESHOLD else "medium"
        score_add = 3.0 if severity == "high" else 2.0
        overall_risk_score += score_add
        risks.append(
            {
                "risk_type": "high_competitor_density",
                "severity": severity,
                "evidence": f"Competitor density of {comp_density:.2f} competitors/km² exceeds the threshold of {HIGH_COMPETITOR_DENSITY_THRESHOLD:.1f}/km².",
                "source": "Normalized Business Registry",
                "value": _safe_value(round(comp_density, 2)),
            }
        )

    # 2. seasonal_market
    norm_vol_str = (price_volatility or "").strip().lower()
    is_seasonal_trigger = (
        is_seasonal
        or norm_vol_str in ("seasonal", "high_seasonal")
        or (
            price_volatility_score is not None
            and price_volatility_score >= SEASONAL_VOLATILITY_THRESHOLD
        )
    )
    if is_seasonal_trigger:
        severity = (
            "high"
            if (price_volatility_score or 0.0) >= VERY_HIGH_SEASONAL_VOLATILITY_THRESHOLD
            else "medium"
        )
        overall_risk_score += 2.0
        if price_volatility_score is not None:
            ev_str = f"Market exhibits seasonal trade fluctuations with price variance coefficient of {price_volatility_score:.2f}."
            val_out: Any = round(price_volatility_score, 2)
        else:
            ev_str = "Market activity and commodity trade in the region are subject to seasonal peak and off-peak supply cycles."
            val_out = "seasonal"
        risks.append(
            {
                "risk_type": "seasonal_market",
                "severity": severity,
                "evidence": ev_str,
                "source": "Agmarknet & Crop Seasonality Data",
                "value": _safe_value(val_out),
            }
        )

    # 3. low_market_access
    has_low_access = (
        nearest_market_distance_km is not None
        and nearest_market_distance_km > LOW_MARKET_ACCESS_DISTANCE_KM
    ) or (nearby_markets_count == 0)
    if has_low_access:
        if nearby_markets_count == 0:
            severity = "high"
            ev_str = f"Zero commercial markets or mandis identified within {radius_km:.1f}km primary radius."
            val_dist: Any = 0.0
        elif (
            nearest_market_distance_km is not None
            and nearest_market_distance_km > VERY_LOW_MARKET_ACCESS_DISTANCE_KM
        ):
            severity = "high"
            ev_str = f"Nearest commercial market/mandi is located {nearest_market_distance_km:.1f}km away (exceeds {VERY_LOW_MARKET_ACCESS_DISTANCE_KM:.0f}km distant access threshold)."
            val_dist = round(nearest_market_distance_km, 1)
        else:
            severity = "medium"
            ev_str = f"Nearest commercial market/mandi is located {nearest_market_distance_km:.1f}km away (exceeds {LOW_MARKET_ACCESS_DISTANCE_KM:.0f}km access threshold)."
            val_dist = round(nearest_market_distance_km, 1)

        overall_risk_score += 2.5 if severity == "high" else 1.5
        risks.append(
            {
                "risk_type": "low_market_access",
                "severity": severity,
                "evidence": ev_str,
                "source": "Market & Mandi Registry",
                "value": _safe_value(val_dist),
            }
        )

    # 4. single_market_dependency
    if nearby_markets_count == 1:
        overall_risk_score += 1.5
        m_name_str = f" ({single_market_name})" if single_market_name else ""
        risks.append(
            {
                "risk_type": "single_market_dependency",
                "severity": "medium",
                "evidence": f"Only 1 commercial market{m_name_str} identified within {radius_km:.1f}km radius, creating single-point market dependency.",
                "source": "Market & Mandi Registry",
                "value": _safe_value(1),
            }
        )

    # 5. limited_infrastructure
    financial_count = facility_counts.get("bank", 0) + facility_counts.get("atm", 0)
    logistics_count = facility_counts.get("cold_storage", 0) + facility_counts.get("warehouse", 0)

    if financial_count == 0 or logistics_count == 0:
        if financial_count == 0 and logistics_count == 0:
            severity = "high"
            ev_str = "Zero financial infrastructure (banks/ATMs) and zero storage/cold chain facilities identified in primary radius."
            score_add = 3.0
        elif financial_count == 0:
            severity = "medium"
            ev_str = "Financial infrastructure gap: Zero formal banking or ATM facilities identified within primary radius."
            score_add = 1.5
        else:
            severity = "medium"
            ev_str = "Logistics infrastructure gap: Zero cold storage or warehouse facilities identified within primary radius."
            score_add = 1.5

        overall_risk_score += score_add
        risks.append(
            {
                "risk_type": "limited_infrastructure",
                "severity": severity,
                "evidence": ev_str,
                "source": "Facilities & Infrastructure Registry",
                "value": _safe_value(f"financial:{financial_count},logistics:{logistics_count}"),
            }
        )

    # 6. price_volatility
    is_high_vol = norm_vol_str in ("high", "very_high") or (
        price_volatility_score is not None and price_volatility_score >= PRICE_VOLATILITY_THRESHOLD
    )
    if is_high_vol:
        severity = (
            "high"
            if (
                norm_vol_str == "very_high"
                or (price_volatility_score or 0.0) >= VERY_HIGH_PRICE_VOLATILITY_THRESHOLD
            )
            else "medium"
        )
        overall_risk_score += 2.5 if severity == "high" else 1.5
        if price_volatility_score is not None:
            ev_str = f"Commodity prices exhibit high historical volatility ({price_volatility_score * 100:.1f}% variance coefficient)."
            val_vol: Any = round(price_volatility_score, 2)
        else:
            ev_str = (
                "Commodity prices in surrounding markets exhibit high historical price volatility."
            )
            val_vol = norm_vol_str or "high"
        risks.append(
            {
                "risk_type": "price_volatility",
                "severity": severity,
                "evidence": ev_str,
                "source": "Agmarknet Price Records",
                "value": _safe_value(val_vol),
            }
        )

    # 7. low_demographic_demand
    if 0 < pop_reach < LOW_DEMOGRAPHIC_DEMAND_THRESHOLD:
        overall_risk_score += 2.0
        risks.append(
            {
                "risk_type": "low_demographic_demand",
                "severity": "medium",
                "evidence": f"Total population reach within radius is {pop_reach} (below {LOW_DEMOGRAPHIC_DEMAND_THRESHOLD:,} threshold for viable local demand).",
                "source": "Census Population Data",
                "value": _safe_value(pop_reach),
            }
        )

    # Deterministically sort risks by risk_type key for predictable API output
    risks.sort(key=lambda r: str(r.get("risk_type")))

    # Risk level classification
    risk_score_capped = round(min(overall_risk_score, 10.0), 1)
    if risk_score_capped >= HIGH_RISK_SCORE_THRESHOLD:
        risk_level = "high"
    elif risk_score_capped >= MEDIUM_RISK_SCORE_THRESHOLD:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Human-readable summary flags
    identified_flags = [
        f"{r['risk_type'].replace('_', ' ').title()} ({r['severity'].upper()}): {r['evidence']}"
        for r in risks
    ]

    provenance = [
        {
            "dataset_name": "Market Risk Indicators Engine",
            "source": r["source"],
            "source_url": None,
            "data_year": 2026,
            "record_count": len(risks),
            "confidence_score": "high",
        }
        for r in risks
    ]

    return {
        "overall_market_risk_level": risk_level,
        "risk_score": risk_score_capped,
        "sufficient_data": True,
        "data_available": True,
        "risks": risks,
        "identified_risk_flags": identified_flags,
        "provenance": provenance,
    }
