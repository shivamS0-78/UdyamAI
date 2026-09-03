from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.location import Village


class Infrastructure(SQLModel, table=True):
    __tablename__ = "infrastructure"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    location_id: UUID | None = Field(default=None, foreign_key="villages.id", nullable=True)
    facility_type: str | None = Field(default=None)
    name: str | None = Field(default=None)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    geog: Any | None = Field(
        default=None,
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True
        ),
    )

    distance_from_village: float | None = Field(default=None)
    capacity: float | None = Field(default=None)

    # Provenance fields
    source: str | None = Field(default=None)
    source_url: str | None = Field(default=None)
    data_year: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    location: Optional["Village"] = Relationship(back_populates="infrastructure_records")
