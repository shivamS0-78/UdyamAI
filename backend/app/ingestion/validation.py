"""Row validation for the ingestion pipeline.

One pydantic model per import domain.  Validation *rejects* bad rows — it
never silently coerces invalid values into placeholders.  Missing values
become ``None``; unparseable values raise ``ValidationError`` so the row is
rejected and logged in the :class:`ImportReport`.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ingestion.normalization import MISSING_MARKERS, parse_date, to_bool, to_float, to_int
from app.ingestion.report import ImportReport, RowError

__all__ = [
    "AgricultureRow",
    "BusinessRow",
    "ImportReport",
    "LivestockRow",
    "LocationRow",
    "LocationNamesMixin",
    "MarketPriceRow",
    "MarketRow",
    "PopulationRow",
    "RowError",
    "WeatherRow",
]


# ---------------------------------------------------------------------------
# Row models
# ---------------------------------------------------------------------------


class _CSVRow(BaseModel):
    """Base row model: ignores unknown columns, maps missing markers to None."""

    model_config = ConfigDict(extra="ignore")

    @field_validator("*", mode="before")
    @classmethod
    def _missing_to_none(cls, value):  # noqa: ANN001
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in MISSING_MARKERS:
                return None
        return value


class LocationNamesMixin(BaseModel):
    """Location-hierarchy columns shared by domain rows.

    All optional — each domain decides which are required.  ``village_name``
    plus ``district_name``/``taluka_name`` allow ``resolve_village`` to walk
    the hierarchy.
    """

    district_name: str | None = None
    taluka_name: str | None = None
    gram_panchayat_name: str | None = None
    village_name: str | None = None
    state: str | None = None
    lgd_code: str | None = None
    pin_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def _coords(cls, value):  # noqa: ANN001
        return to_float(value)


class PopulationRow(LocationNamesMixin, _CSVRow):
    """``population`` — Census-style village counts."""

    year: int
    population_total: int | None = None
    male_population: int | None = None
    female_population: int | None = None
    households: int | None = None
    working_population: int | None = None
    literacy_rate: float | None = None

    @field_validator(
        "year",
        "population_total",
        "male_population",
        "female_population",
        "households",
        "working_population",
        mode="before",
    )
    @classmethod
    def _ints(cls, value):  # noqa: ANN001
        return to_int(value)

    @field_validator("literacy_rate", mode="before")
    @classmethod
    def _floats(cls, value):  # noqa: ANN001
        return to_float(value)


class AgricultureRow(LocationNamesMixin, _CSVRow):
    """``agriculture`` — crop area / production per village-season."""

    crop_name: str = Field(min_length=1)
    crop_category: str | None = None
    cultivated_area: float | None = None
    production: float | None = None
    production_unit: str | None = None
    irrigated_area: float | None = None
    year: int | None = None
    season: str | None = None

    @field_validator("cultivated_area", "production", "irrigated_area", mode="before")
    @classmethod
    def _floats(cls, value):  # noqa: ANN001
        return to_float(value)

    @field_validator("year", mode="before")
    @classmethod
    def _year(cls, value):  # noqa: ANN001
        return to_int(value)


class LivestockRow(LocationNamesMixin, _CSVRow):
    """``livestock`` — animal counts / milk production per village."""

    animal_type: str = Field(min_length=1)
    animal_count: int | None = None
    milk_production: float | None = None
    milk_production_unit: str | None = None
    year: int | None = None

    @field_validator("animal_count", "year", mode="before")
    @classmethod
    def _ints(cls, value):  # noqa: ANN001
        return to_int(value)

    @field_validator("milk_production", mode="before")
    @classmethod
    def _floats(cls, value):  # noqa: ANN001
        return to_float(value)


class WeatherRow(LocationNamesMixin, _CSVRow):
    """``weather`` — daily station/observation records.  Location optional."""

    date: date
    rainfall_mm: float | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    drought_indicator: bool | None = None

    @field_validator("date", mode="before")
    @classmethod
    def _date(cls, value):  # noqa: ANN001
        return parse_date(value)

    @field_validator("rainfall_mm", "temperature_min", "temperature_max", mode="before")
    @classmethod
    def _floats(cls, value):  # noqa: ANN001
        return to_float(value)

    @field_validator("drought_indicator", mode="before")
    @classmethod
    def _bool(cls, value):  # noqa: ANN001
        return to_bool(value)


class MarketRow(LocationNamesMixin, _CSVRow):
    """``markets`` — physical market/mandi locations."""

    market_name: str = Field(min_length=1)
    market_type: str | None = None


class MarketPriceRow(LocationNamesMixin, _CSVRow):
    """``market_prices`` — Agmarknet-style daily commodity prices."""

    market_name: str | None = None
    market_type: str | None = None
    commodity: str = Field(min_length=1)
    commodity_variety: str | None = None
    unit: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    modal_price: float | None = None
    arrival_quantity: float | None = None
    arrival_unit: str | None = None
    recorded_date: date

    @field_validator("recorded_date", mode="before")
    @classmethod
    def _date(cls, value):  # noqa: ANN001
        return parse_date(value)

    @field_validator("min_price", "max_price", "modal_price", "arrival_quantity", mode="before")
    @classmethod
    def _floats(cls, value):  # noqa: ANN001
        return to_float(value)

    @model_validator(mode="after")
    def _needs_market_or_village(self) -> MarketPriceRow:
        if not self.market_name and not self.village_name:
            raise ValueError("market_name or village_name is required to place the price record")
        return self


class BusinessRow(LocationNamesMixin, _CSVRow):
    """``businesses`` — registered/surveyed businesses."""

    business_name: str = Field(min_length=1)
    category_name: str | None = None
    address: str | None = None


class LocationRow(LocationNamesMixin, _CSVRow):
    """Location hierarchy import — one village per row with its parents."""

    village_name: str = Field(min_length=1)
    district_name: str = Field(min_length=1)
    taluka_name: str = Field(min_length=1)
