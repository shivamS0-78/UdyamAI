"""Recommendation explanation utilities for the AI advisor.

These explanations are intentionally grounded in the backend's verified
feasibility outputs. The AI must not change, estimate, or invent any score.
"""

from __future__ import annotations


def _score_value(value: object) -> float | None:
    if value is None:
        return None
    val: float | None = None
    if isinstance(value, (int, float)):
        val = float(value)
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            val = float(stripped)
        except ValueError:
            return None
    else:
        return None

    if val is not None:
        if 0 < val <= 1.0:
            val = val * 100.0
        return val
    return None


def _format_score(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value:.0f}/100"


def explain(feasibility: dict) -> str:
    """Return a grounded explanation of the backend feasibility result."""
    if not isinstance(feasibility, dict) or not feasibility:
        return "The backend did not provide a valid feasibility summary, so no AI recommendation can be generated from unsupported data."

    overall = _score_value(feasibility.get("overall_score"))
    market = _score_value(feasibility.get("market_score"))
    financial = _score_value(feasibility.get("financial_score"))
    risk = _score_value(feasibility.get("risk_score"))
    recommendation = feasibility.get("recommendation") or "No recommendation provided by backend"

    summary_parts: list[str] = []

    if overall is not None:
        summary_parts.append(
            f"The backend analysis reports an overall feasibility score of {_format_score(overall)}."
        )
    else:
        summary_parts.append("The backend analysis does not provide an overall feasibility score.")

    if market is not None:
        summary_parts.append(f"The market component is scored at {_format_score(market)}.")
    if financial is not None:
        summary_parts.append(f"The financial component is scored at {_format_score(financial)}.")
    if risk is not None:
        summary_parts.append(f"The risk indicator is scored at {_format_score(risk)}.")

    summary_parts.append(f"The backend recommendation is: {recommendation}.")

    data_conf = str(feasibility.get("data_confidence", "")).lower()
    if data_conf in ("low", "insufficient"):
        summary_parts.append(
            "Note: Empirical data confidence is limited for this location, so indicators should be treated as preliminary rather than exhaustive."
        )
    elif feasibility.get("competition_data_available") is False:
        summary_parts.append(
            "Note: Zero local business records are available in the database to assess competition directly."
        )

    if overall is not None and overall >= 75:
        summary_parts.append(
            "This suggests the business appears reasonably feasible based on the verified backend analysis."
        )
    elif overall is not None and overall >= 50:
        summary_parts.append(
            "This suggests the business is viable but needs tighter financial or operational controls based on the verified backend analysis."
        )
    elif overall is not None:
        summary_parts.append(
            "This suggests the business is currently weak on the verified backend indicators and should be reviewed before moving ahead."
        )

    return " ".join(part for part in summary_parts if part)
