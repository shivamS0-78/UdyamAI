from __future__ import annotations

import json
from typing import Any


def _safe_get(obj: Any, *path: str) -> Any:
    current = obj
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            return dumped if isinstance(dumped, dict) else {}
        except Exception:
            pass
    if hasattr(value, "dict"):
        try:
            dumped = value.dict()
            return dumped if isinstance(dumped, dict) else {}
        except Exception:
            pass
    return {}


def build(
    analysis_context: dict,
    include_raw_context: bool = False,
    max_raw_context_length: int = 2000,
    rag_response: Any | None = None,
) -> dict:
    """Turn verified backend AnalysisContext into a compact prompt payload.

    This keeps the AI provider grounded in backend calculations and avoids exposing
    raw database or non-user-facing implementation details.
    """
    context = _as_dict(analysis_context)
    location = _as_dict(context.get("location"))
    business = _as_dict(context.get("business"))
    financial = _as_dict(context.get("financial"))
    market = _as_dict(context.get("market"))
    competition = _as_dict(context.get("competition"))
    schemes = context.get("schemes", []) or []
    feasibility = _as_dict(context.get("feasibility"))
    risks = context.get("risks", []) or []
    language = context.get("language") or "en"

    village = _as_dict(location.get("village"))
    district = _as_dict(location.get("district"))
    taluka = _as_dict(location.get("taluka"))
    category = _as_dict(business.get("category"))

    summary = {
        "location": {
            "village": village.get("name") or "N/A",
            "taluka": taluka.get("name") or "N/A",
            "district": district.get("name") or "N/A",
        },
        "business": {
            "category_name": category.get("name") or business.get("category_name") or "N/A",
        },
        "source_note": "Verified backend data only; no invented subsidy, price, or feasibility values.",
    }

    scheme_summary = []
    for scheme in schemes:
        scheme_obj = _as_dict(scheme)
        scheme_meta = _as_dict(scheme_obj.get("scheme"))
        scheme_summary.append(
            {
                "name": scheme_meta.get("name") or "Unnamed scheme",
                "match_status": scheme_obj.get("match_status"),
                "match_score": scheme_obj.get("match_score"),
                "verification_required": scheme_obj.get("verification_required", True),
            }
        )

    # Process RAG evidence response if provided
    rag_status = None
    rag_evidence: list[dict[str, Any]] = []
    if rag_response is not None:
        if hasattr(rag_response, "status"):
            rag_status = rag_response.status
        elif isinstance(rag_response, dict):
            rag_status = rag_response.get("status")

        raw_evidence = getattr(rag_response, "evidence", []) or []
        if isinstance(rag_response, dict):
            raw_evidence = rag_response.get("evidence", []) or []

        for item in raw_evidence:
            item_dict = _as_dict(item)
            source_meta = _as_dict(item_dict.get("source"))
            rag_evidence.append(
                {
                    "chunk_id": str(item_dict.get("chunk_id", "")),
                    "text": item_dict.get("text", ""),
                    "score": item_dict.get("score", 0.0),
                    "source": {
                        "document_id": str(source_meta.get("document_id", "")),
                        "title": source_meta.get("title", ""),
                        "page_number": source_meta.get("page_number"),
                        "section_title": source_meta.get("section_title"),
                        "source_name": source_meta.get("source_name", ""),
                        "source_url": source_meta.get("source_url"),
                        "language": source_meta.get("language", "hi"),
                        "version": source_meta.get("version"),
                        "effective_from": source_meta.get("effective_from"),
                        "effective_until": source_meta.get("effective_until"),
                    },
                }
            )

    raw_context_val = None
    if include_raw_context:
        dumped = json.dumps(context, default=str, ensure_ascii=False)
        if len(dumped) > max_raw_context_length:
            dumped = dumped[:max_raw_context_length] + "...[truncated]"
        raw_context_val = dumped

    return {
        "language": language,
        "summary": summary,
        "location": {
            "village_name": village.get("name") or "N/A",
            "taluka_name": taluka.get("name") or "N/A",
            "district_name": district.get("name") or "N/A",
        },
        "business": {
            "category_name": category.get("name") or business.get("category_name") or "N/A",
            "model_name": _safe_get(business, "model", "name") or "N/A",
        },
        "financial": {
            "available_capital": financial.get("available_capital"),
            "required_contribution": financial.get("required_contribution"),
            "shortfall": financial.get("shortfall"),
            "desired_project_cost": financial.get("desired_project_cost"),
            "feasible_project_cost": financial.get("feasible_project_cost"),
            "potential_loan": financial.get("potential_loan"),
            "status": financial.get("status"),
        },
        "market": {
            "overall_market_score": market.get("overall_market_score"),
            "demand_level": market.get("demand_level"),
            "estimated_target_customers": market.get("estimated_target_customers"),
            "estimated_monthly_expenditure": market.get("estimated_monthly_expenditure"),
            "average_household_income": market.get("average_household_income"),
            "purchasing_power_index": market.get("purchasing_power_index"),
            "average_market_price": market.get("average_market_price"),
        },
        "competition": {
            "total_competitors_count": competition.get("total_competitors_count"),
            "direct_competitors_count": competition.get("direct_competitors_count"),
            "indirect_competitors_count": competition.get("indirect_competitors_count"),
            "competition_density": competition.get("competition_density"),
            "threat_level": competition.get("threat_level"),
            "nearest_competitor_distance_km": competition.get("nearest_competitor_distance_km"),
        },
        "schemes": scheme_summary,
        "feasibility": {
            "overall_score": feasibility.get("overall_score"),
            "market_score": feasibility.get("market_score"),
            "financial_score": feasibility.get("financial_score"),
            "competition_score": feasibility.get("competition_score"),
            "risk_score": feasibility.get("risk_score"),
            "recommendation": feasibility.get("recommendation"),
            "strengths": _safe_get(feasibility, "swot", "strengths") or [],
            "weaknesses": _safe_get(feasibility, "swot", "weaknesses") or [],
            "opportunities": _safe_get(feasibility, "swot", "opportunities") or [],
            "threats": _safe_get(feasibility, "swot", "threats") or [],
        },
        "risks": risks,
        "rag_status": rag_status,
        "rag_evidence": rag_evidence,
        "raw_context": raw_context_val,
    }
