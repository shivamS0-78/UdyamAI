"""API routes for Weather data queries."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.weather import WeatherResponse
from app.services.weather_service import WeatherService

router = APIRouter()


@router.get("", response_model=list[WeatherResponse])
def list_weather(
    location_id: UUID | None = Query(default=None, description="Filter by village location UUID"),
    start_date: date | None = Query(default=None, description="Start of date range"),
    end_date: date | None = Query(default=None, description="End of date range"),
    drought_only: bool = Query(default=False, description="Only drought-flagged records"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_session),
):
    """List weather records with optional filters."""
    return WeatherService.get_weather_records(
        db,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date,
        drought_only=drought_only,
        limit=limit,
    )


@router.get("/{weather_id}", response_model=WeatherResponse)
def get_weather(weather_id: UUID, db: Session = Depends(get_session)):
    """Get a single weather record by ID."""
    record = WeatherService.get_weather_by_id(db, weather_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Weather record {weather_id} not found")
    return record
