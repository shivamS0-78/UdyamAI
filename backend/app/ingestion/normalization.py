"""Normalization helpers for the ingestion pipeline.

Pure helpers coerce raw CSV values into canonical Python types.  Missing
values become ``None`` — never fake zeros or sentinel dates.  Unparseable
values raise ``ValueError`` so the row is *rejected*, not silently fixed.

Also holds the DB-aware location resolution wrapper used by the importers.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session

from app.ingestion.report import ImportReport
from app.services.location_service import LocationService

# Raw values treated as "missing" (case-insensitive).  Government datasets
# commonly use NA / N/A / null / - for unknowns.
MISSING_MARKERS = {"", "na", "n/a", "null", "none", "-", "--"}


def clean_str(value: Any) -> str | None:
    """Strip whitespace; map missing markers to ``None``."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in MISSING_MARKERS:
        return None
    return text or None


def to_int(value: Any) -> int | None:
    """Parse an int from raw CSV text (tolerates ``1,234`` grouping)."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = clean_str(value)
    if text is None:
        return None
    try:
        return int(text.replace(",", "").strip())
    except ValueError:
        raise ValueError(f"cannot parse {value!r} as int") from None


def to_float(value: Any) -> float | None:
    """Parse a float from raw CSV text (tolerates ``1,234.5`` grouping)."""
    if value is None:
        return None
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    text = clean_str(value)
    if text is None:
        return None
    try:
        return float(text.replace(",", "").strip())
    except ValueError:
        raise ValueError(f"cannot parse {value!r} as float") from None


_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%m-%y")


def parse_date(value: Any) -> date | None:
    """Parse a date from raw CSV text (ISO or Indian DD/MM/YYYY)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = clean_str(value)
    if text is None:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"cannot parse {value!r} as date (expected YYYY-MM-DD or DD/MM/YYYY)")


def to_bool(value: Any) -> bool | None:
    """Parse a boolean from raw CSV text (true/false/yes/no/1/0)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = clean_str(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered in {"true", "yes", "y", "1"}:
        return True
    if lowered in {"false", "no", "n", "0"}:
        return False
    raise ValueError(f"cannot parse {value!r} as bool")


# ---------------------------------------------------------------------------
# Location resolution — DB-aware, wraps LocationService
# ---------------------------------------------------------------------------


def _resolve_one(
    db: Session,
    find_fn: Callable[[], Any],
    create_fn: Callable[[], UUID],
    name: str,
    report: ImportReport,
    label: str,
    allow_create: bool,
) -> tuple[UUID, bool]:
    """Find-or-create one hierarchy level.  Returns ``(id, was_created)``."""
    match = find_fn()
    if match:
        return match.id, False
    if not allow_create:
        raise ValueError(f"{label} {name!r} not found (dry-run: creation disabled)")
    record_id = create_fn()
    report.created_locations.append(f"{label}: {name}")
    return record_id, True


def _cache_key(level: str, *parts: Any) -> tuple[str, ...]:
    """Hashable cache key for one hierarchy-level resolution."""
    return (level, *[str(p) for p in parts if p is not None])


def resolve_village(
    db: Session,
    row: Any,
    report: ImportReport,
    allow_create: bool = True,
) -> UUID | None:
    """Resolve a row's location names to a canonical village UUID.

    Walks District → Taluka → GramPanchayat → Village via
    ``LocationService`` (LGD → exact → fuzzy chain).  Missing hierarchy
    records are created when ``allow_create`` is True (dry-run disables
    creation so nothing is written).

    Uses ``report.location_cache`` (when present) to memoize lookups for the
    duration of one import run — the same village appears on many rows, and
    every find_* call otherwise re-queries the database.

    Returns ``None`` when the row has no ``village_name``.  Raises
    ``ValueError`` when parents are missing or a lookup fails — the row is
    then rejected by the importer.
    """
    village_name = clean_str(getattr(row, "village_name", None))
    if not village_name:
        return None

    cache = report.location_cache if isinstance(report, ImportReport) else None

    state = clean_str(getattr(row, "state", None))
    lgd_code = clean_str(getattr(row, "lgd_code", None))
    district_id: UUID | None = None
    taluka_id: UUID | None = None
    gp_id: UUID | None = None

    district_name = clean_str(getattr(row, "district_name", None))
    if district_name:
        key = _cache_key("district", district_name, state)
        if cache is not None and key in cache:
            district_id = cache[key]
        else:
            district_id, _ = _resolve_one(
                db,
                find_fn=lambda: LocationService.find_district(db, district_name, state=state),
                create_fn=lambda: LocationService.resolve_location(
                    db, district_name, level="district", state=state
                ),
                name=district_name,
                report=report,
                label="district",
                allow_create=allow_create,
            )
            if cache is not None:
                cache[key] = district_id

    taluka_name = clean_str(getattr(row, "taluka_name", None))
    if taluka_name:
        if district_id is None:
            raise ValueError(f"taluka {taluka_name!r} given without district_name — cannot resolve")
        key = _cache_key("taluka", taluka_name, district_id)
        if cache is not None and key in cache:
            taluka_id = cache[key]
        else:
            taluka_id, _ = _resolve_one(
                db,
                find_fn=lambda: LocationService.find_taluka(
                    db, taluka_name, district_id=district_id
                ),
                create_fn=lambda: LocationService.resolve_location(
                    db, taluka_name, level="taluka", district_id=district_id
                ),
                name=taluka_name,
                report=report,
                label="taluka",
                allow_create=allow_create,
            )
            if cache is not None:
                cache[key] = taluka_id

    gp_name = clean_str(getattr(row, "gram_panchayat_name", None))
    if gp_name:
        if taluka_id is None:
            raise ValueError(
                f"gram panchayat {gp_name!r} given without taluka_name — cannot resolve"
            )
        key = _cache_key("gram_panchayat", gp_name, taluka_id, district_id)
        if cache is not None and key in cache:
            gp_id = cache[key]
        else:
            gp_id, _ = _resolve_one(
                db,
                find_fn=lambda: LocationService.find_gram_panchayat(
                    db, gp_name, taluka_id=taluka_id, district_id=district_id
                ),
                create_fn=lambda: LocationService.resolve_location(
                    db,
                    gp_name,
                    level="gram_panchayat",
                    taluka_id=taluka_id,
                    district_id=district_id,
                ),
                name=gp_name,
                report=report,
                label="gram_panchayat",
                allow_create=allow_create,
            )
            if cache is not None:
                cache[key] = gp_id

    if taluka_id is None:
        raise ValueError(
            f"cannot resolve village {village_name!r} without district_name and taluka_name"
        )

    key = _cache_key("village", village_name, taluka_id, lgd_code)
    if cache is not None and key in cache:
        village_id = cache[key]
    else:
        village_id, _ = _resolve_one(
            db,
            find_fn=lambda: LocationService.find_village(
                db, village_name, taluka_id=taluka_id, lgd_code=lgd_code
            ),
            create_fn=lambda: LocationService.resolve_location(
                db,
                village_name,
                level="village",
                district_id=district_id,
                taluka_id=taluka_id,
                gram_panchayat_id=gp_id,
                lgd_code=lgd_code,
            ),
            name=village_name,
            report=report,
            label="village",
            allow_create=allow_create,
        )
        if cache is not None:
            cache[key] = village_id
    return village_id
