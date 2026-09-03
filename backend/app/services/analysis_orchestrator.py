"""Analysis Orchestrator for UdyamAI.

Coordinates the end-to-end multi-step analysis pipeline:
1. Validate input
2. Create AnalysisRun
3. Fetch location
4. Fetch business category
5. Run finance
6. Run market analysis
7. Run competition analysis
8. Obtain scheme matches
9. Run feasibility
10. Build AnalysisContext
11. Hand context to AI Advisor
12. Save final results
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlmodel import Session, select

from app.ai import advisor
from app.config import settings
from app.market.risks import (
    HIGH_COMPETITOR_DENSITY_THRESHOLD,
    VERY_HIGH_COMPETITOR_DENSITY_THRESHOLD,
)
from app.models.analysis import AIAnalysis, AnalysisRun, FeasibilityAnalysis
from app.models.business import BusinessCategory
from app.models.location import District, Taluka, Village
from app.models.market import CompetitorAnalysis, MarketAnalysis
from app.models.report import Report
from app.models.user import Profile
from app.schemas.ai import (
    AnalysisContext,
    BusinessContext,
    CompetitionContext,
    FeasibilityContext,
    LocationContext,
    MarketContext,
    RiskContext,
    SchemeMatchContext,
)
from app.schemas.business import BusinessCategoryResponse
from app.schemas.feasibility import AnalysisRunCreate
from app.schemas.finance import FinanceCalculateRequest
from app.schemas.location import DistrictResponse, TalukaResponse, VillageResponse
from app.schemas.scheme import SchemeResponse
from app.schemes.matcher import match_schemes_for_analysis
from app.services.analysis_service import AnalysisService
from app.services.feasibility_service import FeasibilityService
from app.services.finance_service import FinanceService
from app.services.market_service import MarketService
from app.services.scheme_service import SchemeService

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"en", "hi", "mr"}


def _get_comp_count(res: Any) -> Any:
    if res is None:
        return 0
    t_cnt = getattr(res, "total_competitors_count", None)
    if t_cnt is not None and type(t_cnt).__name__ != "MagicMock":
        return t_cnt
    c_cnt = getattr(res, "competitor_count", None)
    if c_cnt is not None and type(c_cnt).__name__ != "MagicMock":
        return c_cnt
    return t_cnt if t_cnt is not None else (c_cnt if c_cnt is not None else 0)


class AnalysisOrchestrator:
    """Orchestrates the central 12-step analysis workflow with strict transaction boundaries."""

    @staticmethod
    def run_analysis_pipeline(db: Session, run_data: AnalysisRunCreate) -> AnalysisRun:
        logger.info("Starting Analysis Orchestrator pipeline")

        category: BusinessCategory | None = None
        village: Village | None = None
        taluka: Taluka | None = None
        district: District | None = None

        # -------------------------------------------------------------
        # Step 1: Validate input
        # -------------------------------------------------------------
        raw_location = run_data.location_id or run_data.village_id
        if not raw_location:
            raise HTTPException(
                status_code=400,
                detail="Location identifier (location_id or village_id) is required",
            )

        location_id = AnalysisService.verify_location(db, raw_location)
        category_id = None
        if run_data.business_category_id:
            category_id = AnalysisService.verify_business_category(
                db, run_data.business_category_id
            )

        # Handle user profile (auto-create guest/demo profile if unauthenticated or not found)
        user_id = run_data.user_id
        if user_id is None:
            guest_profile = db.exec(
                select(Profile).where(Profile.name == "Guest Entrepreneur")
            ).first()
            if not guest_profile:
                guest_profile = Profile(
                    auth_user_id=uuid4(),
                    name="Guest Entrepreneur",
                    preferred_language="en",
                )
                db.add(guest_profile)
                db.commit()
                db.refresh(guest_profile)
            user_id = guest_profile.id
        else:
            profile = db.get(Profile, user_id)
            if not profile:
                profile = Profile(
                    id=user_id,
                    auth_user_id=uuid4(),
                    name="Entrepreneur User",
                    preferred_language="en",
                )
                db.add(profile)
                db.commit()
                db.refresh(profile)

        # -------------------------------------------------------------
        # Step 2: Create AnalysisRun
        # -------------------------------------------------------------
        db_run = AnalysisRun(
            user_id=user_id,
            location_id=location_id,
            business_category_id=category_id,
            available_capital=run_data.available_capital or 0.0,
            status="running",
        )
        db.add(db_run)
        db.commit()
        db.refresh(db_run)

        try:
            # -------------------------------------------------------------
            # Step 3: Fetch location
            # -------------------------------------------------------------
            village = db.get(Village, location_id)
            if not village:
                raise HTTPException(
                    status_code=404,
                    detail=f"Village with ID {location_id} not found",
                )

            taluka = db.get(Taluka, village.taluka_id) if village.taluka_id else None
            if not taluka and village.taluka_id:
                raise HTTPException(
                    status_code=404,
                    detail=f"Taluka with ID {village.taluka_id} not found",
                )

            district = (
                db.get(District, taluka.district_id) if taluka and taluka.district_id else None
            )
            if not district and taluka and taluka.district_id:
                raise HTTPException(
                    status_code=404,
                    detail=f"District associated with Taluka {taluka.id} not found",
                )

            # -------------------------------------------------------------
            # Step 4: Fetch business category
            # -------------------------------------------------------------
            category = db.get(BusinessCategory, category_id) if category_id else None
            if not category:
                raise HTTPException(
                    status_code=400,
                    detail="Business category is required for analysis. Please specify business_category_id.",
                )

            # -------------------------------------------------------------
            # Step 5: Run finance
            # -------------------------------------------------------------
            desired_cost = run_data.desired_project_cost or 200_000.0
            avail_cap = run_data.available_capital or 50_000.0

            db_scheme_matches = match_schemes_for_analysis(
                db,
                analysis_run_id=db_run.id,
                business_category=category,
                district=district,
                desired_project_cost=desired_cost,
                available_capital=avail_cap,
            )

            best_match = db_scheme_matches[0] if db_scheme_matches else None
            best_rule = (
                SchemeService.get_latest_rule(db, best_match.scheme_id) if best_match else None
            )

            finance_req = FinanceCalculateRequest(
                desired_project_cost=desired_cost,
                available_capital=avail_cap,
                scheme_id=best_match.scheme_id if best_match else None,
                loan_percent=best_rule.loan_percent
                if best_rule and best_rule.loan_percent is not None
                else None,
                interest_rate=best_rule.interest_rate
                if best_rule and best_rule.interest_rate is not None
                else settings.DEFAULT_INTEREST_RATE,
                tenure_months=best_rule.tenure_months
                if best_rule and best_rule.tenure_months is not None
                else settings.DEFAULT_TENURE_MONTHS,
                moratorium_months=best_rule.moratorium_months
                if best_rule and best_rule.moratorium_months is not None
                else 0,
                beneficiary_contribution_percent=(
                    best_rule.beneficiary_contribution_percent
                    if best_rule and best_rule.beneficiary_contribution_percent is not None
                    else settings.DEFAULT_BENEFICIARY_CONTRIBUTION_PERCENT
                ),
                analysis_run_id=db_run.id,
            )
            financial_calc = FinanceService.calculate_finance(finance_req, session=db)

            # -------------------------------------------------------------
            # Step 6: Run market analysis
            # -------------------------------------------------------------
            market_location_res = MarketService.analyze_village_market(
                db,
                village_id=village.id,
                business_category_id=category.id,
                radii_km=[10.0],
            )
            radius_results = None
            if hasattr(market_location_res, "radius_results") and isinstance(
                market_location_res.radius_results, list
            ):
                radius_results = market_location_res.radius_results
            elif hasattr(market_location_res, "radius_analyses") and isinstance(
                market_location_res.radius_analyses, list
            ):
                radius_results = market_location_res.radius_analyses
            else:
                radius_results = getattr(market_location_res, "radius_analyses", None) or getattr(
                    market_location_res, "radius_results", None
                )

            if not radius_results:
                raise HTTPException(
                    status_code=422,
                    detail="Market analysis returned no radius results for the given location.",
                )
            market_res = radius_results[0]

            # -------------------------------------------------------------
            # Step 7: Run competition analysis
            # -------------------------------------------------------------
            competition_res = MarketService.analyze_competition_for_location(
                db,
                village_id=village.id,
                business_category_id=category.id,
                radius_km=10.0,
            )

            # -------------------------------------------------------------
            # Step 8: Scheme matches already computed during finance setup
            # -------------------------------------------------------------
            if not db_scheme_matches:
                logger.warning(
                    "No eligible government schemes matched for analysis run %s", db_run.id
                )

            # -------------------------------------------------------------
            # Step 9: Run feasibility
            # -------------------------------------------------------------
            est_subsidy_val = getattr(financial_calc, "potential_subsidy", 0.0) or 0.0
            feasibility_score_res = FeasibilityService.calculate_feasibility(
                db,
                village_id=village.id,
                business_category_id=category.id,
                available_capital=avail_cap,
                desired_project_cost=desired_cost,
                estimated_subsidy=est_subsidy_val,
                matched_schemes=db_scheme_matches,
            )

            # -------------------------------------------------------------
            # Step 10: Build AnalysisContext
            # -------------------------------------------------------------
            loc_context = LocationContext(
                village=VillageResponse.model_validate(village),
                district=DistrictResponse.model_validate(district) if district else None,
                taluka=TalukaResponse.model_validate(taluka) if taluka else None,
            )
            biz_context = BusinessContext(
                category=BusinessCategoryResponse.model_validate(category)
            )

            mkt_size = getattr(market_res, "market_size", None)
            if mkt_size:
                pop_est = getattr(mkt_size, "total_population_reach", None)
                hh_est = getattr(mkt_size, "household_reach", None)
                target_est = getattr(mkt_size, "estimated_target_customers", None)
            else:
                pop_est = getattr(market_res, "estimated_population_reach", None)
                hh_est = getattr(market_res, "estimated_household_reach", None)
                target_est = getattr(market_res, "estimated_target_customers", None)

            mkt_indicators = getattr(market_res, "market_indicators", {}) or {}
            demand_info = (
                mkt_indicators.get("demand", {}) if isinstance(mkt_indicators, dict) else {}
            )
            pricing_info = (
                mkt_indicators.get("pricing", {}) if isinstance(mkt_indicators, dict) else {}
            )

            demand_score_val = demand_info.get("demand_score")
            if demand_score_val is not None:
                _ds = float(demand_score_val)
                _demand_level = "High" if _ds >= 70 else ("Moderate" if _ds >= 40 else "Low")
            else:
                _demand_level = None

            mkt_context = MarketContext(
                population_estimate=pop_est,
                household_estimate=hh_est,
                market_reach_estimate=target_est,
                radius_km=10.0,
                demand_indicators={
                    "score": demand_score_val,
                    "level": _demand_level,
                    "growth_rate": demand_info.get("growth_rate"),
                },
                pricing_indicators={
                    "average_market_price": pricing_info.get("average_market_price"),
                    "price_range_min": pricing_info.get("price_range_min"),
                    "price_range_max": pricing_info.get("price_range_max"),
                },
            )

            comp_cnt = _get_comp_count(competition_res)
            raw_comp_conf = getattr(competition_res, "data_confidence", None)
            comp_conf = str(raw_comp_conf) if isinstance(raw_comp_conf, str) else None

            comp_context = CompetitionContext(
                competitor_count=comp_cnt,
                competitor_density=getattr(competition_res, "competition_density", 0.0),
                businesses_within_5km=getattr(competition_res, "businesses_within_5km", 0),
                businesses_within_10km=getattr(competition_res, "businesses_within_10km", 0),
                total_businesses_in_radius=getattr(
                    competition_res, "total_businesses_in_radius", 0
                ),
                target_category=getattr(category, "name", None) if category else None,
                data_confidence=comp_conf,
            )

            scheme_contexts = []
            for match in db_scheme_matches:
                sch_obj = SchemeService.get_scheme_by_id(db, match.scheme_id)
                if sch_obj:
                    scheme_contexts.append(
                        SchemeMatchContext(
                            scheme=SchemeResponse.model_validate(sch_obj),
                            match_status=match.match_status,
                            match_score=match.match_score,
                            matched_conditions=match.matched_conditions,
                            failed_conditions=match.failed_conditions,
                            missing_information=match.missing_information,
                            estimated_loan_amount=match.estimated_loan_amount,
                            estimated_project_cost=match.estimated_project_cost,
                            verification_required=match.verification_required,
                        )
                    )

            raw_feas_conf = getattr(feasibility_score_res, "data_confidence", None)
            feas_conf = str(raw_feas_conf) if isinstance(raw_feas_conf, str) else "high"

            mkt_avail = (
                feasibility_score_res.market_data_available
                if isinstance(getattr(feasibility_score_res, "market_data_available", None), bool)
                else True
            )
            fin_avail = (
                feasibility_score_res.financial_data_available
                if isinstance(
                    getattr(feasibility_score_res, "financial_data_available", None), bool
                )
                else True
            )
            comp_avail = (
                feasibility_score_res.competition_data_available
                if isinstance(
                    getattr(feasibility_score_res, "competition_data_available", None), bool
                )
                else True
            )
            infra_avail = (
                feasibility_score_res.infrastructure_data_available
                if isinstance(
                    getattr(feasibility_score_res, "infrastructure_data_available", None), bool
                )
                else True
            )
            risk_avail = (
                feasibility_score_res.risk_data_available
                if isinstance(getattr(feasibility_score_res, "risk_data_available", None), bool)
                else True
            )

            feasibility_context = FeasibilityContext(
                overall_score=feasibility_score_res.overall_score,
                market_score=feasibility_score_res.market_score,
                financial_score=feasibility_score_res.financial_score,
                competition_score=feasibility_score_res.competition_score,
                infrastructure_score=feasibility_score_res.infrastructure_score,
                risk_score=feasibility_score_res.risk_score,
                swot=feasibility_score_res.swot,
                confidence=feas_conf,
                data_confidence=feas_conf,
                market_data_available=mkt_avail,
                financial_data_available=fin_avail,
                competition_data_available=comp_avail,
                infrastructure_data_available=infra_avail,
                risk_data_available=risk_avail,
            )

            # Safely extract optional language property with default fallback and validation guard
            lang_attr = getattr(run_data, "language", None)
            lang_str = str(getattr(lang_attr, "value", lang_attr)) if lang_attr else "en"
            if lang_str not in SUPPORTED_LANGUAGES:
                logger.warning("Unsupported language %s, defaulting to 'en'", lang_str)
                lang_str = "en"

            # Extract risk data from the market_indicators dict inside
            # RadiusMarketAnalysisResult (it does NOT have a top-level 'risks' attr).
            _mkt_indicators = (
                market_res.market_indicators if hasattr(market_res, "market_indicators") else {}
            ) or {}
            mkt_risks = _mkt_indicators.get("risks") or {}
            raw_mkt_score = mkt_risks.get("risk_score", 0.0)
            mkt_risk_score = (
                float(raw_mkt_score) if isinstance(raw_mkt_score, (int, float)) else 0.0
            )

            raw_mkt_level = mkt_risks.get("overall_market_risk_level", "low")
            mkt_risk_level = str(raw_mkt_level) if isinstance(raw_mkt_level, str) else "low"

            # CompetitionAnalysisDetailResponse has no 'threat_level' field;
            # derive it dynamically from competitor_density.
            comp_density = 0.0
            if competition_res is not None:
                _cd = getattr(competition_res, "competitor_density", None)
                if _cd is not None:
                    try:
                        comp_density = float(_cd)
                    except (ValueError, TypeError):
                        comp_density = 0.0
            if comp_density >= VERY_HIGH_COMPETITOR_DENSITY_THRESHOLD:
                comp_threat_level = "high"
            elif comp_density >= HIGH_COMPETITOR_DENSITY_THRESHOLD:
                comp_threat_level = "medium"
            else:
                comp_threat_level = "low"

            # RiskContext.score is a normalized 0.0-1.0 severity fraction. The raw
            # sources are on wider scales (market risk engine: 0-10; competitor
            # density: competitors per km^2, unbounded), so normalize & clamp before
            # passing them on or the AnalysisContext validation crashes with a 500.
            def _normalize_risk_score(raw: float, max_raw: float) -> float:
                if max_raw <= 0.0:
                    return 0.0
                return max(0.0, min(1.0, raw / max_raw))

            mkt_risk_score_norm = _normalize_risk_score(mkt_risk_score, 10.0)
            comp_threat_max_density = (
                VERY_HIGH_COMPETITOR_DENSITY_THRESHOLD
                if VERY_HIGH_COMPETITOR_DENSITY_THRESHOLD > 0.0
                else HIGH_COMPETITOR_DENSITY_THRESHOLD
            )
            comp_threat_score = _normalize_risk_score(comp_density, comp_threat_max_density)

            risks_context = [
                RiskContext(
                    risk_type="market_risk",
                    score=mkt_risk_score_norm,
                    level=mkt_risk_level,
                ),
                RiskContext(
                    risk_type="competition_threat",
                    score=comp_threat_score,
                    level=comp_threat_level,
                ),
            ]

            analysis_context = AnalysisContext(
                location=loc_context,
                business=biz_context,
                financial=financial_calc,
                market=mkt_context,
                competition=comp_context,
                schemes=scheme_contexts,
                feasibility=feasibility_context,
                risks=risks_context,
                language=lang_str,
            )

            # -------------------------------------------------------------
            # Step 11: Hand context to AI Advisor
            # -------------------------------------------------------------
            ai_advice = advisor.generate_advice(
                analysis_context=analysis_context, language=lang_str, db=db
            )

            # -------------------------------------------------------------
            # Step 12: Save final results
            # -------------------------------------------------------------
            db_feasibility = FeasibilityAnalysis(
                analysis_run_id=db_run.id,
                market_score=feasibility_score_res.market_score,
                financial_score=feasibility_score_res.financial_score,
                competition_score=feasibility_score_res.competition_score,
                infrastructure_score=feasibility_score_res.infrastructure_score,
                risk_score=feasibility_score_res.risk_score,
                overall_score=feasibility_score_res.overall_score,
                recommendation=ai_advice.recommendation,
                strengths={
                    "indicators": getattr(
                        feasibility_score_res.swot,
                        "strengths",
                        getattr(feasibility_score_res.swot, "strength_indicators", []),
                    )
                },
                weaknesses={
                    "indicators": getattr(
                        feasibility_score_res.swot,
                        "weaknesses",
                        getattr(feasibility_score_res.swot, "weakness_indicators", []),
                    )
                },
                opportunities={
                    "indicators": getattr(
                        feasibility_score_res.swot,
                        "opportunities",
                        getattr(feasibility_score_res.swot, "opportunity_indicators", []),
                    )
                },
                threats={
                    "indicators": getattr(
                        feasibility_score_res.swot,
                        "threats",
                        getattr(feasibility_score_res.swot, "threat_indicators", []),
                    )
                },
                confidence=feasibility_score_res.data_confidence or ai_advice.confidence,
                scoring_version="v1.0",
            )
            db.add(db_feasibility)

            db_ai = AIAnalysis(
                analysis_run_id=db_run.id,
                summary=ai_advice.summary,
                recommendation=ai_advice.recommendation,
                swot={
                    "strengths": ai_advice.reasoning,
                    "weaknesses": [],
                    "opportunities": ai_advice.market_advice,
                    "threats": ai_advice.risks,
                },
                opportunities={"advice": ai_advice.market_advice},
                threats={"risks": ai_advice.risks},
                risks={"risks": ai_advice.risks},
                pricing_strategy={"financial_advice": ai_advice.financial_advice},
                business_plan={"next_steps": ai_advice.next_steps},
                model_name=ai_advice.model_name,
                prompt_version=ai_advice.prompt_version,
                confidence=ai_advice.confidence,
            )
            db.add(db_ai)

            mkt_size = getattr(market_res, "market_size", None)
            if mkt_size:
                pop_est = getattr(mkt_size, "total_population_reach", 0)
                hh_est = getattr(mkt_size, "household_reach", 0)
                target_est = getattr(mkt_size, "estimated_target_customers", 0)
            else:
                pop_est = getattr(market_res, "estimated_population_reach", 0)
                hh_est = getattr(market_res, "estimated_household_reach", 0)
                target_est = getattr(market_res, "estimated_target_customers", 0)

            comp_cnt = _get_comp_count(competition_res)
            db_market_analysis = MarketAnalysis(
                analysis_run_id=db_run.id,
                radius_km=10.0,
                population_estimate=pop_est,
                household_estimate=hh_est,
                market_reach_estimate=target_est,
                competitor_count=comp_cnt,
                demand_indicators={
                    "score": demand_score_val,
                    "level": _demand_level,
                },
                pricing_indicators={"average_price": pricing_info.get("average_market_price")},
                data_confidence=ai_advice.confidence,
            )
            db.add(db_market_analysis)

            cat_dist = getattr(competition_res, "category_distribution", {}) or {}
            db_competitor_analysis = CompetitorAnalysis(
                analysis_run_id=db_run.id,
                radius_km=10.0,
                competitor_count=comp_cnt,
                competition_density=getattr(competition_res, "competition_density", 0.0),
                competitor_distribution=cat_dist,
                data_confidence=ai_advice.confidence,
            )
            db.add(db_competitor_analysis)

            category_title = category.name if category else "Business"
            village_title = village.name if village else "Location"
            db_report = Report(
                analysis_run_id=db_run.id,
                user_id=user_id,
                title=f"Analysis Report - {category_title} ({village_title})",
                language=lang_str,
                report_data={
                    "summary": ai_advice.summary,
                    "recommendation": ai_advice.recommendation,
                    "overall_score": feasibility_score_res.overall_score,
                },
            )
            db.add(db_report)

            db_run.status = "completed"
            db_run.completed_at = datetime.now(UTC)
            db.add(db_run)
            db.commit()
            db.refresh(db_run)
            return db_run

        except Exception as exc:
            db.rollback()
            run_id = getattr(db_run, "id", None)
            logger.exception(
                "Error executing analysis orchestrator pipeline for run %s",
                run_id or "unknown",
            )
            try:
                if run_id:
                    failed_run = db.get(AnalysisRun, run_id)
                    if failed_run:
                        failed_run.status = "failed"
                        failed_run.completed_at = datetime.now(UTC)
                        db.add(failed_run)
                        db.commit()
            except Exception as cleanup_exc:
                logger.exception("Failed to update run status to failed: %s", cleanup_exc)
                db.rollback()
            raise exc
