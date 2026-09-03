"""API routes for Population data queries."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.population import PopulationResponse
from app.services.population_service import PopulationService

router = APIRouter()


@router.get("/years", response_model=list[int])
def list_available_years(
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    db: Session = Depends(get_session),
):
    """Get distinct years with population data."""
    return PopulationService.get_available_years(db, location_id=location_id)


@router.get("", response_model=list[PopulationResponse])
def list_population(
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    year: int | None = Query(default=None, description="Filter by year"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List population records with optional filters."""
    return PopulationService.get_population_records(
        db, location_id=location_id, year=year, limit=limit
    )


@router.get("/{population_id}", response_model=PopulationResponse)
def get_population(population_id: UUID, db: Session = Depends(get_session)):
    """Get a single population record by ID."""
    record = PopulationService.get_population_by_id(db, population_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Population record {population_id} not found")
    return record
