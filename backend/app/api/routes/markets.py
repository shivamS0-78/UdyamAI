"""API routes for Market data queries."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.market import (
    CompetitionAnalysisDetailResponse,
    CompetitionAnalysisRequest,
    CompetitorAnalysisResponse,
    LocationMarketAnalysisResponse,
    MarketAnalysisRequest,
    MarketAnalysisResponse,
    MarketPriceResponse,
    MarketResponse,
    MarketRiskAssessmentRequest,
    MarketRiskAssessmentResponse,
)
from app.services.market_service import MarketService

router = APIRouter()


# ------------------------------------------------------------------ #
# Static paths FIRST (before /{market_id})
# ------------------------------------------------------------------ #


@router.get("/types", response_model=list[str])
def list_market_types(db: Session = Depends(get_session)):
    """Get distinct market types."""
    return MarketService.get_market_types(db)


@router.get("/commodities", response_model=list[str])
def list_commodities(
    market_id: UUID | None = Query(default=None, description="Filter by market"),
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    db: Session = Depends(get_session),
):
    """Get distinct commodity names."""
    return MarketService.get_commodities(db, market_id=market_id, location_id=location_id)


@router.get("/prices", response_model=list[MarketPriceResponse])
def list_market_prices(
    market_id: UUID | None = Query(default=None, description="Filter by market UUID"),
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    commodity: str | None = Query(default=None, description="Filter by commodity name"),
    recorded_date: date | None = Query(default=None, description="Filter by exact date"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_session),
):
    """List market prices with optional filters."""
    return MarketService.get_market_prices(
        db,
        market_id=market_id,
        location_id=location_id,
        commodity=commodity,
        recorded_date=recorded_date,
        limit=limit,
    )


@router.get("/prices/history", response_model=list[MarketPriceResponse])
def get_price_history(
    commodity: str = Query(..., description="Commodity name"),
    market_id: UUID | None = Query(default=None, description="Filter by market"),
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    start_date: date | None = Query(default=None, description="Start of date range"),
    end_date: date | None = Query(default=None, description="End of date range"),
    limit: int = Query(default=365, ge=1, le=1000),
    db: Session = Depends(get_session),
):
    """Get price history for a commodity over time."""
    return MarketService.get_price_history(
        db,
        commodity=commodity,
        market_id=market_id,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/prices/latest", response_model=list[MarketPriceResponse])
def get_latest_prices(
    market_id: UUID | None = Query(default=None, description="Filter by market"),
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """Get the most recent price for each commodity."""
    return MarketService.get_latest_prices(
        db, market_id=market_id, location_id=location_id, limit=limit
    )


# ------------------------------------------------------------------ #
# Market / Competitor Analyses
# ------------------------------------------------------------------ #


@router.post("/analyze", response_model=LocationMarketAnalysisResponse)
def run_market_analysis(
    payload: MarketAnalysisRequest,
    db: Session = Depends(get_session),
):
    """Run comprehensive market analysis for a village location across configurable radii."""
    return MarketService.analyze_village_market(
        db=db,
        village_id=payload.village_id,
        radii_km=payload.radii_km,
        target_conversion_rate=payload.target_conversion_rate,
        business_category_id=payload.business_category_id,
        analysis_run_id=payload.analysis_run_id,
    )


@router.get("/analyze/{village_id}", response_model=LocationMarketAnalysisResponse)
def get_village_market_analysis(
    village_id: UUID,
    radii: list[float] | None = Query(default=None, description="Radii in km (e.g. 5.0, 10.0)"),
    target_conversion_rate: float = Query(
        default=0.05, ge=0.0, le=1.0, description="Target customer conversion rate (0.0 to 1.0)"
    ),
    business_category_id: UUID | None = Query(
        default=None, description="Optional business category"
    ),
    analysis_run_id: UUID | None = Query(default=None, description="Optional analysis run ID"),
    db: Session = Depends(get_session),
):
    """Perform market analysis for a village location specified by path parameter."""
    return MarketService.analyze_village_market(
        db=db,
        village_id=village_id,
        radii_km=radii,
        target_conversion_rate=target_conversion_rate,
        business_category_id=business_category_id,
        analysis_run_id=analysis_run_id,
    )


@router.get("/analyses/{analysis_run_id}", response_model=list[MarketAnalysisResponse])
def get_market_analyses(analysis_run_id: UUID, db: Session = Depends(get_session)):
    """Get market analyses for an analysis run."""
    return MarketService.get_market_analyses(db, analysis_run_id)


@router.get("/competitors/{analysis_run_id}", response_model=list[CompetitorAnalysisResponse])
def get_competitor_analyses(analysis_run_id: UUID, db: Session = Depends(get_session)):
    """Get competitor analyses for an analysis run."""
    return MarketService.get_competitor_analyses(db, analysis_run_id)


@router.post("/competition", response_model=CompetitionAnalysisDetailResponse)
def analyze_competition_post(
    payload: CompetitionAnalysisRequest,
    db: Session = Depends(get_session),
):
    """Run standalone Phase 7 competition analysis for a location and business category."""
    return MarketService.analyze_competition_for_location(
        db=db,
        village_id=payload.village_id,
        lat=payload.latitude,
        lng=payload.longitude,
        radius_km=payload.radius_km,
        business_category_id=payload.business_category_id,
        category_name=payload.category_name,
    )


@router.get("/competition/{village_id}", response_model=CompetitionAnalysisDetailResponse)
def analyze_competition_get(
    village_id: UUID,
    radius_km: float = Query(default=10.0, ge=0.1, le=50.0, description="Analysis radius in km"),
    business_category_id: UUID | None = Query(
        default=None, description="Optional business category ID"
    ),
    category_name: str | None = Query(
        default=None, description="Optional category name (e.g. Dairy)"
    ),
    lat: float | None = Query(
        default=None, ge=-90.0, le=90.0, description="Optional override latitude center point"
    ),
    lng: float | None = Query(
        default=None, ge=-180.0, le=180.0, description="Optional override longitude center point"
    ),
    db: Session = Depends(get_session),
):
    """Run Phase 7 competition analysis for a village specified by path parameter."""
    return MarketService.analyze_competition_for_location(
        db=db,
        village_id=village_id,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        business_category_id=business_category_id,
        category_name=category_name,
    )


@router.post("/risks", response_model=MarketRiskAssessmentResponse)
def assess_market_risks_post(
    payload: MarketRiskAssessmentRequest,
    db: Session = Depends(get_session),
):
    """Run Phase 8 Risk Indicators assessment for a location."""
    return MarketService.assess_risks_for_location(
        db=db,
        village_id=payload.village_id,
        lat=payload.latitude,
        lng=payload.longitude,
        radius_km=payload.radius_km,
        competition_density=payload.competition_density,
        price_volatility=payload.price_volatility,
        is_seasonal=payload.is_seasonal,
    )


@router.get("/risks/{village_id}", response_model=MarketRiskAssessmentResponse)
def assess_market_risks_get(
    village_id: UUID,
    radius_km: float = Query(default=10.0, ge=0.1, le=50.0, description="Analysis radius in km"),
    lat: float | None = Query(
        default=None, ge=-90.0, le=90.0, description="Optional override latitude center point"
    ),
    lng: float | None = Query(
        default=None, ge=-180.0, le=180.0, description="Optional override longitude center point"
    ),
    price_volatility: str | None = Query(
        default=None,
        description="Optional price volatility classification ('low', 'medium', 'high')",
    ),
    is_seasonal: bool = Query(
        default=False, description="Flag indicating seasonal crop/trade market"
    ),
    db: Session = Depends(get_session),
):
    """Run Phase 8 Risk Indicators assessment for a village specified by path parameter."""
    return MarketService.assess_risks_for_location(
        db=db,
        village_id=village_id,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        price_volatility=price_volatility,
        is_seasonal=is_seasonal,
    )


# ------------------------------------------------------------------ #
# Markets (dynamic path LAST)
# ------------------------------------------------------------------ #


@router.get("", response_model=list[MarketResponse])
def list_markets(
    market_type: str | None = Query(default=None, description="Filter by market type"),
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List markets with optional filters."""
    return MarketService.get_markets(
        db, market_type=market_type, location_id=location_id, limit=limit
    )


@router.get("/{market_id}", response_model=MarketResponse)
def get_market(market_id: UUID, db: Session = Depends(get_session)):
    """Get a single market by ID."""
    market = MarketService.get_market_by_id(db, market_id)
    if not market:
        raise HTTPException(status_code=404, detail=f"Market {market_id} not found")
    return market
