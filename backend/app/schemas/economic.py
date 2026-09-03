"""Pydantic response schemas for Economic indicator domain data."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EconomicIndicatorResponse(BaseModel):
    id: UUID
    location_id: UUID | None = None
    indicator_name: str | None = None
    indicator_value: float | None = None
    unit: str | None = None
    year: int | None = None
    source: str | None = None
    source_url: str | None = None
    data_year: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
