"""Pydantic response schemas for Weather domain data."""

from datetime import date as Date
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WeatherResponse(BaseModel):
    id: UUID
    location_id: UUID | None = None
    date: Date | None = None
    rainfall_mm: float | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    drought_indicator: bool = False
    source: str | None = None
    source_url: str | None = None
    data_year: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
