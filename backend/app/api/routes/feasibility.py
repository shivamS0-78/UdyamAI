"""Feasibility Engine API Routes for UdyamAI."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.feasibility import (
    FeasibilityCalculationRequest,
    FeasibilityScoreResult,
)
from app.services.feasibility_service import FeasibilityService

router = APIRouter()


@router.post("/calculate", response_model=FeasibilityScoreResult)
def calculate_feasibility(req: FeasibilityCalculationRequest, db: Session = Depends(get_session)):
    """Calculate deterministic feasibility sub-scores and SWOT indicators for location/project."""
    return FeasibilityService.calculate_feasibility(
        db=db,
        village_id=req.village_id,
        lat=req.latitude,
        lng=req.longitude,
        radius_km=req.radius_km,
        business_category_id=req.business_category_id,
        available_capital=req.available_capital,
        desired_project_cost=req.desired_project_cost,
    )


@router.get("", response_model=FeasibilityScoreResult)
def get_feasibility_by_query(
    village_id: UUID | None = Query(default=None, description="Village UUID"),
    lat: float | None = Query(default=None, ge=-90.0, le=90.0, description="Latitude coordinate"),
    lng: float | None = Query(
        default=None, ge=-180.0, le=180.0, description="Longitude coordinate"
    ),
    radius_km: float = Query(default=10.0, ge=0.1, le=50.0, description="Analysis radius in km"),
    available_capital: float = Query(default=0.0, ge=0.0, description="Available capital in INR"),
    desired_project_cost: float = Query(
        default=0.0, ge=0.0, description="Desired project cost in INR"
    ),
    business_category_id: UUID | None = Query(default=None, description="Business category UUID"),
    db: Session = Depends(get_session),
):
    """Get deterministic feasibility score breakdown via query parameters."""
    if not village_id and (lat is None or lng is None):
        raise HTTPException(
            status_code=400,
            detail="Either village_id or both lat and lng query parameters must be provided.",
        )
    return FeasibilityService.calculate_feasibility(
        db=db,
        village_id=village_id,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        business_category_id=business_category_id,
        available_capital=available_capital,
        desired_project_cost=desired_project_cost,
    )


@router.get("/{village_id}", response_model=FeasibilityScoreResult)
def get_village_feasibility(
    village_id: UUID,
    lat: float | None = Query(
        default=None, ge=-90.0, le=90.0, description="Optional latitude override"
    ),
    lng: float | None = Query(
        default=None, ge=-180.0, le=180.0, description="Optional longitude override"
    ),
    radius_km: float = Query(default=10.0, ge=0.1, le=50.0, description="Analysis radius in km"),
    available_capital: float = Query(default=0.0, ge=0.0, description="Available capital in INR"),
    desired_project_cost: float = Query(
        default=0.0, ge=0.0, description="Desired project cost in INR"
    ),
    business_category_id: UUID | None = Query(default=None, description="Business category UUID"),
    db: Session = Depends(get_session),
):
    """Get deterministic feasibility score breakdown for a specified village."""
    return FeasibilityService.calculate_feasibility(
        db=db,
        village_id=village_id,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        business_category_id=business_category_id,
        available_capital=available_capital,
        desired_project_cost=desired_project_cost,
    )
