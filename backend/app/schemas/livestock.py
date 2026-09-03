"""Pydantic response schemas for Livestock domain data."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LivestockResponse(BaseModel):
    id: UUID
    location_id: UUID
    animal_type: str | None = None
    animal_count: int | None = Field(default=None, ge=0)
    milk_production: float | None = Field(default=None, ge=0)
    milk_production_unit: str | None = None
    year: int | None = None
    source: str | None = None
    source_url: str | None = None
    data_year: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
