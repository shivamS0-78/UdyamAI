"""API routes for Infrastructure data queries."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.infrastructure import InfrastructureResponse
from app.services.infrastructure_service import InfrastructureService

router = APIRouter()


@router.get("/types", response_model=list[str])
def list_facility_types(db: Session = Depends(get_session)):
    """Get distinct facility types."""
    return InfrastructureService.get_facility_types(db)


@router.get("", response_model=list[InfrastructureResponse])
def list_infrastructure(
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    facility_type: str | None = Query(default=None, description="Filter by facility type"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """List infrastructure records with optional filters."""
    return InfrastructureService.get_infrastructure(
        db, location_id=location_id, facility_type=facility_type, limit=limit
    )


@router.get("/{infrastructure_id}", response_model=InfrastructureResponse)
def get_infrastructure(infrastructure_id: UUID, db: Session = Depends(get_session)):
    """Get a single infrastructure record by ID."""
    record = InfrastructureService.get_infrastructure_by_id(db, infrastructure_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Infrastructure {infrastructure_id} not found")
    return record
