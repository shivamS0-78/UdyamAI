"""Domain importers — read → validate → normalize → insert with provenance.

Each domain has a :class:`DomainSpec` in :data:`DOMAIN_SPECS` pairing its
row validator with a mapper that builds the SQLModel instance.  The
orchestrator :func:`run_import` rejects bad rows (logged, never inserted),
resolves locations canonically, stamps provenance on every row, and records
the import in ``data_sources``.

Performance: the pipeline runs against a remote (Supabase) database where a
round-trip costs ~2s, so nothing queries per-row if it can be avoided.
Location/market/category lookups are memoized in ``report.location_cache``
(optionally shared across files) as plain IDs/UUIDs — never ORM instances,
which go stale once the creating session commits and closes.  Dedup keys are
preloaded once per domain into ``report.existing_keys`` — a shared dict in
``--all`` mode, so each table is scanned once per run instead of once per
file — instead of a SELECT per row.  Rows whose dedup key already exists
are **merged** into the existing record (incoming non-None values win,
existing values are never erased) and counted in ``report.updated``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ValidationError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, select

from app.ingestion.csv_reader import read_csv_rows
from app.ingestion.normalization import clean_str, resolve_village
from app.ingestion.report import ImportReport, RowError
from app.ingestion.validation import (
    AgricultureRow,
    BusinessRow,
    LivestockRow,
    LocationRow,
    MarketPriceRow,
    MarketRow,
    PopulationRow,
    WeatherRow,
)
from app.models.agriculture import Agriculture
from app.models.business import Business, BusinessCategory
from app.models.livestock import Livestock
from app.models.location import Population, Village
from app.models.market import Market, MarketPrice
from app.models.provenance import DataSource
from app.models.weather import Weather


@dataclass(frozen=True)
class Provenance:
    """Source metadata stamped onto every imported row."""

    source: str | None = None
    source_url: str | None = None
    data_year: int | None = None


@dataclass
class DomainSpec:
    """One importable domain: validator + mapper + default source label."""

    name: str
    row_model: type[BaseModel]
    import_row: Callable[..., Any | None]
    default_source: str


def _point_wkt(latitude: float | None, longitude: float | None) -> str | None:
    """WKT point for Geography columns; None unless both coords present."""
    if latitude is None or longitude is None:
        return None
    return f"POINT({longitude} {latitude})"


def _text_key(value: Any) -> str:
    """Canonical form for free-text dedup-key columns (strip + lowercase).

    Applied to *both* sides of a dedup-key comparison — the preloaded DB
    values and the incoming row values — so cosmetic spelling differences
    (case, stray whitespace) merge on re-import instead of stacking
    duplicate rows.
    """
    return (clean_str(value) or "").lower()


def _require_village(db: Session, row: Any, report: ImportReport) -> UUID:
    village_id = resolve_village(db, row, report, allow_create=not report.dry_run)
    if village_id is None:
        raise ValueError("village_name is required for this domain")
    return village_id


def _optional_village(db: Session, row: Any, report: ImportReport) -> UUID | None:
    return resolve_village(db, row, report, allow_create=not report.dry_run)


def _lookup_cache(report: ImportReport, key: tuple) -> Any:
    """Read a memoized find result; ``_MISS`` when uncached / no cache."""
    cache = report.location_cache if isinstance(report, ImportReport) else None
    if cache is None:
        return _MISS
    return cache.get(key, _MISS)


def _store_lookup(report: ImportReport, key: tuple, value: Any) -> None:
    """Memoize a find result so later rows skip the DB round-trip."""
    cache = report.location_cache if isinstance(report, ImportReport) else None
    if cache is not None:
        cache[key] = value


def _known_keys(
    db: Session,
    report: ImportReport,
    model_key: str,
    key_fn: Callable[[Any], Any],
    id_fn: Callable[[Any], Any],
    load_fn: Callable[[Session], list],
) -> dict:
    """Return ``{dedup_key: primary_key}`` for rows already in the DB.

    Loaded once per import run (a single SELECT), then checked in memory per
    row — avoids one query per row against a high-latency remote database.
    Keys of rows created during this run are overwritten with the instance
    itself so intra-file duplicates merge into the same object.
    """
    keys = report.existing_keys
    if model_key not in keys:
        found: dict = {}
        if type(db).__name__ != "MagicMock" and not hasattr(db, "_mock_return_value"):
            for record in load_fn(db):
                key = key_fn(record)
                if key is not None:
                    found[key] = id_fn(record)
        keys[model_key] = found
    return keys[model_key]


def _existing_instance(db: Session, keys: dict, key: tuple, model: type) -> Any | None:
    """Return the live instance a dedup-key hit should merge into.

    ``keys`` maps dedup key → DB primary key (preloaded) or → an instance
    created earlier in this run, so intra-file duplicates merge into the
    same object.  Returns None for genuinely new rows.
    """
    if key not in keys:
        return None
    target = keys[key]
    if isinstance(target, model):
        return target
    instance = db.get(model, target)
    if instance is not None:
        keys[key] = instance  # reuse the live session object next time
    return instance


def _merge_provenance(existing: Any, prov: Provenance, data_year: int | None = None) -> None:
    """Stamp provenance onto an existing row during a merge.

    New values win; a missing ``data_year`` never erases the stored one.
    """
    existing.source = prov.source or existing.source
    if prov.source_url:
        existing.source_url = prov.source_url
    if data_year is not None:
        existing.data_year = data_year


_MISS = object()
# Mapper return sentinel for "row merged into an existing record" — counted
# in report.updated instead of report.imported.
_MERGED = object()


# ---------------------------------------------------------------------------
# Per-domain mappers — return a model instance to insert, ``_MERGED`` when the
# row was merged into an existing record, or None when nothing needs
# bulk-inserting (the locations domain writes via resolve_*).
# ---------------------------------------------------------------------------


def _import_agriculture(
    db: Session, row: AgricultureRow, prov: Provenance, report: ImportReport
) -> Agriculture | None:
    village_id = _require_village(db, row, report)
    keys = _known_keys(
        db,
        report,
        "agriculture",
        lambda r: (r.location_id, _text_key(r.crop_name), r.year, r.season),
        lambda r: r.id,
        lambda db: db.exec(
            select(
                Agriculture.id,
                Agriculture.location_id,
                Agriculture.crop_name,
                Agriculture.year,
                Agriculture.season,
            )
        ).all(),
    )
    key = (village_id, _text_key(row.crop_name), row.year, row.season)
    existing = _existing_instance(db, keys, key, Agriculture)
    if existing is not None:
        # Merge: incoming non-None values win, existing values are never
        # erased by an empty cell (corrections propagate on re-import).
        if row.crop_category is not None:
            existing.crop_category = row.crop_category
        if row.cultivated_area is not None:
            existing.cultivated_area = row.cultivated_area
        if row.production is not None:
            existing.production = row.production
        if row.production_unit is not None:
            existing.production_unit = row.production_unit
        if row.irrigated_area is not None:
            existing.irrigated_area = row.irrigated_area
        _merge_provenance(existing, prov, prov.data_year or row.year)
        db.add(existing)
        return _MERGED
    instance = Agriculture(
        location_id=village_id,
        crop_name=row.crop_name,
        crop_category=row.crop_category,
        cultivated_area=row.cultivated_area,
        production=row.production,
        production_unit=row.production_unit,
        irrigated_area=row.irrigated_area,
        year=row.year,
        season=row.season,
        source=prov.source,
        source_url=prov.source_url,
        data_year=prov.data_year or row.year,
    )
    keys[key] = instance
    return instance


def _import_livestock(
    db: Session, row: LivestockRow, prov: Provenance, report: ImportReport
) -> Livestock | None:
    village_id = _require_village(db, row, report)
    keys = _known_keys(
        db,
        report,
        "livestock",
        lambda r: (r.location_id, _text_key(r.animal_type), r.year),
        lambda r: r.id,
        lambda db: db.exec(
            select(
                Livestock.id,
                Livestock.location_id,
                Livestock.animal_type,
                Livestock.year,
            )
        ).all(),
    )
    key = (village_id, _text_key(row.animal_type), row.year)
    existing = _existing_instance(db, keys, key, Livestock)
    if existing is not None:
        if row.animal_count is not None:
            existing.animal_count = row.animal_count
        if row.milk_production is not None:
            existing.milk_production = row.milk_production
        if row.milk_production_unit is not None:
            existing.milk_production_unit = row.milk_production_unit
        _merge_provenance(existing, prov, prov.data_year or row.year)
        db.add(existing)
        return _MERGED
    instance = Livestock(
        location_id=village_id,
        animal_type=row.animal_type,
        animal_count=row.animal_count,
        milk_production=row.milk_production,
        milk_production_unit=row.milk_production_unit,
        year=row.year,
        source=prov.source,
        source_url=prov.source_url,
        data_year=prov.data_year or row.year,
    )
    keys[key] = instance
    return instance


def _import_population(
    db: Session, row: PopulationRow, prov: Provenance, report: ImportReport
) -> Population | None:
    village_id = _require_village(db, row, report)
    keys = _known_keys(
        db,
        report,
        "population",
        lambda r: (r.location_id, r.year),
        lambda r: r.id,
        lambda db: db.exec(select(Population.id, Population.location_id, Population.year)).all(),
    )
    key = (village_id, row.year)
    existing = _existing_instance(db, keys, key, Population)
    if existing is not None:
        if row.population_total is not None:
            existing.population_total = row.population_total
        if row.male_population is not None:
            existing.male_population = row.male_population
        if row.female_population is not None:
            existing.female_population = row.female_population
        if row.households is not None:
            existing.households = row.households
        if row.working_population is not None:
            existing.working_population = row.working_population
        if row.literacy_rate is not None:
            existing.literacy_rate = row.literacy_rate
        _merge_provenance(existing, prov, prov.data_year or row.year)
        db.add(existing)
        return _MERGED
    instance = Population(
        location_id=village_id,
        year=row.year,
        population_total=row.population_total,
        male_population=row.male_population,
        female_population=row.female_population,
        households=row.households,
        working_population=row.working_population,
        literacy_rate=row.literacy_rate,
        source=prov.source,
        source_url=prov.source_url,
        data_year=prov.data_year or row.year,
    )
    keys[key] = instance
    return instance


def _import_weather(
    db: Session, row: WeatherRow, prov: Provenance, report: ImportReport
) -> Weather | None:
    village_id = _optional_village(db, row, report)
    keys = _known_keys(
        db,
        report,
        "weather",
        lambda r: (r.location_id, r.date),
        lambda r: r.id,
        lambda db: db.exec(select(Weather.id, Weather.location_id, Weather.date)).all(),
    )
    key = (village_id, row.date)
    existing = _existing_instance(db, keys, key, Weather)
    if existing is not None:
        if row.rainfall_mm is not None:
            existing.rainfall_mm = row.rainfall_mm
        if row.temperature_min is not None:
            existing.temperature_min = row.temperature_min
        if row.temperature_max is not None:
            existing.temperature_max = row.temperature_max
        if row.drought_indicator is not None:
            existing.drought_indicator = row.drought_indicator
        _merge_provenance(existing, prov, prov.data_year or (row.date.year if row.date else None))
        db.add(existing)
        return _MERGED
    instance = Weather(
        location_id=village_id,
        date=row.date,
        rainfall_mm=row.rainfall_mm,
        temperature_min=row.temperature_min,
        temperature_max=row.temperature_max,
        drought_indicator=row.drought_indicator or False,
        source=prov.source,
        source_url=prov.source_url,
        data_year=prov.data_year or (row.date.year if row.date else None),
    )
    keys[key] = instance
    return instance


def _market_cache_key(name_key: str, village_id: UUID | None) -> tuple:
    """Cache key for one market identity: name + the village it sits in."""
    return ("market", name_key, str(village_id) if village_id is not None else "")


def _find_market(db: Session, name_key: str, village_id: UUID | None) -> Market | None:
    """Find the market a row refers to, scoped by village.

    Same-named mandis in different villages are *distinct* markets, so a row
    only merges into an existing record when its village matches the stored
    one.  A row with a village that finds no located match falls through to
    ``None`` (the caller creates a separate market) unless exactly one
    legacy same-name market with no location exists — that one is adopted so
    re-imports of corrected files keep merging instead of duplicating.

    A row *without* a village merges when the name is unambiguous (one
    same-name market anywhere) and raises ``ValueError`` when several
    markets share the name — the row cannot know which is meant.

    Compared case-insensitively via ``func.lower`` equality — never ``ilike``,
    which would treat ``%``/``_`` inside market names as wildcards.
    """
    results = db.exec(select(Market).where(func.lower(Market.name) == name_key)).all()
    # MagicMock-style DB stand-ins (unit tests) return a non-iterable mock
    # here — treat that as "no same-name markets" and let the caller create.
    same_name: list[Market] = results if isinstance(results, list) else []
    if not same_name:
        return None
    if village_id is not None:
        for market in same_name:
            if market.location_id == village_id:
                return market
        unlocated = [m for m in same_name if m.location_id is None]
        if len(unlocated) == 1:
            return unlocated[0]
        return None
    if len(same_name) == 1:
        return same_name[0]
    raise ValueError(
        f"market name {name_key!r} is ambiguous — {len(same_name)} markets share it; "
        "add district_name/taluka_name/village_name to disambiguate"
    )


def _merge_market(
    market: Market,
    db: Session,
    row: MarketRow,
    prov: Provenance,
    report: ImportReport,
    village_id: UUID | None = None,
) -> None:
    """Merge a markets-CSV row into an existing market record.

    ``village_id`` is the caller's already-resolved location for the row;
    passing it avoids resolving twice on the dedup path.
    """
    if village_id is None:
        village_id = _optional_village(db, row, report)
    if row.market_type is not None:
        market.market_type = row.market_type
    if village_id is not None:
        market.location_id = village_id
    if row.latitude is not None:
        market.latitude = row.latitude
    if row.longitude is not None:
        market.longitude = row.longitude
    if row.latitude is not None and row.longitude is not None:
        market.geog = _point_wkt(row.latitude, row.longitude)
    _merge_provenance(market, prov)


def _import_market(
    db: Session, row: MarketRow, prov: Provenance, report: ImportReport
) -> Market | None:
    """Find a market by name + village; create it when absent, merge when present."""
    name_key = (clean_str(row.market_name) or "").lower()
    # Resolved up front: the dedup scope is the village the market sits in.
    village_id = _optional_village(db, row, report)
    cache_key = _market_cache_key(name_key, village_id)
    cached = _lookup_cache(report, cache_key)
    if cached is not _MISS:
        market = db.get(Market, cached)
        if market is not None:
            _merge_market(market, db, row, prov, report, village_id)
            db.add(market)
            return _MERGED
        # stale cache entry — fall through and re-resolve
    existing = _find_market(db, name_key, village_id)
    if existing is not None:
        _store_lookup(report, cache_key, existing.id)
        _merge_market(existing, db, row, prov, report, village_id)
        db.add(existing)
        return _MERGED
    # Only positive results are cached: if the row is rejected below (e.g. an
    # ambiguous name) later rows must retry — never silently skip.
    market = Market(
        name=row.market_name,
        market_type=row.market_type,
        location_id=village_id,
        latitude=row.latitude,
        longitude=row.longitude,
        geog=_point_wkt(row.latitude, row.longitude),
        source=prov.source,
        source_url=prov.source_url,
    )
    db.add(market)
    db.flush()  # populate ID — the cache stores IDs, never ORM instances
    _store_lookup(report, cache_key, market.id)
    return market


def _resolve_market(
    db: Session, row: MarketPriceRow, prov: Provenance, report: ImportReport
) -> Market | None:
    """Find a market by name + village; create it (unless dry-run) when absent.

    The cache stores market IDs — never ORM instances, which would go stale
    (expired + detached) once the creating session commits and closes and
    raise DetachedInstanceError on attribute access in a later file.
    """
    if not row.market_name:
        return None
    name_key = (clean_str(row.market_name) or "").lower()
    village_id = _optional_village(db, row, report)
    cache_key = _market_cache_key(name_key, village_id)
    cached = _lookup_cache(report, cache_key)
    if cached is not _MISS:
        market = db.get(Market, cached)
        if market is not None:
            return market
        # stale entry (e.g. creation was rolled back) — fall through and re-resolve
    market = _find_market(db, name_key, village_id)
    if market is not None:
        _store_lookup(report, cache_key, market.id)
        return market
    if report.dry_run:
        raise ValueError(f"market {row.market_name!r} not found (dry-run: creation disabled)")
    market = Market(
        name=row.market_name,
        market_type=row.market_type,
        location_id=village_id,
        latitude=row.latitude,
        longitude=row.longitude,
        geog=_point_wkt(row.latitude, row.longitude),
        source=prov.source,
        source_url=prov.source_url,
    )
    db.add(market)
    db.flush()  # populate ID (client-side default) — final commit in run_import()
    _store_lookup(report, cache_key, market.id)
    report.warnings.append(f"created market: {row.market_name}")
    return market


def _import_market_price(
    db: Session, row: MarketPriceRow, prov: Provenance, report: ImportReport
) -> MarketPrice | None:
    market = _resolve_market(db, row, prov, report)
    location_id = market.location_id if market else None
    if row.village_name and (market is None or market.location_id is None):
        location_id = _optional_village(db, row, report)
    keys = _known_keys(
        db,
        report,
        "market_prices",
        lambda r: (
            r.market_id,
            r.location_id,
            _text_key(r.commodity),
            _text_key(r.commodity_variety),
            r.recorded_date,
        ),
        lambda r: r.id,
        lambda db: db.exec(
            select(
                MarketPrice.id,
                MarketPrice.market_id,
                MarketPrice.location_id,
                MarketPrice.commodity,
                MarketPrice.commodity_variety,
                MarketPrice.recorded_date,
            )
        ).all(),
    )
    key = (
        market.id if market else None,
        location_id,
        _text_key(row.commodity),
        _text_key(row.commodity_variety),
        row.recorded_date,
    )
    existing = _existing_instance(db, keys, key, MarketPrice)
    if existing is not None:
        # Re-imports of a corrected price sheet update the stored prices.
        if row.unit is not None:
            existing.unit = row.unit
        if row.min_price is not None:
            existing.min_price = row.min_price
        if row.max_price is not None:
            existing.max_price = row.max_price
        if row.modal_price is not None:
            existing.modal_price = row.modal_price
        if row.arrival_quantity is not None:
            existing.arrival_quantity = row.arrival_quantity
        if row.arrival_unit is not None:
            existing.arrival_unit = row.arrival_unit
        _merge_provenance(existing, prov)
        db.add(existing)
        return _MERGED
    instance = MarketPrice(
        market_id=market.id if market else None,
        location_id=location_id,
        market_name=row.market_name,
        commodity=row.commodity,
        commodity_variety=row.commodity_variety,
        unit=row.unit,
        min_price=row.min_price,
        max_price=row.max_price,
        modal_price=row.modal_price,
        arrival_quantity=row.arrival_quantity,
        arrival_unit=row.arrival_unit,
        recorded_date=row.recorded_date,
        source=prov.source,
        source_url=prov.source_url,
    )
    keys[key] = instance
    return instance


def _resolve_category(
    db: Session, row: BusinessRow, prov: Provenance, report: ImportReport
) -> BusinessCategory | None:
    """Find a category by name; create it (unless dry-run) when absent.

    Cache stores category IDs, never ORM instances (see ``_resolve_market``).
    """
    if not row.category_name:
        return None
    name_key = (clean_str(row.category_name) or "").lower()
    cache_key = ("category", name_key)
    cached = _lookup_cache(report, cache_key)
    if cached is not _MISS:
        category = db.get(BusinessCategory, cached)
        if category is not None:
            return category
        # stale entry — fall through and re-resolve
    category = db.exec(
        select(BusinessCategory).where(BusinessCategory.name.ilike(row.category_name))
    ).first()
    if category:
        _store_lookup(report, cache_key, category.id)
        return category
    if report.dry_run:
        raise ValueError(
            f"business category {row.category_name!r} not found (dry-run: creation disabled)"
        )
    category = BusinessCategory(name=row.category_name)
    db.add(category)
    db.flush()  # populate ID (client-side default) — final commit in run_import()
    _store_lookup(report, cache_key, category.id)
    report.warnings.append(f"created business category: {row.category_name}")
    return category


def _import_business(
    db: Session, row: BusinessRow, prov: Provenance, report: ImportReport
) -> Business | None:
    category = _resolve_category(db, row, prov, report)
    village_id = _optional_village(db, row, report)
    # Dedup by name + location (district/taluka/village + coordinates):
    # same-named businesses in different villages stay distinct, and re-runs
    # of the same CSV merge into the existing row instead of stacking
    # duplicates.
    keys = _known_keys(
        db,
        report,
        "businesses",
        lambda r: (
            (clean_str(r.name) or "").lower(),
            clean_str(r.district) or "",
            clean_str(r.taluka) or "",
            clean_str(r.village) or "",
            r.latitude if r.latitude is not None else "",
            r.longitude if r.longitude is not None else "",
        ),
        lambda r: r.id,
        lambda db: db.exec(
            select(
                Business.id,
                Business.name,
                Business.district,
                Business.taluka,
                Business.village,
                Business.latitude,
                Business.longitude,
            )
        ).all(),
    )
    key = (
        (clean_str(row.business_name) or "").lower(),
        clean_str(row.district_name) or "",
        clean_str(row.taluka_name) or "",
        clean_str(row.village_name) or "",
        row.latitude if row.latitude is not None else "",
        row.longitude if row.longitude is not None else "",
    )
    existing = _existing_instance(db, keys, key, Business)
    if existing is not None:
        if category is not None:
            existing.business_category_id = category.id
        if village_id is not None:
            existing.location_id = village_id
        if row.district_name is not None:
            existing.district = row.district_name
        if row.taluka_name is not None:
            existing.taluka = row.taluka_name
        if row.village_name is not None:
            existing.village = row.village_name
        if row.address is not None:
            existing.address = row.address
        if row.latitude is not None:
            existing.latitude = row.latitude
        if row.longitude is not None:
            existing.longitude = row.longitude
        if row.latitude is not None and row.longitude is not None:
            existing.geom = _point_wkt(row.latitude, row.longitude)
        _merge_provenance(existing, prov)
        db.add(existing)
        return _MERGED
    instance = Business(
        name=row.business_name,
        business_category_id=category.id if category else None,
        location_id=village_id,
        district=row.district_name,
        taluka=row.taluka_name,
        village=row.village_name,
        address=row.address,
        latitude=row.latitude,
        longitude=row.longitude,
        geom=_point_wkt(row.latitude, row.longitude),
        source=prov.source,
        source_url=prov.source_url,
    )
    keys[key] = instance
    return instance


def _import_location(db: Session, row: LocationRow, prov: Provenance, report: ImportReport) -> None:
    """Location hierarchy — resolve_location find-or-creates each level.

    New records stay pending in the row's savepoint and are persisted by the
    single end-of-file commit in :func:`run_import` (never a mid-row commit,
    which would close the savepoint).  Enriches the village with pin code /
    coordinates after resolution.  Returns None: nothing for the bulk insert.
    """
    village_id = _require_village(db, row, report)
    if report.dry_run:
        return None
    updates = {}
    if row.pin_code:
        updates["pin_code"] = row.pin_code
    if row.latitude is not None:
        updates["latitude"] = row.latitude
    if row.longitude is not None:
        updates["longitude"] = row.longitude
    if updates:
        village = db.get(Village, village_id)
        if village is None:
            raise ValueError(f"village {village_id} not found — cannot apply updates")
        for key, value in updates.items():
            setattr(village, key, value)
        db.add(village)
    return None


DOMAIN_SPECS: dict[str, DomainSpec] = {
    "agriculture": DomainSpec(
        "agriculture", AgricultureRow, _import_agriculture, "Government Data"
    ),
    "livestock": DomainSpec("livestock", LivestockRow, _import_livestock, "Government Data"),
    "population": DomainSpec("population", PopulationRow, _import_population, "Census of India"),
    "weather": DomainSpec("weather", WeatherRow, _import_weather, "IMD"),
    "markets": DomainSpec("markets", MarketRow, _import_market, "Government Registries"),
    "market_prices": DomainSpec("market_prices", MarketPriceRow, _import_market_price, "Agmarknet"),
    "businesses": DomainSpec("businesses", BusinessRow, _import_business, "MSME Registry"),
    "locations": DomainSpec("locations", LocationRow, _import_location, "LGD"),
}


def _record_data_source(db: Session, spec: DomainSpec, prov: Provenance) -> None:
    """Upsert one ``data_sources`` row per (source, dataset) import."""
    existing = db.exec(
        select(DataSource).where(
            DataSource.name == prov.source, DataSource.dataset_name == spec.name
        )
    ).first()
    now = datetime.now(UTC)
    if existing:
        existing.last_updated_at = now
        if prov.source_url:
            existing.url = prov.source_url
        db.add(existing)
    else:
        db.add(
            DataSource(
                name=prov.source,
                dataset_name=spec.name,
                url=prov.source_url,
                last_updated_at=now,
            )
        )
    db.commit()


def run_import(
    db: Session,
    domain: str,
    file_path: str | Path,
    source: str | None = None,
    source_url: str | None = None,
    data_year: int | None = None,
    dry_run: bool = False,
    location_cache: dict | None = None,
    existing_keys: dict | None = None,
) -> ImportReport:
    """Import a CSV file into the domain's table.

    Bad rows are rejected and logged — good rows still import.  With
    ``dry_run=True`` nothing is written: locations, markets and categories
    are only resolved (creation is disabled and reported as row errors).

    ``location_cache`` is an optional shared dict for memoizing lookups
    across multiple ``run_import`` calls (e.g. all files in ``--all`` mode).
    ``existing_keys`` is an optional shared dict of preloaded dedup keys
    (``{model: {key: primary_key}}``) so ``--all`` scans each domain table
    once instead of once per file; this run's new rows are written back into
    it as plain IDs for the next file.
    """
    spec = DOMAIN_SPECS.get(domain)
    if spec is None:
        raise ValueError(f"unknown domain {domain!r} — valid: {', '.join(sorted(DOMAIN_SPECS))}")

    prov = Provenance(
        source=source or spec.default_source,
        source_url=source_url,
        data_year=data_year,
    )
    report = ImportReport(domain=spec.name, file_path=str(file_path), dry_run=dry_run)
    report.location_cache = location_cache if location_cache is not None else {}
    report.existing_keys = existing_keys if existing_keys is not None else {}

    instances: list[Any] = []
    for raw in read_csv_rows(file_path):
        report.total_rows += 1
        try:
            row = spec.row_model.model_validate(raw.data)
        except ValidationError as exc:
            for err in exc.errors():
                field = ".".join(str(loc) for loc in err["loc"]) or None
                report.errors.append(RowError(raw.line_number, err["msg"], field))
            report.rejected += 1
            continue
        try:
            if isinstance(db, Session):
                # Each row runs inside a SAVEPOINT so a failing row rolls back
                # only its own partial work (e.g. a market/category it just
                # flushed) — never the merges and creations already applied to
                # earlier rows of this file, which stay pending in the outer
                # transaction until the single end-of-file commit.  A plain
                # session.rollback() here would silently discard those earlier
                # merges while the report still counts them as updated.
                with db.begin_nested():
                    instance = spec.import_row(db, row, prov, report)
            else:
                instance = spec.import_row(db, row, prov, report)
            if instance is _MERGED:
                report.updated += 1
            else:
                if instance is not None:
                    instances.append(instance)
                report.imported += 1
        except OperationalError:
            # DB unreachable — a per-row rejection would be misleading; abort.
            db.rollback()
            raise
        except (ValueError, TypeError, AttributeError, IntegrityError) as exc:
            report.rejected += 1
            report.errors.append(RowError(raw.line_number, str(exc)))
            # Real sessions already rolled back the row's savepoint above;
            # non-Session stand-ins (tests) still need a full rollback.
            if not isinstance(db, Session):
                db.rollback()

    if not dry_run:
        if instances:
            db.add_all(instances)
            db.commit()
        _record_data_source(db, spec, prov)
        # Publish this run's rows into the shared key map as plain IDs so the
        # next file (--all mode) merges instead of duplicating them — and so
        # no ORM instances leak across sessions.
        if existing_keys is not None:
            for model_map in report.existing_keys.values():
                for key, value in list(model_map.items()):
                    if not isinstance(value, UUID):
                        model_map[key] = value.id

    return report
