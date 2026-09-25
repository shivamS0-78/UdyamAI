"""Feasibility Service for UdyamAI.

Orchestrates data aggregation across Market, Finance, Competition, Infrastructure,
and Risk Indicators domains to generate deterministic feasibility scores and structured SWOT indicators.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.feasibility.scorer import calculate_feasibility_scores
from app.feasibility.swot import build_swot_indicators
from app.geo.nearby_businesses import find_nearby_businesses
from app.geo.nearby_facilities import find_nearby_facilities
from app.geo.nearby_markets import find_nearby_markets
from app.geo.nearby_villages import find_nearby_villages
from app.market.competition import analyze_competition
from app.market.infrastructure import analyze_relevant_infrastructure
from app.market.risks import assess_market_risks
from app.models.location import Village
from app.schemas.feasibility import FeasibilityScoreResult, SWOTIndicators
from app.services.location_service import LocationService

logger = logging.getLogger(__name__)


def _get_entity_by_id(db: Session, model_cls: type, entity_id: UUID) -> Any:
    """Safely retrieves an entity by ID supporting SQLModel Session, SQLAlchemy 2.0, and legacy Session APIs."""
    try:
        return db.get(model_cls, entity_id)
    except AttributeError:
        res = db.execute(select(model_cls).where(model_cls.id == entity_id))
        return res.scalars().first()


class FeasibilityService:
    """Orchestrates deterministic feasibility calculations."""

    @staticmethod
    def calculate_feasibility(
        db: Session,
        village_id: UUID | None = None,
        lat: float | None = None,
        lng: float | None = None,
        radius_km: float = 10.0,
        business_category_id: UUID | None = None,
        category_name: str | None = None,
        project_size_sqm: float = 0.0,
        electricity_required_kw: float = 0.0,
        daily_water_req_liters: float = 0.0,
        road_access_required: bool = True,
        three_phase_power_required: bool = False,
        daily_passenger_traffic: int = 0,
        daily_cargo_tonnage: float = 0.0,
        is_seasonal: bool = False,
        price_volatility: str | None = None,
        available_capital: float = 0.0,
        desired_project_cost: float = 0.0,
        estimated_subsidy: float | None = None,
        matched_schemes: list[Any] | None = None,
        precomputed_nearby_biz: list[dict] | None = None,
        precomputed_nearby_facs: list[dict] | None = None,
        precomputed_nearby_mkts: list[dict] | None = None,
        precomputed_nearby_vils: list[dict] | None = None,
        precomputed_pop_reach: int | None = None,
        precomputed_hh_reach: int | None = None,
        precomputed_comp_res: dict[str, Any] | None = None,
        precomputed_infra_res: dict[str, Any] | None = None,
        precomputed_risk_res: dict[str, Any] | None = None,
    ) -> FeasibilityScoreResult:
        """Perform unified feasibility analysis for a location and project parameters."""
        target_lat = lat
        target_lng = lng

        if (target_lat is None or target_lng is None) and village_id is not None:
            village = _get_entity_by_id(db, Village, village_id)
            if not village:
                raise HTTPException(
                    status_code=404, detail=f"Village with id {village_id} not found"
                )
            if village.latitude is None or village.longitude is None:
                target_lat, target_lng = LocationService.ensure_village_coordinates(db, village)
            else:
                target_lat = village.latitude
                target_lng = village.longitude

        if target_lat is None or target_lng is None:
            raise HTTPException(
                status_code=400,
                detail="Location coordinates (lat, lng) or a valid village_id are required for feasibility calculation.",
            )

        # Retrieve empirical spatial data (or use precomputed values when passed by orchestrator).
        # A radius lookup is skipped outright when the only thing consuming it already has a
        # precomputed result. The orchestrator passes competition, population and infrastructure
        # metrics straight from the market-analysis step, so re-querying them here would add
        # several full spatial scans to every analysis run for nothing.
        nearby_biz = precomputed_nearby_biz if precomputed_nearby_biz is not None else []
        if precomputed_nearby_biz is None and precomputed_comp_res is None:
            nearby_biz = find_nearby_businesses(
                db,
                lat=target_lat,
                lng=target_lng,
                radius_km=max(radius_km, 25.0),
                category_id=business_category_id,
                limit=500,
            )
        nearby_facs = precomputed_nearby_facs if precomputed_nearby_facs is not None else []
        if precomputed_nearby_facs is None and precomputed_infra_res is None:
            nearby_facs = find_nearby_facilities(
                db, lat=target_lat, lng=target_lng, radius_km=radius_km, limit=500
            )
        nearby_mkts = (
            precomputed_nearby_mkts
            if precomputed_nearby_mkts is not None
            else find_nearby_markets(
                db, lat=target_lat, lng=target_lng, radius_km=max(radius_km, 35.0), limit=50
            )
        )
        nearby_vils = precomputed_nearby_vils if precomputed_nearby_vils is not None else []
        if precomputed_nearby_vils is None and precomputed_pop_reach is None:
            nearby_vils = find_nearby_villages(
                db, lat=target_lat, lng=target_lng, radius_km=max(radius_km, 15.0), limit=500
            )

        # 1. Market metrics - retrieve demographic data from Population table (or use precomputed)
        if precomputed_pop_reach is not None:
            pop_reach = precomputed_pop_reach
            hh_reach = precomputed_hh_reach if precomputed_hh_reach is not None else 0
        else:
            all_vil_ids = [v["id"] for v in nearby_vils if v.get("id")]
            if village_id and village_id not in all_vil_ids:
                all_vil_ids.append(village_id)

            def _val(obj: Any, attr: str) -> int:
                if obj is None:
                    return 0
                val = getattr(obj, attr, None)
                if val is not None and not isinstance(val, bool):
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        pass
                pop_obj = getattr(obj, "Population", None)
                if pop_obj is not None:
                    val2 = getattr(pop_obj, attr, None)
                    if val2 is not None and not isinstance(val2, bool):
                        try:
                            return int(val2)
                        except (ValueError, TypeError):
                            pass
                if isinstance(obj, (tuple, list)) and len(obj) > 0:
                    return _val(obj[0], attr)
                return 0

            from app.models.location import Population

            try:
                pop_records_raw = (
                    db.exec(select(Population).where(Population.location_id.in_(all_vil_ids))).all()
                    if all_vil_ids
                    else []
                )
                pop_records = pop_records_raw if isinstance(pop_records_raw, (list, tuple)) else []
            except Exception:
                pop_records = []

            pop_reach = sum(_val(p, "population_total") for p in pop_records)
            hh_reach = sum(_val(p, "households") for p in pop_records)

            # Fallback to direct village population lookup if list is empty
            if pop_reach == 0 and village_id:
                try:
                    t_pop = db.exec(
                        select(Population).where(Population.location_id == village_id)
                    ).first()
                except Exception:
                    t_pop = None
                if t_pop:
                    pop_reach = _val(t_pop, "population_total")
                    hh_reach = _val(t_pop, "households")

        # Explicit distance calculation without 100000 sentinel
        valid_distances = [
            m["distance_meters"] / 1000.0
            for m in nearby_mkts
            if isinstance(m, dict) and m.get("distance_meters") is not None
        ]
        nearest_dist = min(valid_distances) if valid_distances else None
        single_mkt_name = nearby_mkts[0].get("name") if len(nearby_mkts) == 1 else None

        # Determine data availability flags
        # Finding zero results IS valid data (e.g. 0 competitors = low competition = good).
        # Data is "available" when the search was successfully performed, not only when results exist.
        comp_data_available = True  # Search performed; 0 competitors is a valid finding
        mkt_data_available = True  # Search performed; 0 markets is a valid finding
        infra_data_available = True  # Search performed; 0 facilities is a valid finding
        fin_data_available = float(desired_project_cost or 0.0) > 0.0
        risk_data_available = comp_data_available or mkt_data_available or infra_data_available

        # 2. Competition metrics
        if precomputed_comp_res is not None:
            comp_res = precomputed_comp_res
        else:
            from app.models.business import BusinessCategory

            cat_obj = (
                _get_entity_by_id(db, BusinessCategory, business_category_id)
                if business_category_id
                else None
            )
            cat_name = cat_obj.name if cat_obj else None

            comp_res = analyze_competition(
                nearby_biz,
                radius_km=max(radius_km, 25.0),
                target_category_id=str(business_category_id) if business_category_id else None,
                target_category_name=cat_name,
            )
        if not isinstance(comp_res, dict):
            logger.warning("analyze_competition returned unexpected type: %r", comp_res)
            comp_res = {}
        calc_comp_density = float(
            comp_res.get("competition_density_per_km2", comp_res.get("competition_density", 0.0))
            or 0.0
        )
        direct_comp_count = int(
            comp_res.get(
                "direct_competitor_count", comp_res.get("competitor_count", len(nearby_biz))
            )
            or 0
        )

        # 3. Infrastructure metrics
        if precomputed_infra_res is not None:
            infra_res = precomputed_infra_res
        else:
            infra_res = analyze_relevant_infrastructure(nearby_facs)
        if not isinstance(infra_res, dict):
            logger.warning(
                "analyze_relevant_infrastructure returned unexpected type: %r", infra_res
            )
            infra_res = {"facility_counts_by_type": {}}
        facility_counts = infra_res.get("facility_counts_by_type", {}) or {}

        # 4. Risk indicators
        if precomputed_risk_res is not None:
            risk_res = precomputed_risk_res
        else:
            risk_res = assess_market_risks(
                competition_density=calc_comp_density,
                facility_counts=facility_counts,
                price_volatility=price_volatility or "low",
                is_seasonal=is_seasonal,
                population_reach=pop_reach,
                nearby_markets_count=len(nearby_mkts),
                nearest_market_distance_km=nearest_dist,
                single_market_name=single_mkt_name,
                radius_km=radius_km,
                data_available=risk_data_available,
            )
        engine_risk_score = float(risk_res.get("risk_score", 0.0))
        risk_flags = risk_res.get("identified_risk_flags", [])

        # 5. Financial subsidy estimation (use matched subsidy if provided, else 0.0)
        if estimated_subsidy is not None:
            calc_subsidy = float(estimated_subsidy)
        elif matched_schemes:
            subsidies = [
                float(
                    getattr(s, "estimated_subsidy_amount", 0.0)
                    or getattr(s, "potential_subsidy", 0.0)
                    or 0.0
                )
                for s in matched_schemes
            ]
            calc_subsidy = max(subsidies) if subsidies else 0.0
        else:
            calc_subsidy = 0.0

        # Calculate sub-scores & overall score with sufficiency signals
        scores = calculate_feasibility_scores(
            population_reach=pop_reach,
            household_reach=hh_reach,
            nearest_market_distance_km=nearest_dist,
            nearby_markets_count=len(nearby_mkts),
            available_capital=available_capital,
            desired_project_cost=desired_project_cost,
            estimated_subsidy=calc_subsidy,
            competition_density=calc_comp_density,
            facility_counts=facility_counts,
            engine_risk_score=engine_risk_score,
            competitor_count=direct_comp_count,
            market_data_available=mkt_data_available,
            financial_data_available=fin_data_available,
            competition_data_available=comp_data_available,
            infrastructure_data_available=infra_data_available,
            risk_data_available=risk_data_available,
        )

        # Build SWOT indicators for AI narrative
        swot_dict = build_swot_indicators(
            market_scores=scores,
            population_reach=pop_reach,
            household_reach=hh_reach,
            available_capital=available_capital,
            desired_project_cost=desired_project_cost,
            estimated_subsidy=calc_subsidy,
            competition_density=calc_comp_density,
            facility_counts=facility_counts,
            identified_risk_flags=risk_flags,
            nearest_market_distance_km=nearest_dist,
            competition_data_available=comp_data_available,
            market_data_available=mkt_data_available,
            financial_data_available=fin_data_available,
            infrastructure_data_available=infra_data_available,
            risk_data_available=risk_data_available,
        )

        return FeasibilityScoreResult(
            market_score=scores["market_score"],
            financial_score=scores["financial_score"],
            competition_score=scores["competition_score"],
            infrastructure_score=scores["infrastructure_score"],
            risk_score=scores["risk_score"],
            overall_score=scores["overall_score"],
            swot=SWOTIndicators(
                strength_indicators=swot_dict["strength_indicators"],
                weakness_indicators=swot_dict["weakness_indicators"],
                opportunity_indicators=swot_dict["opportunity_indicators"],
                threat_indicators=swot_dict["threat_indicators"],
            ),
            data_confidence=scores["data_confidence"],
            market_data_available=scores["market_data_available"],
            financial_data_available=scores["financial_data_available"],
            competition_data_available=scores["competition_data_available"],
            infrastructure_data_available=scores["infrastructure_data_available"],
            risk_data_available=scores["risk_data_available"],
        )
