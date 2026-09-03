"""Pricing Analysis and Price Indicators for UdyamAI."""

from datetime import date, datetime
from typing import Any


def _extract_year(recorded: Any) -> int | None:
    """Safely extract data year from date, datetime, or ISO date string."""
    if not recorded:
        return None
    if isinstance(recorded, (date, datetime)):
        return recorded.year
    if isinstance(recorded, str):
        try:
            return date.fromisoformat(recorded.split("T")[0]).year
        except Exception:
            return None
    return None


def analyze_market_pricing(
    nearby_markets: list[dict[str, Any]],
    market_prices: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze commodity pricing indicators across nearby markets.

    Args:
        nearby_markets: List of market dicts within radius.
        market_prices: List of MarketPrice dicts.

    Returns:
        Dict containing average modal price, commodity samples, price range,
        volatility indicator, and provenance.
    """
    if not market_prices:
        return {
            "average_modal_price": None,
            "min_modal_price": None,
            "max_modal_price": None,
            "commodity_coverage_count": 0,
            "prices_analyzed_count": 0,
            "price_volatility": "low",
            "provenance": [
                {
                    "dataset_name": "Agmarknet / Mandi Prices",
                    "source": "Normalized Data Pipeline",
                    "source_url": None,
                    "data_year": None,
                    "record_count": 0,
                    "confidence_score": "low",
                }
            ],
        }

    modal_prices = [p.get("modal_price") for p in market_prices if p.get("modal_price") is not None]
    commodities = {p.get("commodity") for p in market_prices if p.get("commodity")}

    avg_modal = round(sum(modal_prices) / len(modal_prices), 2) if modal_prices else None
    min_modal = min(modal_prices) if modal_prices else None
    max_modal = max(modal_prices) if modal_prices else None

    # Determine volatility based on spread
    volatility = "low"
    if min_modal and max_modal and avg_modal and avg_modal > 0:
        spread_pct = (max_modal - min_modal) / avg_modal
        if spread_pct > 0.4:
            volatility = "high"
        elif spread_pct > 0.2:
            volatility = "medium"

    sources: set[tuple[str | None, str | None, int | None]] = set()
    for p in market_prices:
        source = p.get("source")
        source_url = p.get("source_url")
        data_year = _extract_year(p.get("recorded_date"))
        if source or source_url or data_year:
            sources.add((source, source_url, data_year))

    provenance_entries = []
    if sources:
        for s_name, s_url, s_yr in sources:
            provenance_entries.append(
                {
                    "dataset_name": "Agmarknet / Mandi Prices",
                    "source": s_name or "Agmarknet / Department of Agriculture",
                    "source_url": s_url,
                    "data_year": s_yr,
                    "record_count": len(market_prices),
                    "confidence_score": "high",
                }
            )
    else:
        provenance_entries.append(
            {
                "dataset_name": "Agmarknet / Mandi Prices",
                "source": "Normalized Data Pipeline",
                "source_url": None,
                "data_year": None,
                "record_count": len(market_prices),
                "confidence_score": "medium",
            }
        )

    return {
        "average_modal_price": avg_modal,
        "min_modal_price": min_modal,
        "max_modal_price": max_modal,
        "commodity_coverage_count": len(commodities),
        "prices_analyzed_count": len(market_prices),
        "price_volatility": volatility,
        "provenance": provenance_entries,
    }
