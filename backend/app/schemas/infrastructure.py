"""Pydantic response schemas for Infrastructure domain data."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InfrastructureResponse(BaseModel):
    id: UUID
    location_id: UUID | None = None
    facility_type: str | None = None
    name: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    distance_from_village: float | None = None
    capacity: float | None = None
    source: str | None = None
    source_url: str | None = None
    data_year: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
