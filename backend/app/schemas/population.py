"""Pydantic response schemas for Population domain data."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PopulationResponse(BaseModel):
    id: UUID
    location_id: UUID
    year: int
    population_total: int | None = Field(default=None, ge=0)
    male_population: int | None = Field(default=None, ge=0)
    female_population: int | None = Field(default=None, ge=0)
    households: int | None = Field(default=None, ge=0)
    working_population: int | None = Field(default=None, ge=0)
    literacy_rate: float | None = Field(default=None, ge=0, le=100)
    source: str | None = None
    source_url: str | None = None
    data_year: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
