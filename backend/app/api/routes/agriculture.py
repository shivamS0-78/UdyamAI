"""API routes for Agriculture data queries."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.agriculture import AgricultureResponse
from app.services.agriculture_service import AgricultureService

router = APIRouter()


@router.get("/crops", response_model=list[str])
def list_crop_names(
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    db: Session = Depends(get_session),
):
    """Get distinct crop names."""
    return AgricultureService.get_crop_names(db, location_id=location_id)


@router.get("/seasons", response_model=list[str])
def list_seasons(db: Session = Depends(get_session)):
    """Get distinct seasons."""
    return AgricultureService.get_seasons(db)


@router.get("", response_model=list[AgricultureResponse])
def list_agriculture(
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    crop_name: str | None = Query(default=None, description="Filter by crop name"),
    crop_category: str | None = Query(default=None, description="Filter by crop category"),
    season: str | None = Query(default=None, description="Filter by season"),
    year: int | None = Query(default=None, description="Filter by year"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List agriculture records with optional filters."""
    return AgricultureService.get_agriculture_records(
        db,
        location_id=location_id,
        crop_name=crop_name,
        crop_category=crop_category,
        season=season,
        year=year,
        limit=limit,
    )


@router.get("/{agriculture_id}", response_model=AgricultureResponse)
def get_agriculture(agriculture_id: UUID, db: Session = Depends(get_session)):
    """Get a single agriculture record by ID."""
    record = AgricultureService.get_agriculture_by_id(db, agriculture_id)
    if not record:
        raise HTTPException(
            status_code=404, detail=f"Agriculture record {agriculture_id} not found"
        )
    return record
