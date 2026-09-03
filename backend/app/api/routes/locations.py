from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.geo.nearby_businesses import find_nearby_businesses
from app.geo.nearby_facilities import find_nearby_facilities
from app.geo.nearby_markets import find_nearby_markets
from app.geo.nearby_villages import find_nearby_villages
from app.schemas.location import (
    DedupDetectResponse,
    DistrictResponse,
    MergeRequest,
    MergeResponse,
    NearbyBusinessResponse,
    NearbyFacilityResponse,
    NearbyMarketResponse,
    NearbyVillageResponse,
    NormalizeRequest,
    NormalizeResponse,
    TalukaResponse,
    VillageResponse,
)
from app.services.location_service import LocationService, normalize_for_match

router = APIRouter()


# --- Hierarchy Endpoints ---


@router.get("/districts", response_model=list[DistrictResponse])
def get_districts(db: Session = Depends(get_session)):
    return LocationService.get_districts(db)


@router.get("/talukas", response_model=list[TalukaResponse])
def get_talukas(district_id: UUID | None = None, db: Session = Depends(get_session)):
    return LocationService.get_talukas(db, district_id=district_id)


@router.get("/villages", response_model=list[VillageResponse])
def get_villages(taluka_id: UUID | None = None, db: Session = Depends(get_session)):
    return LocationService.get_villages(db, taluka_id=taluka_id)


# --- Normalization & Dedup Endpoints ---


@router.post("/normalize", response_model=NormalizeResponse)
def normalize_location(req: NormalizeRequest):
    """Normalize a raw location name (no DB write)."""
    normalized = normalize_for_match(req.name)
    return NormalizeResponse(
        original=req.name,
        normalized=normalized,
        level=req.level,
    )


@router.get("/dedup/detect", response_model=DedupDetectResponse)
def detect_duplicates(
    level: str = Query(
        default="village",
        pattern=r"^(district|taluka|gram_panchayat|village)$",
        description="Location hierarchy level",
    ),
    state: str | None = Query(default=None, description="Filter by state (districts only)"),
    fuzzy_threshold: float = Query(
        default=0.85, ge=0.5, le=1.0, description="Fuzzy match threshold (0.5–1.0)"
    ),
    db: Session = Depends(get_session),
):
    """Detect groups of potential duplicate locations at the given level."""
    groups = LocationService.detect_duplicates(
        db, level=level, state=state, fuzzy_threshold=fuzzy_threshold
    )
    return DedupDetectResponse(
        level=level,
        total_groups=len(groups),
        groups=groups,
    )


@router.post("/dedup/merge", response_model=MergeResponse)
def merge_duplicates(
    req: MergeRequest,
    db: Session = Depends(get_session),
):
    """Merge duplicate locations into a single canonical record."""
    summary = LocationService.merge_duplicates(
        db, keep_id=req.keep_id, merge_ids=req.merge_ids, level=req.level
    )
    return MergeResponse(
        keep_id=req.keep_id,
        merged_count=len(req.merge_ids),
        summary=summary,
    )


# --- Nearby / Geo-Query Endpoints ---


@router.get("/nearby/villages", response_model=list[NearbyVillageResponse])
def get_nearby_villages(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Center latitude"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Center longitude"),
    radius_km: float = Query(default=10.0, gt=0.0, le=100.0, description="Search radius in km"),
    district_id: UUID | None = Query(default=None, description="Filter by district UUID"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """Find villages within radius_km of (lat, lng)."""
    return find_nearby_villages(db, lat, lng, radius_km, district_id, limit)


@router.get("/nearby/businesses", response_model=list[NearbyBusinessResponse])
def get_nearby_businesses(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Center latitude"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Center longitude"),
    radius_km: float = Query(default=10.0, gt=0.0, le=100.0, description="Search radius in km"),
    category_id: UUID | None = Query(default=None, description="Filter by business category UUID"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """Find businesses within radius_km of (lat, lng)."""
    return find_nearby_businesses(db, lat, lng, radius_km, category_id, limit)


@router.get("/nearby/markets", response_model=list[NearbyMarketResponse])
def get_nearby_markets(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Center latitude"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Center longitude"),
    radius_km: float = Query(default=25.0, gt=0.0, le=100.0, description="Search radius in km"),
    market_type: str | None = Query(default=None, description="Filter by market type"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """Find markets within radius_km of (lat, lng)."""
    return find_nearby_markets(db, lat, lng, radius_km, market_type, limit)


@router.get("/nearby/facilities", response_model=list[NearbyFacilityResponse])
def get_nearby_facilities(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Center latitude"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Center longitude"),
    radius_km: float = Query(default=10.0, gt=0.0, le=100.0, description="Search radius in km"),
    facility_type: str | None = Query(default=None, description="Filter by facility type"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """Find infrastructure facilities within radius_km of (lat, lng)."""
    return find_nearby_facilities(db, lat, lng, radius_km, facility_type, limit)
