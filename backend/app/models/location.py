from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.agriculture import Agriculture
    from app.models.analysis import AnalysisRun
    from app.models.business import Business
    from app.models.economic import EconomicIndicator
    from app.models.infrastructure import Infrastructure
    from app.models.livestock import Livestock
    from app.models.market import Market, MarketPrice
    from app.models.user import Profile
    from app.models.weather import Weather


class District(SQLModel, table=True):
    __tablename__ = "districts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    state: str = Field(default="Maharashtra", nullable=False)
    lgd_code: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    talukas: list["Taluka"] = Relationship(back_populates="district")
    gram_panchayats: list["GramPanchayat"] = Relationship(back_populates="district")
    villages: list["Village"] = Relationship(back_populates="district")


class Taluka(SQLModel, table=True):
    __tablename__ = "talukas"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    district_id: UUID = Field(foreign_key="districts.id", nullable=False)
    lgd_code: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    district: District = Relationship(back_populates="talukas")
    gram_panchayats: list["GramPanchayat"] = Relationship(back_populates="taluka")
    villages: list["Village"] = Relationship(back_populates="taluka")


class GramPanchayat(SQLModel, table=True):
    __tablename__ = "gram_panchayats"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    taluka_id: UUID = Field(foreign_key="talukas.id", nullable=False)
    district_id: UUID = Field(foreign_key="districts.id", nullable=False)
    lgd_code: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    district: District = Relationship(back_populates="gram_panchayats")
    taluka: Taluka = Relationship(back_populates="gram_panchayats")
    villages: list["Village"] = Relationship(back_populates="gram_panchayat")


class Village(SQLModel, table=True):
    __tablename__ = "villages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    district_id: UUID = Field(foreign_key="districts.id", nullable=False)
    taluka_id: UUID = Field(foreign_key="talukas.id", nullable=False)
    gram_panchayat_id: UUID = Field(foreign_key="gram_panchayats.id", nullable=False)
    lgd_code: str | None = Field(default=None)
    pin_code: str | None = Field(default=None)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    geom: Any | None = Field(
        default=None,
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True
        ),
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    district: District = Relationship(back_populates="villages")
    taluka: Taluka = Relationship(back_populates="villages")
    gram_panchayat: GramPanchayat = Relationship(back_populates="villages")

    # User profiles & Analysis Runs
    profiles: list["Profile"] = Relationship(back_populates="location")
    analysis_runs: list["AnalysisRun"] = Relationship(back_populates="location")

    # Local Datasets Relationships
    population_records: list["Population"] = Relationship(back_populates="location")
    businesses: list["Business"] = Relationship(back_populates="location")
    agriculture_records: list["Agriculture"] = Relationship(back_populates="location")
    livestock_records: list["Livestock"] = Relationship(back_populates="location")
    economic_indicator_records: list["EconomicIndicator"] = Relationship(back_populates="location")
    infrastructure_records: list["Infrastructure"] = Relationship(back_populates="location")
    weather_records: list["Weather"] = Relationship(back_populates="location")
    markets: list["Market"] = Relationship(back_populates="location")
    market_prices: list["MarketPrice"] = Relationship(back_populates="location")


class Population(SQLModel, table=True):
    __tablename__ = "population"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    location_id: UUID = Field(foreign_key="villages.id", nullable=False)
    year: int = Field(nullable=False, index=True)
    population_total: int | None = Field(default=None)
    male_population: int | None = Field(default=None)
    female_population: int | None = Field(default=None)
    households: int | None = Field(default=None)
    working_population: int | None = Field(default=None)
    literacy_rate: float | None = Field(default=None)

    # Provenance fields
    source: str | None = Field(default=None)
    source_url: str | None = Field(default=None)
    data_year: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    location: Village = Relationship(back_populates="population_records")
