"""API routes for Livestock data queries."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.livestock import LivestockResponse
from app.services.livestock_service import LivestockService

router = APIRouter()


@router.get("/types", response_model=list[str])
def list_animal_types(
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    db: Session = Depends(get_session),
):
    """Get distinct animal types."""
    return LivestockService.get_animal_types(db, location_id=location_id)


@router.get("", response_model=list[LivestockResponse])
def list_livestock(
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    animal_type: str | None = Query(default=None, description="Filter by animal type"),
    year: int | None = Query(default=None, description="Filter by year"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List livestock records with optional filters."""
    return LivestockService.get_livestock_records(
        db, location_id=location_id, animal_type=animal_type, year=year, limit=limit
    )


@router.get("/{livestock_id}", response_model=LivestockResponse)
def get_livestock(livestock_id: UUID, db: Session = Depends(get_session)):
    """Get a single livestock record by ID."""
    record = LivestockService.get_livestock_by_id(db, livestock_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Livestock record {livestock_id} not found")
    return record
