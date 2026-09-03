"""Pydantic response schemas for Agriculture domain data."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AgricultureResponse(BaseModel):
    id: UUID
    location_id: UUID
    crop_name: str | None = None
    crop_category: str | None = None
    cultivated_area: float | None = Field(default=None, ge=0)
    production: float | None = Field(default=None, ge=0)
    production_unit: str | None = None
    irrigated_area: float | None = Field(default=None, ge=0)
    year: int | None = None
    season: str | None = None
    source: str | None = None
    source_url: str | None = None
    data_year: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
