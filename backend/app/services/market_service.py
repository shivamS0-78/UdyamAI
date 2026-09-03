"""Market Service for UdyamAI.

Provides reusable data-access functions for Market, MarketPrice,
MarketAnalysis, and CompetitorAnalysis domain data, as well as the
master Market Analysis orchestrator.
"""

import logging
from datetime import date
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_
from sqlmodel import Session, col, select

from app.geo.nearby_businesses import find_nearby_businesses
from app.geo.nearby_facilities import find_nearby_facilities
from app.geo.nearby_markets import find_nearby_markets
from app.geo.nearby_villages import find_nearby_villages
from app.market.competition import analyze_competition
from app.market.demand import calculate_demand_indicators
from app.market.infrastructure import analyze_relevant_infrastructure
from app.market.market_size import (
    calculate_population_and_household_reach,
    estimate_target_customers,
)
from app.market.pricing import analyze_market_pricing
from app.market.purchasing_power import estimate_purchasing_power
from app.market.risks import assess_market_risks
from app.models.agriculture import Agriculture
from app.models.business import BusinessCategory
from app.models.economic import EconomicIndicator
from app.models.location import Population, Village
from app.models.market import CompetitorAnalysis, Market, MarketAnalysis, MarketPrice
from app.schemas.market import (
    CompetitionAnalysisDetailResponse,
    LocationMarketAnalysisResponse,
    MarketProvenanceInfo,
    MarketRiskAssessmentResponse,
    NearbyInfrastructureSummary,
    NearbyMarketSummary,
    RadiusMarketAnalysisResult,
    RiskIndicatorItem,
)

logger = logging.getLogger(__name__)


def _get_entity_by_id(db: Session, model_cls: type, entity_id: UUID) -> Any:
    """Safely retrieves an entity by ID supporting SQLModel Session, SQLAlchemy 2.0, and legacy Session APIs."""
    try:
        return db.get(model_cls, entity_id)
    except AttributeError:
        res = db.execute(select(model_cls).where(model_cls.id == entity_id))
        return res.scalars().first()


class MarketService:
    # ------------------------------------------------------------------ #
    # Markets
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_markets(
        db: Session,
        market_type: str | None = None,
        location_id: UUID | None = None,
        limit: int = 50,
    ) -> list[Market]:
        """List markets with optional filters."""
        limit = min(limit, 200)
        statement = select(Market).order_by(Market.name)

        if market_type is not None:
            statement = statement.where(Market.market_type == market_type)
        if location_id is not None:
            statement = statement.where(Market.location_id == location_id)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_market_by_id(db: Session, market_id: UUID) -> Market | None:
        """Get a single market by ID."""
        return db.get(Market, market_id)

    # ------------------------------------------------------------------ #
    # Market Prices
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_market_prices(
        db: Session,
        market_id: UUID | None = None,
        location_id: UUID | None = None,
        commodity: str | None = None,
        recorded_date: date | None = None,
        limit: int = 100,
    ) -> list[MarketPrice]:
        """List market prices with optional filters."""
        limit = min(limit, 500)
        statement = select(MarketPrice).order_by(col(MarketPrice.recorded_date).desc())

        if market_id is not None:
            statement = statement.where(MarketPrice.market_id == market_id)
        if location_id is not None:
            statement = statement.where(MarketPrice.location_id == location_id)
        if commodity is not None:
            statement = statement.where(MarketPrice.commodity == commodity)
        if recorded_date is not None:
            statement = statement.where(MarketPrice.recorded_date == recorded_date)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_price_history(
        db: Session,
        commodity: str,
        market_id: UUID | None = None,
        location_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 365,
    ) -> list[MarketPrice]:
        """Get price history for a commodity over time."""
        limit = min(limit, 1000)
        statement = (
            select(MarketPrice)
            .where(MarketPrice.commodity == commodity)
            .order_by(col(MarketPrice.recorded_date).asc())
        )

        if market_id is not None:
            statement = statement.where(MarketPrice.market_id == market_id)
        if location_id is not None:
            statement = statement.where(MarketPrice.location_id == location_id)
        if start_date is not None:
            statement = statement.where(MarketPrice.recorded_date >= start_date)
        if end_date is not None:
            statement = statement.where(MarketPrice.recorded_date <= end_date)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_latest_prices(
        db: Session,
        market_id: UUID | None = None,
        location_id: UUID | None = None,
        limit: int = 50,
    ) -> list[MarketPrice]:
        """Get the most recent price entry for each commodity at a market/location."""
        limit = min(limit, 200)
        from sqlalchemy import func

        subq = select(
            MarketPrice.commodity,
            func.max(MarketPrice.recorded_date).label("latest_date"),
        ).group_by(MarketPrice.commodity)

        if market_id is not None:
            subq = subq.where(MarketPrice.market_id == market_id)
        if location_id is not None:
            subq = subq.where(MarketPrice.location_id == location_id)

        subq = subq.subquery()

        statement = (
            select(MarketPrice)
            .join(
                subq,
                (MarketPrice.commodity == subq.c.commodity)
                & (MarketPrice.recorded_date == subq.c.latest_date),
            )
            .order_by(MarketPrice.commodity)
            .limit(limit)
        )

        return db.exec(statement).all()

    # ------------------------------------------------------------------ #
    # Market Analyses Data Access
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_market_analyses(
        db: Session,
        analysis_run_id: UUID,
    ) -> list[MarketAnalysis]:
        """Get market analyses for a given analysis run."""
        statement = (
            select(MarketAnalysis)
            .where(MarketAnalysis.analysis_run_id == analysis_run_id)
            .order_by(MarketAnalysis.created_at)
        )
        return db.exec(statement).all()

    @staticmethod
    def get_competitor_analyses(
        db: Session,
        analysis_run_id: UUID,
    ) -> list[CompetitorAnalysis]:
        """Get competitor analyses for a given analysis run."""
        statement = (
            select(CompetitorAnalysis)
            .where(CompetitorAnalysis.analysis_run_id == analysis_run_id)
            .order_by(CompetitorAnalysis.created_at)
        )
        return db.exec(statement).all()

    # ------------------------------------------------------------------ #
    # Market Analysis Orchestration (Phase 6)
    # ------------------------------------------------------------------ #

    @staticmethod
    def analyze_village_market(
        db: Session,
        village_id: UUID,
        radii_km: list[float] | None = None,
        target_conversion_rate: float = 0.05,
        business_category_id: UUID | None = None,
        analysis_run_id: UUID | None = None,
    ) -> LocationMarketAnalysisResponse:
        """Perform comprehensive market analysis for a target village location across configurable radii.

        Optimized with single-pass batch querying, error handling, configurable conversion rates,
        and provenance deduplication.
        """
        if radii_km is None or len(radii_km) == 0:
            radii_km = [5.0, 10.0]

        # Clean and sort requested radii
        radii_km = sorted([abs(float(r)) for r in radii_km if float(r) > 0])
        if not radii_km:
            radii_km = [5.0, 10.0]

        village = _get_entity_by_id(db, Village, village_id)
        if not village:
            raise HTTPException(status_code=404, detail=f"Village with id {village_id} not found")

        if village.latitude is None or village.longitude is None:
            raise HTTPException(
                status_code=400,
                detail=f"Village '{village.name}' (id {village_id}) is missing latitude/longitude coordinates.",
            )

        lat = village.latitude
        lng = village.longitude

        district_name = (
            village.district.name if hasattr(village, "district") and village.district else None
        )
        taluka_name = village.taluka.name if hasattr(village, "taluka") and village.taluka else None

        # Optimization 1 & 2: Batch geo lookups up to the max radius with error handling & logging
        max_radius = max(radii_km)

        try:
            all_nearby_villages = find_nearby_villages(
                db, lat=lat, lng=lng, radius_km=max_radius, limit=500
            )
        except Exception as e:
            logger.warning(f"Spatial lookup failed for nearby villages: {e}")
            all_nearby_villages = []

        all_village_ids = [UUID(str(v["id"])) for v in all_nearby_villages if v.get("id")]
        if village_id not in all_village_ids:
            all_village_ids.append(village_id)
            all_nearby_villages.append(
                {
                    "id": village.id,
                    "name": village.name,
                    "latitude": village.latitude,
                    "longitude": village.longitude,
                    "distance_meters": 0.0,
                }
            )

        try:
            all_nearby_markets = find_nearby_markets(
                db, lat=lat, lng=lng, radius_km=max_radius, limit=200
            )
        except Exception as e:
            logger.warning(f"Spatial lookup failed for nearby markets: {e}")
            all_nearby_markets = []

        all_market_ids = [UUID(str(m["id"])) for m in all_nearby_markets if m.get("id")]

        try:
            all_nearby_facilities = find_nearby_facilities(
                db, lat=lat, lng=lng, radius_km=max_radius, limit=200
            )
        except Exception as e:
            logger.warning(f"Spatial lookup failed for nearby facilities: {e}")
            all_nearby_facilities = []

        try:
            all_nearby_businesses = find_nearby_businesses(
                db,
                lat=lat,
                lng=lng,
                radius_km=max_radius,
                category_id=business_category_id,
                limit=500,
            )
        except Exception as e:
            logger.warning(f"Spatial lookup failed for nearby businesses: {e}")
            all_nearby_businesses = []

        # Optimization 1: Single-pass batch query for DB records across all unique village/market IDs
        pop_map: dict[str, dict] = {}
        if all_village_ids:
            pop_stmt = select(Population).where(Population.location_id.in_(all_village_ids))
            for pr in db.exec(pop_stmt).all():
                pop_map[str(pr.location_id)] = {
                    "population_total": pr.population_total,
                    "households": pr.households,
                    "working_population": pr.working_population,
                    "source": pr.source,
                    "source_url": pr.source_url,
                    "data_year": pr.data_year,
                }

        all_mkt_prices: list[dict] = []
        conds = []
        if all_market_ids:
            conds.append(MarketPrice.market_id.in_(all_market_ids))
        if all_village_ids:
            conds.append(MarketPrice.location_id.in_(all_village_ids))
        if conds:
            price_stmt = select(MarketPrice).where(or_(*conds)).limit(500)
            all_mkt_prices = [
                {k: v for k, v in p.__dict__.items() if not k.startswith("_")}
                for p in db.exec(price_stmt).all()
            ]

        all_econ_recs: list[dict] = []
        if all_village_ids:
            econ_stmt = select(EconomicIndicator).where(
                EconomicIndicator.location_id.in_(all_village_ids)
            )
            all_econ_recs = [
                {k: v for k, v in e.__dict__.items() if not k.startswith("_")}
                for e in db.exec(econ_stmt).all()
            ]

        all_agri_recs: list[dict] = []
        if all_village_ids:
            agri_stmt = select(Agriculture).where(Agriculture.location_id.in_(all_village_ids))
            all_agri_recs = [
                {k: v for k, v in a.__dict__.items() if not k.startswith("_")}
                for a in db.exec(agri_stmt).all()
            ]

        radius_results: list[RadiusMarketAnalysisResult] = []
        global_provenance: dict[tuple[str, str | None, int | None], MarketProvenanceInfo] = {}

        # Evaluate each requested radius in-memory using cached datasets
        for r in radii_km:
            max_meters = r * 1000.0

            nearby_villages = [
                v for v in all_nearby_villages if (v.get("distance_meters") or 0.0) <= max_meters
            ]
            v_ids_in_radius = {str(v["id"]) for v in nearby_villages if v.get("id")}

            nearby_mkts = [
                m for m in all_nearby_markets if (m.get("distance_meters") or 0.0) <= max_meters
            ]
            m_ids_in_radius = {str(m["id"]) for m in nearby_mkts if m.get("id")}

            nearby_facs = [
                f for f in all_nearby_facilities if (f.get("distance_meters") or 0.0) <= max_meters
            ]

            nearby_biz = [
                b for b in all_nearby_businesses if (b.get("distance_meters") or 0.0) <= max_meters
            ]

            mkt_prices = [
                p
                for p in all_mkt_prices
                if (p.get("market_id") and str(p.get("market_id")) in m_ids_in_radius)
                or (p.get("location_id") and str(p.get("location_id")) in v_ids_in_radius)
            ]

            econ_recs = [
                e
                for e in all_econ_recs
                if e.get("location_id") and str(e.get("location_id")) in v_ids_in_radius
            ]

            agri_recs = [
                a
                for a in all_agri_recs
                if a.get("location_id") and str(a.get("location_id")) in v_ids_in_radius
            ]

            # 1. Population & target customer estimation with configurable conversion rate
            pop_res = calculate_population_and_household_reach(nearby_villages, pop_map)
            pop_reach = pop_res["estimated_population_reach"]
            hh_reach = pop_res["estimated_household_reach"]
            target_cust = estimate_target_customers(
                pop_reach, hh_reach, conversion_rate=target_conversion_rate
            )

            # 2. Market summaries
            market_summaries = []
            for m in nearby_mkts:
                dist_km = round((m.get("distance_meters") or 0.0) / 1000.0, 2)
                m_id = m.get("id")
                sample_p = next(
                    (
                        p
                        for p in mkt_prices
                        if p.get("market_id") is not None and str(p.get("market_id")) == str(m_id)
                    ),
                    None,
                )
                market_summaries.append(
                    NearbyMarketSummary(
                        id=m_id,
                        name=m.get("name"),
                        market_type=m.get("market_type"),
                        distance_km=dist_km,
                        modal_price_sample=sample_p.get("modal_price") if sample_p else None,
                        commodity_sample=sample_p.get("commodity") if sample_p else None,
                    )
                )

            # 3. Infrastructure
            infra_res = analyze_relevant_infrastructure(nearby_facs)
            if not isinstance(infra_res, dict):
                logger.warning(
                    "analyze_relevant_infrastructure returned unexpected type: %r", infra_res
                )
                infra_res = {"facility_summaries": [], "facility_counts_by_type": {}}

            infra_summaries = [
                NearbyInfrastructureSummary(
                    id=item.get("id"),
                    name=item.get("name"),
                    facility_type=item.get("facility_type"),
                    distance_km=item.get("distance_km", 0.0),
                    capacity=item.get("capacity"),
                )
                for item in infra_res.get("facility_summaries", [])
            ]

            # 4. Competition
            target_cat_name = None
            if business_category_id:
                b_cat = _get_entity_by_id(db, BusinessCategory, business_category_id)
                if b_cat:
                    target_cat_name = b_cat.name

            comp_res = analyze_competition(
                nearby_biz,
                radius_km=r,
                target_category_id=str(business_category_id) if business_category_id else None,
                target_category_name=target_cat_name,
            )

            # 5. Indicators & Pricing
            pricing_res = analyze_market_pricing(nearby_mkts, mkt_prices)
            demand_res = calculate_demand_indicators(
                pop_reach,
                hh_reach,
                pop_res["estimated_working_population"],
                econ_recs,
                agri_recs,
                radius_km=r,
            )
            pp_res = estimate_purchasing_power(
                pop_reach, hh_reach, pop_res["estimated_working_population"], econ_recs
            )
            nearest_mkt_dist = (
                min([m.get("distance_meters", 100000) / 1000.0 for m in nearby_mkts])
                if nearby_mkts
                else None
            )
            single_mkt_name = nearby_mkts[0].get("name") if len(nearby_mkts) == 1 else None

            risk_res = assess_market_risks(
                competition_density=comp_res["competition_density_per_km2"],
                facility_counts=infra_res["facility_counts_by_type"],
                price_volatility=pricing_res["price_volatility"],
                population_reach=pop_reach,
                nearby_markets_count=len(nearby_mkts),
                nearest_market_distance_km=nearest_mkt_dist,
                single_market_name=single_mkt_name,
                radius_km=r,
            )

            indicators_dict = {
                "demand": demand_res,
                "pricing": pricing_res,
                "competition": comp_res,
                "purchasing_power": pp_res,
                "risks": risk_res,
            }

            # Optimization 5: Provenance deduplication per radius & globally by key
            radius_provenance_map: dict[
                tuple[str, str | None, int | None], MarketProvenanceInfo
            ] = {}
            for prov_group in (
                pop_res.get("provenance", []),
                infra_res.get("provenance", []),
                comp_res.get("provenance", []),
                pricing_res.get("provenance", []),
            ):
                for p in prov_group:
                    d_name = p.get("dataset_name", "Unknown Dataset")
                    s_source = p.get("source")
                    s_yr = p.get("data_year")
                    pkey = (d_name, s_source, s_yr)

                    prov_obj = MarketProvenanceInfo(
                        dataset_name=d_name,
                        source=s_source,
                        source_url=p.get("source_url"),
                        data_year=s_yr,
                        record_count=p.get("record_count", 0),
                        confidence_score=p.get("confidence_score", "medium"),
                    )
                    radius_provenance_map[pkey] = prov_obj
                    global_provenance[pkey] = prov_obj

            radius_result = RadiusMarketAnalysisResult(
                radius_km=r,
                estimated_population_reach=pop_reach,
                estimated_household_reach=hh_reach,
                estimated_target_customers=target_cust,
                nearby_villages_count=len(nearby_villages),
                nearby_markets_count=len(nearby_mkts),
                nearby_markets=market_summaries,
                relevant_infrastructure_count=len(nearby_facs),
                relevant_infrastructure=infra_summaries,
                market_indicators=indicators_dict,
                provenance=list(radius_provenance_map.values()),
            )
            radius_results.append(radius_result)

            # Save DB record if analysis_run_id is provided
            if analysis_run_id is not None:
                db_analysis = MarketAnalysis(
                    analysis_run_id=analysis_run_id,
                    radius_km=r,
                    population_estimate=pop_reach,
                    household_estimate=hh_reach,
                    market_reach_estimate=target_cust,
                    competitor_count=comp_res["competitor_count"],
                    demand_indicators=demand_res,
                    distribution_channels={
                        "markets_count": len(nearby_mkts),
                        "infrastructure_count": len(nearby_facs),
                    },
                    pricing_indicators=pricing_res,
                    market_gaps={"identified_gaps": comp_res["identified_market_gaps"]},
                    data_confidence=comp_res["data_completeness"],
                )
                db_comp_analysis = CompetitorAnalysis(
                    analysis_run_id=analysis_run_id,
                    radius_km=r,
                    competitor_count=comp_res["competitor_count"],
                    competition_density=comp_res["competitor_density"],
                    competitor_distribution=comp_res["category_distribution"],
                    identified_gaps={"identified_gaps": comp_res["identified_market_gaps"]},
                    data_confidence=comp_res["data_completeness"],
                )
                try:
                    with db.begin_nested():
                        db.add(db_analysis)
                        db.add(db_comp_analysis)
                        db.flush()
                except Exception as e:
                    logger.error(
                        f"Failed to stage MarketAnalysis record for radius {r}km: {e}",
                        exc_info=True,
                    )

        if analysis_run_id is not None:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(
                    f"Failed to commit MarketAnalysis batch for run {analysis_run_id}: {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Database commit error while persisting market analysis: {e}",
                ) from e

        return LocationMarketAnalysisResponse(
            village_id=village.id,
            village_name=village.name,
            district_name=district_name,
            taluka_name=taluka_name,
            latitude=village.latitude,
            longitude=village.longitude,
            radii_km=radii_km,
            radius_analyses=radius_results,
            provenance_summary=list(global_provenance.values()),
        )

    # ------------------------------------------------------------------ #
    # Competition Analysis (Phase 7)
    # ------------------------------------------------------------------ #

    @staticmethod
    def analyze_competition_for_location(
        db: Session,
        village_id: UUID | None = None,
        lat: float | None = None,
        lng: float | None = None,
        radius_km: float = 10.0,
        business_category_id: UUID | None = None,
        category_name: str | None = None,
    ) -> CompetitionAnalysisDetailResponse:
        """Perform standalone competition analysis for a location and business category."""
        target_lat = lat
        target_lng = lng

        if (target_lat is None or target_lng is None) and village_id is not None:
            village = _get_entity_by_id(db, Village, village_id)
            if not village:
                raise HTTPException(
                    status_code=404, detail=f"Village with id {village_id} not found"
                )
            if village.latitude is None or village.longitude is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Village '{village.name}' (id {village_id}) is missing latitude/longitude coordinates.",
                )
            target_lat = village.latitude
            target_lng = village.longitude

        if target_lat is None or target_lng is None:
            raise HTTPException(
                status_code=400,
                detail="Location coordinates (lat, lng) or a valid village_id are required for competition analysis.",
            )

        # Resolve category name if ID provided
        resolved_category_name = category_name
        if business_category_id and not resolved_category_name:
            b_cat = _get_entity_by_id(db, BusinessCategory, business_category_id)
            if b_cat:
                resolved_category_name = b_cat.name

        try:
            nearby_businesses = find_nearby_businesses(
                db,
                lat=target_lat,
                lng=target_lng,
                radius_km=radius_km,
                category_id=business_category_id,
                limit=500,
            )
        except Exception as e:
            logger.warning(f"Spatial lookup failed for competition analysis: {e}")
            nearby_businesses = []

        comp_res = analyze_competition(
            nearby_businesses,
            radius_km=radius_km,
            target_category_id=str(business_category_id) if business_category_id else None,
            target_category_name=resolved_category_name,
        )

        provenance_objs = [
            MarketProvenanceInfo(
                dataset_name=p.get("dataset_name", "Businesses Registry"),
                source=p.get("source"),
                source_url=p.get("source_url"),
                data_year=p.get("data_year"),
                record_count=p.get("record_count", 0),
                confidence_score=p.get("confidence_score", "medium"),
            )
            for p in comp_res.get("provenance", [])
        ]

        return CompetitionAnalysisDetailResponse(
            competitor_count=comp_res["competitor_count"],
            competitor_density=comp_res["competitor_density"],
            businesses_within_5km=comp_res["businesses_within_5km"],
            businesses_within_10km=comp_res["businesses_within_10km"],
            total_businesses_in_radius=comp_res["total_businesses_in_radius"],
            target_category=resolved_category_name
            or (str(business_category_id) if business_category_id else None),
            category_distribution=comp_res["category_distribution"],
            identified_market_gaps=comp_res["identified_market_gaps"],
            quality_indicator=comp_res["quality_indicator"],
            data_confidence=comp_res["data_completeness"],
            provenance=provenance_objs,
        )

    @staticmethod
    def assess_risks_for_location(
        db: Session,
        village_id: UUID | None = None,
        lat: float | None = None,
        lng: float | None = None,
        radius_km: float = 10.0,
        competition_density: float | None = None,
        price_volatility: str | None = None,
        is_seasonal: bool = False,
    ) -> MarketRiskAssessmentResponse:
        """Perform standalone Phase 8 Risk Indicators assessment for a location."""
        target_lat = lat
        target_lng = lng

        if (target_lat is None or target_lng is None) and village_id is not None:
            village = _get_entity_by_id(db, Village, village_id)
            if not village:
                raise HTTPException(
                    status_code=404, detail=f"Village with id {village_id} not found"
                )
            if village.latitude is None or village.longitude is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Village '{village.name}' (id {village_id}) is missing latitude/longitude coordinates.",
                )
            target_lat = village.latitude
            target_lng = village.longitude

        if target_lat is None or target_lng is None:
            raise HTTPException(
                status_code=400,
                detail="Location coordinates (lat, lng) or a valid village_id are required for risk assessment.",
            )

        # Retrieve empirical data around coordinates
        nearby_biz = find_nearby_businesses(
            db, lat=target_lat, lng=target_lng, radius_km=radius_km, limit=500
        )
        nearby_facs = find_nearby_facilities(
            db, lat=target_lat, lng=target_lng, radius_km=radius_km, limit=500
        )
        nearby_mkts = find_nearby_markets(
            db, lat=target_lat, lng=target_lng, radius_km=radius_km, limit=50
        )
        nearby_vils = find_nearby_villages(
            db, lat=target_lat, lng=target_lng, radius_km=radius_km, limit=500
        )

        calc_comp_density = competition_density
        if calc_comp_density is None:
            comp_analysis = analyze_competition(nearby_biz, radius_km=radius_km)
            if not isinstance(comp_analysis, dict):
                logger.warning("analyze_competition returned non-dict value: %r", comp_analysis)
                comp_analysis = {}
            calc_comp_density = float(comp_analysis.get("competition_density_per_km2", 0.0) or 0.0)

        infra_analysis = analyze_relevant_infrastructure(nearby_facs)
        if not isinstance(infra_analysis, dict):
            logger.warning(
                "analyze_relevant_infrastructure returned non-dict value: %r", infra_analysis
            )
            infra_analysis = {}
        facility_counts = infra_analysis.get("facility_counts_by_type", {}) or {}

        pop_reach = sum(v.get("population", 0) or 0 for v in nearby_vils)

        valid_distances = [
            m["distance_meters"] / 1000.0
            for m in nearby_mkts
            if isinstance(m, dict) and m.get("distance_meters") is not None
        ]
        nearest_dist = min(valid_distances) if valid_distances else None
        single_mkt_name = nearby_mkts[0].get("name") if len(nearby_mkts) == 1 else None
        has_empirical_data = bool(
            nearby_biz
            or nearby_facs
            or nearby_mkts
            or nearby_vils
            or is_seasonal
            or price_volatility
            or competition_density is not None
        )
        logger.debug(
            f"Risk assessment empirical inputs: comp_density={calc_comp_density}, "
            f"facility_counts={facility_counts}, pop_reach={pop_reach}, "
            f"nearby_mkts={len(nearby_mkts)}, nearest_dist={nearest_dist}, "
            f"has_empirical_data={has_empirical_data}"
        )

        risk_res = assess_market_risks(
            competition_density=calc_comp_density,
            facility_counts=facility_counts,
            price_volatility=price_volatility or "low",
            population_reach=pop_reach,
            nearby_markets_count=len(nearby_mkts),
            nearest_market_distance_km=nearest_dist,
            single_market_name=single_mkt_name,
            is_seasonal=is_seasonal,
            radius_km=radius_km,
            data_available=has_empirical_data,
        )

        risk_items = [
            RiskIndicatorItem(
                risk_type=r["risk_type"],
                severity=r["severity"],
                evidence=r["evidence"],
                source=r["source"],
                value=r.get("value"),
            )
            for r in risk_res.get("risks", [])
        ]

        provenance_objs = [
            MarketProvenanceInfo(
                dataset_name=p.get("dataset_name", "Risk Indicators Engine"),
                source=p.get("source"),
                source_url=p.get("source_url"),
                data_year=p.get("data_year"),
                record_count=p.get("record_count", 0),
                confidence_score=p.get("confidence_score", "high"),
            )
            for p in risk_res.get("provenance", [])
        ]

        return MarketRiskAssessmentResponse(
            overall_market_risk_level=risk_res["overall_market_risk_level"],
            risk_score=risk_res["risk_score"],
            risks=risk_items,
            identified_risk_flags=risk_res["identified_risk_flags"],
            provenance=provenance_objs,
        )

    # ------------------------------------------------------------------ #
    # Aggregation helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_commodities(
        db: Session,
        market_id: UUID | None = None,
        location_id: UUID | None = None,
    ) -> list[str]:
        """Get distinct commodity names available at a market or location."""
        from sqlalchemy import distinct

        statement = select(distinct(MarketPrice.commodity)).where(
            MarketPrice.commodity.is_not(None)
        )

        if market_id is not None:
            statement = statement.where(MarketPrice.market_id == market_id)
        if location_id is not None:
            statement = statement.where(MarketPrice.location_id == location_id)

        statement = statement.order_by(MarketPrice.commodity)
        return [row[0] for row in db.exec(statement).all()]

    @staticmethod
    def get_market_types(db: Session) -> list[str]:
        """Get distinct market types in the database."""
        from sqlalchemy import distinct

        statement = (
            select(distinct(Market.market_type))
            .where(Market.market_type.is_not(None))
            .order_by(Market.market_type)
        )
        return [row[0] for row in db.exec(statement).all()]
