from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlmodel import Session, select

from app.finance.break_even import calculate_break_even_period
from app.models.analysis import AIAnalysis, AnalysisRun, FeasibilityAnalysis
from app.models.business import BusinessCategory
from app.models.finance import FinancialAnalysis
from app.models.location import District, Taluka, Village
from app.models.market import CompetitorAnalysis, MarketAnalysis
from app.models.scheme import Scheme, SchemeMatch
from app.schemas.feasibility import (
    AnalysisRunCreate,
    AnalysisStatusResponse,
    ConsolidatedAnalysisResponse,
)
from app.schemes.matcher import estimate_subsidy_for_match

_AI_UNAVAILABLE_MARKERS = (
    "ai advisory guidance is temporarily unavailable",
    "ai-generated recommendations are currently unavailable",
    "ai guidance is unavailable",
)


def _extract_indicator_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    if isinstance(value, dict):
        indicators = value.get("indicators", [])
        if isinstance(indicators, list):
            return [
                str(item).strip() for item in indicators if item is not None and str(item).strip()
            ]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _is_ai_unavailable_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in _AI_UNAVAILABLE_MARKERS)


def _normalize_ai_advice_payload(
    ai_rec: AIAnalysis | None, feas_rec: FeasibilityAnalysis | None
) -> dict:
    if not ai_rec:
        return {}

    swot = ai_rec.swot if isinstance(ai_rec.swot, dict) else {}
    opportunities_raw = ai_rec.opportunities if isinstance(ai_rec.opportunities, dict) else {}
    threats_raw = ai_rec.threats if isinstance(ai_rec.threats, dict) else {}
    business_plan = ai_rec.business_plan if isinstance(ai_rec.business_plan, dict) else {}
    pricing_strategy = ai_rec.pricing_strategy if isinstance(ai_rec.pricing_strategy, dict) else {}

    strengths = _extract_indicator_list(swot.get("strengths"))
    weaknesses = _extract_indicator_list(swot.get("weaknesses"))
    opportunities = _extract_indicator_list(swot.get("opportunities")) or _extract_indicator_list(
        opportunities_raw.get("advice")
    )
    threats = _extract_indicator_list(swot.get("threats")) or _extract_indicator_list(
        threats_raw.get("risks")
    )

    if feas_rec:
        strengths = strengths or _extract_indicator_list(feas_rec.strengths)
        weaknesses = weaknesses or _extract_indicator_list(feas_rec.weaknesses)
        opportunities = opportunities or _extract_indicator_list(feas_rec.opportunities)
        threats = threats or _extract_indicator_list(feas_rec.threats)

    recommendations = _extract_indicator_list(business_plan.get("next_steps"))
    financial_advice = _extract_indicator_list(pricing_strategy.get("financial_advice"))

    summary = ai_rec.summary or ""
    if _is_ai_unavailable_text(summary) and feas_rec and feas_rec.recommendation:
        summary = (
            f"Verified feasibility analysis completed with an overall score of "
            f"{feas_rec.overall_score:.0f}/100. Review the structured recommendations below."
            if feas_rec.overall_score is not None
            else "Verified feasibility analysis completed. Review the structured recommendations below."
        )

    return {
        "summary": summary,
        "recommendation": ai_rec.recommendation,
        "recommendations": recommendations,
        "reasoning": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
        "financial_advice": financial_advice,
        "swot": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats,
        },
        "confidence": ai_rec.confidence,
        "model_name": ai_rec.model_name,
        "rag_status": "success"
        if ai_rec.model_name not in (None, "unavailable")
        else "no_relevant_evidence",
    }


def _build_risks_payload(ai_data: dict, feas_rec: FeasibilityAnalysis | None) -> list[dict]:
    risks_data: list[dict] = []
    raw_ai_risks = ai_data.get("risks") if ai_data else None
    if isinstance(raw_ai_risks, dict):
        raw_ai_risks = raw_ai_risks.get("risks", [])

    # Collect AI financial advice for mitigation suggestions
    financial_advice_list: list[str] = []
    if ai_data:
        pricing_strategy = ai_data.get("pricing_strategy")
        if isinstance(pricing_strategy, dict):
            financial_advice_list = pricing_strategy.get("financial_advice", []) or []
        if not financial_advice_list:
            financial_advice_list = ai_data.get("financial_advice", []) or []

    def _suggest_mitigation(risk_text: str, category: str) -> str:
        """Generate a context-aware mitigation suggestion from available AI advice."""
        risk_lower = risk_text.lower()
        # Try to match AI financial advice to the risk
        for advice in financial_advice_list:
            if any(
                keyword in risk_lower
                for keyword in ("seasonal", "supply", "volatility", "crop", "harvest")
            ) and any(
                keyword in advice.lower()
                for keyword in ("buffer", "working.capital", "reserve", "seasonal")
            ):
                return advice
            if any(
                keyword in risk_lower
                for keyword in ("subsidy", "eligibility", "scheme", "documents")
            ) and any(
                keyword in advice.lower()
                for keyword in ("subsidy", "scheme", "eligibility", "document")
            ):
                return advice
        # Fallback: generic mitigation based on category
        if "financial" in category.lower() or "cash" in risk_lower:
            return "Maintain adequate working capital reserves and monitor cash flow monthly."
        if "market" in category.lower() or "demand" in risk_lower:
            return "Diversify customer base and monitor local demand indicators regularly."
        if "competition" in category.lower() or "competitor" in risk_lower:
            return "Differentiate service quality and build customer loyalty programs."
        if "seasonal" in risk_lower or "supply" in risk_lower:
            return "Maintain working-capital buffers and diversify supply sources across seasons."
        return "Monitor this risk factor and review with financial advisor before committing."

    if isinstance(raw_ai_risks, list):
        for item in raw_ai_risks:
            if isinstance(item, str) and item.strip() and not _is_ai_unavailable_text(item):
                risks_data.append(
                    {
                        "risk_factor": item,
                        "factor": item,
                        "category": "Operational & Market Risk",
                        "level": "Medium",
                        "mitigation": _suggest_mitigation(item, "Operational & Market Risk"),
                    }
                )
            elif isinstance(item, dict):
                factor = (
                    item.get("risk_factor")
                    or item.get("factor")
                    or item.get("risk_type")
                    or "Operational Risk"
                )
                if _is_ai_unavailable_text(str(factor)):
                    continue
                risks_data.append(
                    {
                        "risk_factor": factor,
                        "factor": factor,
                        "category": item.get("category") or "Operating Risk",
                        "level": item.get("level") or item.get("severity") or "Medium",
                        "mitigation": item.get("mitigation")
                        or item.get("evidence")
                        or _suggest_mitigation(
                            str(factor), item.get("category") or "Operating Risk"
                        ),
                    }
                )

    if not risks_data and feas_rec:
        threat_items = _extract_indicator_list(feas_rec.threats)
        weakness_items = _extract_indicator_list(feas_rec.weaknesses)
        for idx, threat in enumerate(threat_items + weakness_items):
            risks_data.append(
                {
                    "risk_factor": threat,
                    "factor": threat[:60],
                    "category": "Market & Enterprise Risk",
                    "level": "Medium" if idx < len(threat_items) else "Low",
                    "mitigation": _suggest_mitigation(threat, "Market & Enterprise Risk"),
                }
            )

    return risks_data


class AnalysisService:
    @staticmethod
    def verify_location(db: Session, location_ref: UUID | str | None) -> UUID | None:
        if location_ref is None:
            return None

        village: Village | None = None
        if isinstance(location_ref, UUID):
            village = db.get(Village, location_ref)
        else:
            # Try UUID string parsing first
            try:
                parsed_uuid = UUID(str(location_ref))
                village = db.get(Village, parsed_uuid)
            except ValueError:
                pass

            if not village:
                statement = select(Village).where(Village.lgd_code == str(location_ref))
                village = db.exec(statement).first()

            if not village:
                statement = select(Village).where(Village.name == str(location_ref))
                village = db.exec(statement).first()

        if not village:
            raise HTTPException(
                status_code=404,
                detail=f"Location with identifier '{location_ref}' not found",
            )
        return village.id

    @staticmethod
    def verify_business_category(db: Session, category_ref: UUID | str | None) -> UUID | None:
        if category_ref is None:
            return None

        category: BusinessCategory | None = None
        if isinstance(category_ref, UUID):
            category = db.get(BusinessCategory, category_ref)
        else:
            try:
                parsed_uuid = UUID(str(category_ref))
                category = db.get(BusinessCategory, parsed_uuid)
            except ValueError:
                pass

            if not category:
                statement = select(BusinessCategory).where(
                    BusinessCategory.name == str(category_ref)
                )
                category = db.exec(statement).first()

        if not category:
            raise HTTPException(
                status_code=404,
                detail=f"Business category with identifier '{category_ref}' not found",
            )
        return category.id

    @staticmethod
    def create_analysis_run(db: Session, run_data: AnalysisRunCreate) -> AnalysisRun:
        # Step 1: Input validated via AnalysisRunCreate schema
        # Step 2: Verify location
        raw_location = run_data.location_id or run_data.village_id
        resolved_location_id = AnalysisService.verify_location(db, raw_location)

        # Step 3: Verify business category
        resolved_category_id = AnalysisService.verify_business_category(
            db, run_data.business_category_id
        )

        # Step 4: Create AnalysisRun
        user_id = run_data.user_id or uuid4()
        db_run = AnalysisRun(
            user_id=user_id,
            location_id=resolved_location_id,
            business_category_id=resolved_category_id,
            available_capital=run_data.available_capital,
            status="created",
        )
        db.add(db_run)
        db.commit()
        db.refresh(db_run)
        return db_run

    @staticmethod
    def get_analysis_run(db: Session, run_id: UUID) -> AnalysisRun | None:
        return db.get(AnalysisRun, run_id)

    @staticmethod
    def get_analysis_run_status(db: Session, run_id: UUID) -> AnalysisStatusResponse | None:
        db_run = db.get(AnalysisRun, run_id)
        if not db_run:
            return None

        progress = 10
        step = "created"

        if db_run.status == "pending":
            progress = 25
            step = "queued"
        elif db_run.status == "running":
            progress = 65
            step = "evaluating_rules"
        elif db_run.status == "completed":
            progress = 100
            step = "completed"
        elif db_run.status == "failed":
            progress = 0
            step = "failed"

        return AnalysisStatusResponse(
            id=db_run.id,
            analysis_id=db_run.id,
            status=db_run.status,
            progress_percentage=progress,
            current_step=step,
            created_at=db_run.created_at,
            completed_at=db_run.completed_at,
            error_message=None,
        )

    @staticmethod
    def get_consolidated_analysis(db: Session, run_id: UUID) -> ConsolidatedAnalysisResponse | None:
        db_run = db.get(AnalysisRun, run_id)
        if not db_run:
            return None

        # Location details
        village = db.get(Village, db_run.location_id) if db_run.location_id else None
        taluka = db.get(Taluka, village.taluka_id) if village and village.taluka_id else None
        district = db.get(District, taluka.district_id) if taluka and taluka.district_id else None
        location_data = (
            {
                "village_id": str(village.id),
                "village_name": village.name,
                "taluka_name": taluka.name if taluka else None,
                "district_name": district.name if district else None,
                "latitude": village.latitude,
                "longitude": village.longitude,
            }
            if village
            else {}
        )

        # Business details
        category = (
            db.get(BusinessCategory, db_run.business_category_id)
            if db_run.business_category_id
            else None
        )
        business_data = (
            {
                "category_id": str(category.id),
                "category_name": category.name,
                "description": getattr(category, "description", None),
            }
            if category
            else {}
        )

        # Financial analysis
        fin_rec = db.exec(
            select(FinancialAnalysis).where(FinancialAnalysis.analysis_run_id == run_id)
        ).first()
        fin_data = (
            {
                "available_capital": fin_rec.available_capital,
                "required_contribution": fin_rec.required_contribution,
                "desired_project_cost": fin_rec.desired_project_cost,
                "feasible_project_cost": fin_rec.feasible_project_cost,
                "calculated_loan": fin_rec.calculated_loan,
                "monthly_emi": fin_rec.monthly_emi,
                "total_interest": fin_rec.total_interest,
                "total_repayment": fin_rec.total_repayment,
                "working_capital": fin_rec.working_capital,
                "monthly_revenue": fin_rec.monthly_revenue,
                "monthly_operating_cost": fin_rec.monthly_operating_cost,
                "monthly_profit": fin_rec.monthly_profit,
                "break_even_months": fin_rec.break_even_months,
                "repayment_capacity": fin_rec.repayment_capacity,
                "interest_rate": fin_rec.interest_rate,
                "tenure_months": fin_rec.tenure_months,
                "margin_gap": fin_rec.margin_gap,
            }
            if fin_rec
            else {"available_capital": db_run.available_capital}
        )

        # Market & Competition analysis
        mkt_rec = db.exec(
            select(MarketAnalysis).where(MarketAnalysis.analysis_run_id == run_id)
        ).first()
        mkt_data = (
            {
                "population_estimate": mkt_rec.population_estimate,
                "household_estimate": mkt_rec.household_estimate,
                "target_customers": mkt_rec.market_reach_estimate,
                "demand_indicators": mkt_rec.demand_indicators,
                "pricing_indicators": mkt_rec.pricing_indicators,
            }
            if mkt_rec
            else {}
        )

        comp_rec = db.exec(
            select(CompetitorAnalysis).where(CompetitorAnalysis.analysis_run_id == run_id)
        ).first()
        comp_data = (
            {
                "competitor_count": comp_rec.competitor_count,
                "competition_density": comp_rec.competition_density,
                "distribution": comp_rec.competitor_distribution,
            }
            if comp_rec
            else {}
        )

        # Scheme matches
        matches = db.exec(select(SchemeMatch).where(SchemeMatch.analysis_run_id == run_id)).all()
        schemes_data = []
        max_subsidy_est = 0.0
        for m in matches:
            sch_obj = db.get(Scheme, m.scheme_id) if m.scheme_id else None
            s_name = (
                sch_obj.name if sch_obj and sch_obj.name else "Government Welfare & Subsidy Scheme"
            )
            s_desc = (
                sch_obj.description
                if sch_obj and sch_obj.description
                else "Capital subsidy and financial support scheme for micro-enterprises."
            )
            s_agency = sch_obj.agency_name if sch_obj else None
            s_url = sch_obj.official_url if sch_obj else None

            proj_cost = m.estimated_project_cost or 0
            sub_est = estimate_subsidy_for_match(db, m.scheme_id, proj_cost) if m.scheme_id else 0.0
            if sub_est > max_subsidy_est:
                max_subsidy_est = sub_est

            schemes_data.append(
                {
                    "scheme_id": str(m.scheme_id),
                    "scheme_name": s_name,
                    "name": s_name,
                    "description": s_desc,
                    "agency_name": s_agency,
                    "official_url": s_url,
                    "match_status": str(
                        m.match_status.value if hasattr(m.match_status, "value") else m.match_status
                    ),
                    "match_score": m.match_score,
                    "estimated_subsidy_amount": sub_est,
                    "estimated_loan_amount": m.estimated_loan_amount,
                    "estimated_project_cost": m.estimated_project_cost,
                    "matched_conditions": m.matched_conditions or {},
                }
            )

        # ------------------------------------------------------------------
        # Enrich fin_data with sector, market & subsidy-driven estimates
        # ------------------------------------------------------------------
        feasible_cost = fin_data.get("feasible_project_cost") or 0.0
        pricing = mkt_data.get("pricing_indicators") or {}
        target_customers = mkt_data.get("target_customers") or 0
        avg_price = (
            pricing.get("average_market_price")
            or pricing.get("average_modal_price")
            or pricing.get("average_price")
        )

        # Sector / category benchmark parameters for micro-enterprises
        # (rev_ratio: monthly revenue as % of feasible project cost)
        # (cost_ratio: monthly operating costs as % of monthly revenue)
        cat_name = (business_data.get("category_name") or "").lower()
        cat_desc = (business_data.get("description") or "").lower()
        text_context = f"{cat_name} {cat_desc}"

        if any(
            k in text_context
            for k in ["retail", "grocery", "kirana", "shop", "store", "trading", "mart"]
        ):
            bench = {"rev_ratio": 0.35, "cost_ratio": 0.78}
        elif any(
            k in text_context
            for k in ["dairy", "milk", "cattle", "livestock", "poultry", "goat", "animal"]
        ):
            bench = {"rev_ratio": 0.25, "cost_ratio": 0.65}
        elif any(
            k in text_context
            for k in ["service", "repair", "salon", "tailor", "mechanic", "digital"]
        ):
            bench = {"rev_ratio": 0.28, "cost_ratio": 0.48}
        elif any(
            k in text_context
            for k in ["manufactur", "process", "mill", "oil", "textile", "craft", "fabric"]
        ):
            bench = {"rev_ratio": 0.20, "cost_ratio": 0.58}
        elif any(
            k in text_context
            for k in ["food", "hotel", "canteen", "restaurant", "bakery", "sweet", "snack"]
        ):
            bench = {"rev_ratio": 0.32, "cost_ratio": 0.70}
        else:
            bench = {"rev_ratio": 0.24, "cost_ratio": 0.62}

        # Market demand adjustment (score 0-100)
        demand_ind = mkt_data.get("demand_indicators") or {}
        raw_demand_score = demand_ind.get("score") or demand_ind.get("demand_score")
        if raw_demand_score is not None:
            try:
                ds_val = float(raw_demand_score)
                demand_mult = 0.85 + (ds_val / 100.0) * 0.30
            except (ValueError, TypeError):
                demand_mult = 1.0
        else:
            demand_mult = 1.0

        # Competition density adjustment
        comp_count = comp_data.get("competitor_count")
        if comp_count is not None:
            try:
                cc_val = float(comp_count)
                comp_mult = max(0.85, min(1.10, 1.05 - (cc_val * 0.02)))
            except (ValueError, TypeError):
                comp_mult = 1.0
        else:
            comp_mult = 1.0

        market_mult = round(demand_mult * comp_mult, 3)

        est_monthly_rev = fin_data.get("monthly_revenue")
        if est_monthly_rev is None and feasible_cost > 0:
            if target_customers > 0 and avg_price and avg_price > 0:
                est_monthly_rev = round(
                    target_customers * float(avg_price) * 0.3 * 4 * comp_mult, 2
                )
            else:
                est_monthly_rev = round(feasible_cost * bench["rev_ratio"] * market_mult, 2)

        est_monthly_cost = fin_data.get("monthly_operating_cost")
        if est_monthly_cost is None and est_monthly_rev is not None:
            est_monthly_cost = round(est_monthly_rev * bench["cost_ratio"], 2)

        est_monthly_profit = fin_data.get("monthly_profit")
        if (
            est_monthly_profit is None
            and est_monthly_rev is not None
            and est_monthly_cost is not None
        ):
            est_monthly_profit = round(est_monthly_rev - est_monthly_cost, 2)

        est_break_even = fin_data.get("break_even_months")
        if (
            est_break_even is None
            and feasible_cost > 0
            and est_monthly_profit
            and est_monthly_profit > 0
        ):
            est_break_even = calculate_break_even_period(
                project_cost=feasible_cost,
                monthly_profit=est_monthly_profit,
                subsidy_amount=max_subsidy_est,
            )

        est_repayment_capacity = fin_data.get("repayment_capacity")
        est_emi = fin_data.get("monthly_emi") or 0.0
        if est_repayment_capacity is None and est_monthly_rev is not None and est_emi > 0:
            est_repayment_capacity = round(
                (est_monthly_rev - (est_monthly_cost or 0.0)) / est_emi, 2
            )

        fin_data["monthly_revenue"] = est_monthly_rev
        fin_data["monthly_operating_cost"] = est_monthly_cost
        fin_data["monthly_profit"] = est_monthly_profit
        fin_data["break_even_months"] = est_break_even
        fin_data["repayment_capacity"] = est_repayment_capacity
        fin_data["subsidy_estimated"] = max_subsidy_est if max_subsidy_est > 0 else None

        # Feasibility analysis
        feas_rec = db.exec(
            select(FeasibilityAnalysis).where(FeasibilityAnalysis.analysis_run_id == run_id)
        ).first()
        feas_data = (
            {
                "overall_score": feas_rec.overall_score,
                "market_score": feas_rec.market_score,
                "financial_score": feas_rec.financial_score,
                "competition_score": feas_rec.competition_score,
                "infrastructure_score": feas_rec.infrastructure_score,
                "risk_score": feas_rec.risk_score,
                "recommendation": feas_rec.recommendation,
                "strengths": feas_rec.strengths,
                "weaknesses": feas_rec.weaknesses,
                "opportunities": feas_rec.opportunities,
                "threats": feas_rec.threats,
                "swot": {
                    "strengths": _extract_indicator_list(feas_rec.strengths),
                    "weaknesses": _extract_indicator_list(feas_rec.weaknesses),
                    "opportunities": _extract_indicator_list(feas_rec.opportunities),
                    "threats": _extract_indicator_list(feas_rec.threats),
                },
            }
            if feas_rec
            else {}
        )

        ai_rec = db.exec(select(AIAnalysis).where(AIAnalysis.analysis_run_id == run_id)).first()
        ai_data = _normalize_ai_advice_payload(ai_rec, feas_rec) if ai_rec else {}
        if ai_rec and not ai_data:
            ai_data = {
                "summary": ai_rec.summary,
                "recommendation": ai_rec.recommendation,
                "swot": ai_rec.swot,
                "opportunities": ai_rec.opportunities,
                "threats": ai_rec.threats,
                "risks": ai_rec.risks,
                "pricing_strategy": ai_rec.pricing_strategy,
                "business_plan": ai_rec.business_plan,
                "confidence": ai_rec.confidence,
            }

        risks_data = _build_risks_payload(
            {"risks": ai_rec.risks} if ai_rec else {},
            feas_rec,
        )

        return ConsolidatedAnalysisResponse(
            analysis_id=db_run.id,
            status=db_run.status,
            created_at=db_run.created_at,
            completed_at=db_run.completed_at,
            location=location_data,
            business=business_data,
            financial=fin_data,
            market=mkt_data,
            competition=comp_data,
            schemes=schemes_data,
            feasibility=feas_data,
            risks=risks_data,
            ai_advice=ai_data,
        )
