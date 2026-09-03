from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BusinessCategoryResponse(BaseModel):
    id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    sector: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class BusinessResponse(BaseModel):
    id: UUID
    name: str | None = None
    business_category_id: UUID | None = None
    location_id: UUID | None = None
    district: str | None = None
    taluka: str | None = None
    village: str | None = None
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    source: str | None = None
    source_url: str | None = None
    data_year: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BusinessModelResponse(BaseModel):
    id: UUID
    business_category_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    startup_cost_min: float | None = Field(default=None, ge=0, le=100_000_000.0)
    startup_cost_max: float | None = Field(default=None, ge=0, le=100_000_000.0)
    working_capital: float | None = Field(default=None, ge=0, le=100_000_000.0)
    active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}
