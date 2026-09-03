"""API routes for Economic indicator data queries."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.economic import EconomicIndicatorResponse
from app.services.economic_service import EconomicService

router = APIRouter()


@router.get("/indicators", response_model=list[str])
def list_indicator_names(
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    db: Session = Depends(get_session),
):
    """Get distinct indicator names."""
    return EconomicService.get_indicator_names(db, location_id=location_id)


@router.get("", response_model=list[EconomicIndicatorResponse])
def list_economic_indicators(
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    indicator_name: str | None = Query(default=None, description="Filter by indicator name"),
    year: int | None = Query(default=None, description="Filter by year"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List economic indicator records with optional filters."""
    return EconomicService.get_economic_indicators(
        db, location_id=location_id, indicator_name=indicator_name, year=year, limit=limit
    )


@router.get("/{indicator_id}", response_model=EconomicIndicatorResponse)
def get_economic_indicator(indicator_id: UUID, db: Session = Depends(get_session)):
    """Get a single economic indicator record by ID."""
    record = EconomicService.get_economic_indicator_by_id(db, indicator_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Economic indicator {indicator_id} not found")
    return record
