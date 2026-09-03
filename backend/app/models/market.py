from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.analysis import AnalysisRun
    from app.models.location import Village


class Market(SQLModel, table=True):
    __tablename__ = "markets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str | None = Field(default=None)
    market_type: str | None = Field(default=None)
    location_id: UUID | None = Field(default=None, foreign_key="villages.id", nullable=True)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    geog: Any | None = Field(
        default=None,
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True
        ),
    )

    source: str | None = Field(default=None)
    source_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    location: Optional["Village"] = Relationship(back_populates="markets")
    prices: list["MarketPrice"] = Relationship(back_populates="market")


class MarketPrice(SQLModel, table=True):
    __tablename__ = "market_prices"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    market_id: UUID | None = Field(default=None, foreign_key="markets.id", nullable=True)
    location_id: UUID | None = Field(default=None, foreign_key="villages.id", nullable=True)

    market_name: str | None = Field(default=None)
    commodity: str | None = Field(default=None)
    commodity_variety: str | None = Field(default=None)
    unit: str | None = Field(default=None)

    min_price: float | None = Field(default=None)
    max_price: float | None = Field(default=None)
    modal_price: float | None = Field(default=None)
    arrival_quantity: float | None = Field(default=None)
    arrival_unit: str | None = Field(default=None)
    recorded_date: date | None = Field(default=None)

    source: str | None = Field(default=None)
    source_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    market: Market | None = Relationship(back_populates="prices")
    location: Optional["Village"] = Relationship(back_populates="market_prices")


class MarketAnalysis(SQLModel, table=True):
    __tablename__ = "market_analyses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    analysis_run_id: UUID = Field(foreign_key="analysis_runs.id", nullable=False)

    radius_km: float | None = Field(default=None)
    population_estimate: int | None = Field(default=None)
    household_estimate: int | None = Field(default=None)
    market_reach_estimate: int | None = Field(default=None)
    competitor_count: int | None = Field(default=None)

    # JSON indicators
    demand_indicators: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    distribution_channels: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    pricing_indicators: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    market_gaps: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    data_confidence: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    analysis_run: "AnalysisRun" = Relationship(back_populates="market_analyses")


class CompetitorAnalysis(SQLModel, table=True):
    __tablename__ = "competitor_analyses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    analysis_run_id: UUID = Field(foreign_key="analysis_runs.id", nullable=False)

    radius_km: float | None = Field(default=None)
    competitor_count: int | None = Field(default=None)
    competition_density: float | None = Field(default=None)

    # JSON distributions
    competitor_distribution: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    identified_gaps: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    data_confidence: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    analysis_run: "AnalysisRun" = Relationship(back_populates="competitor_analyses")
