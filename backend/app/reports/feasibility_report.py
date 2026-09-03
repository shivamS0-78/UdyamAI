"""
Feasibility Report Data Builder for UdyamAI.
Assembles structured report dictionaries from database models for PDF generation.
"""

from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.analysis import AIAnalysis, AnalysisRun, FeasibilityAnalysis
from app.models.business import BusinessCategory
from app.models.finance import FinancialAnalysis
from app.models.location import Village
from app.models.market import MarketAnalysis
from app.models.scheme import Scheme, SchemeMatch
from app.schemes.matcher import estimate_subsidy_for_match


def assemble_feasibility_report_data(db: Session, analysis_run_id: UUID) -> dict[str, Any]:
    """
    Fetches DB models for an analysis run and constructs a clean data dictionary for PDF rendering.
    """
    run = db.get(AnalysisRun, analysis_run_id)
    if not run:
        raise ValueError(f"Analysis run {analysis_run_id} not found.")

    village = db.get(Village, run.location_id) if run.location_id else None
    category = (
        db.get(BusinessCategory, run.business_category_id) if run.business_category_id else None
    )

    feasibility = db.exec(
        select(FeasibilityAnalysis).where(FeasibilityAnalysis.analysis_run_id == analysis_run_id)
    ).first()

    ai_analysis = db.exec(
        select(AIAnalysis).where(AIAnalysis.analysis_run_id == analysis_run_id)
    ).first()

    mkt_analysis = db.exec(
        select(MarketAnalysis).where(MarketAnalysis.analysis_run_id == analysis_run_id)
    ).first()

    matches = db.exec(
        select(SchemeMatch).where(SchemeMatch.analysis_run_id == analysis_run_id)
    ).all()

    fin_analysis = db.exec(
        select(FinancialAnalysis).where(FinancialAnalysis.analysis_run_id == analysis_run_id)
    ).first()

    schemes_data = []
    for match in matches:
        sch = db.get(Scheme, match.scheme_id)
        if not sch:
            continue
        proj_cost = match.estimated_project_cost or 0.0
        subsidy = estimate_subsidy_for_match(db, sch.id, proj_cost)
        subsidy_pct = round((subsidy / proj_cost) * 100, 1) if proj_cost > 0 and subsidy > 0 else 0
        schemes_data.append(
            {
                "name": sch.name,
                "subsidy_percentage": subsidy_pct,
                "match_status": match.match_status,
                "estimated_loan": match.estimated_loan_amount,
            }
        )

    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    if feasibility:
        if isinstance(feasibility.strengths, dict):
            strengths = feasibility.strengths.get("indicators", [])
        if isinstance(feasibility.weaknesses, dict):
            weaknesses = feasibility.weaknesses.get("indicators", [])
        if isinstance(feasibility.opportunities, dict):
            opportunities = feasibility.opportunities.get("indicators", [])
        if isinstance(feasibility.threats, dict):
            threats = feasibility.threats.get("indicators", [])

    summary = (
        ai_analysis.summary if ai_analysis else (feasibility.recommendation if feasibility else "")
    )
    recommendation = (
        ai_analysis.recommendation
        if ai_analysis
        else (feasibility.recommendation if feasibility else "")
    )
    next_steps = []
    if ai_analysis and isinstance(ai_analysis.business_plan, dict):
        next_steps = ai_analysis.business_plan.get("next_steps", [])

    category_name = category.name if category else ""
    location_name = village.name if village else ""

    avail_cap = run.available_capital or 0.0
    desired_cost = getattr(run, "desired_project_cost", 0.0) or 0.0
    loan_amt = (
        fin_analysis.calculated_loan
        if fin_analysis and fin_analysis.calculated_loan is not None
        else max(0.0, desired_cost - avail_cap)
    )
    monthly_emi = (
        fin_analysis.monthly_emi if fin_analysis and fin_analysis.monthly_emi is not None else 0.0
    )
    monthly_surplus = (
        mkt_analysis.market_reach_estimate
        if mkt_analysis and mkt_analysis.market_reach_estimate
        else 0.0
    )

    return {
        "title": f"{category_name} Feasibility Report"
        if category_name
        else "UdyamAI Feasibility Report",
        "location_name": location_name,
        "category_name": category_name,
        "generated_at": run.created_at.strftime("%Y-%m-%d") if run.created_at else "",
        "overall_score": feasibility.overall_score
        if feasibility and feasibility.overall_score is not None
        else 0.0,
        "market_score": feasibility.market_score
        if feasibility and feasibility.market_score is not None
        else 0.0,
        "financial_score": feasibility.financial_score
        if feasibility and feasibility.financial_score is not None
        else 0.0,
        "competition_score": feasibility.competition_score
        if feasibility and feasibility.competition_score is not None
        else 0.0,
        "infrastructure_score": feasibility.infrastructure_score
        if feasibility and feasibility.infrastructure_score is not None
        else 0.0,
        "risk_score": feasibility.risk_score
        if feasibility and feasibility.risk_score is not None
        else 0.0,
        "summary": summary,
        "recommendation": recommendation,
        "swot": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats,
        },
        "financial_summary": {
            "project_cost": desired_cost,
            "available_capital": avail_cap,
            "loan_amount": loan_amt,
            "monthly_surplus": monthly_surplus,
            "monthly_emi": monthly_emi,
            "net_monthly_surplus": max(0.0, monthly_surplus - monthly_emi),
        },
        "schemes": schemes_data,
        "next_steps": next_steps,
    }
