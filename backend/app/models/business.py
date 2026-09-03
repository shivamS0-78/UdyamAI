from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.analysis import AnalysisRun
    from app.models.location import Village


class BusinessCategory(SQLModel, table=True):
    __tablename__ = "business_categories"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    sector: str | None = Field(default=None)
    description: str | None = Field(default=None)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    business_models: list["BusinessModel"] = Relationship(back_populates="business_category")
    businesses: list["Business"] = Relationship(back_populates="business_category")
    analysis_runs: list["AnalysisRun"] = Relationship(back_populates="business_category")


class BusinessModel(SQLModel, table=True):
    __tablename__ = "business_models"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    business_category_id: UUID = Field(foreign_key="business_categories.id", nullable=False)
    name: str = Field(nullable=False)
    description: str | None = Field(default=None)
    startup_cost_min: float | None = Field(default=None)
    startup_cost_max: float | None = Field(default=None)
    working_capital: float | None = Field(default=None)

    # JSON fields for assumptions
    revenue_assumptions: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    operating_cost_assumptions: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    risk_assumptions: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    business_category: BusinessCategory = Relationship(back_populates="business_models")


class Business(SQLModel, table=True):
    __tablename__ = "businesses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str | None = Field(default=None)
    business_category_id: UUID | None = Field(
        default=None, foreign_key="business_categories.id", nullable=True
    )
    location_id: UUID | None = Field(default=None, foreign_key="villages.id", nullable=True)
    district: str | None = Field(default=None)
    taluka: str | None = Field(default=None)
    village: str | None = Field(default=None)
    address: str | None = Field(default=None)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    geom: Any | None = Field(
        default=None,
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True
        ),
    )

    # Provenance fields
    source: str | None = Field(default=None)
    source_url: str | None = Field(default=None)
    data_year: int | None = Field(default=None)
    verified_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    business_category: BusinessCategory | None = Relationship(back_populates="businesses")
    location: Optional["Village"] = Relationship(back_populates="businesses")
