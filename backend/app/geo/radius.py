"""Core PostGIS radius query engine for UdyamAI.

Provides a generic `find_within_radius` function that works with any model
having a PostGIS Geography POINT column (Village, Business, Market, Infrastructure).
"""

from __future__ import annotations

from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import func, literal_column
from sqlalchemy.sql.elements import ClauseElement
from sqlmodel import Session, select

from app.geo.coordinates import km_to_meters

# ---------------------------------------------------------------------------
# Geo-column discovery
# ---------------------------------------------------------------------------

# Manual mapping kept as a fast-path / documentation of expected columns.
_GEO_COLUMN_MAP: dict[str, str] = {
    "Village": "geom",
    "Business": "geom",
    "Market": "geog",
    "Infrastructure": "geog",
}


def _introspect_geo_column(model: type) -> str | None:
    """Try to find a Geography column on *model* by inspecting its SA columns."""
    for attr_name in dir(model):
        try:
            attr = getattr(model, attr_name)
        except Exception:  # noqa: BLE001
            continue
        sa_col = getattr(attr, "property", None)
        if sa_col is None:
            continue
        col_type = getattr(
            sa_col.columns[0].type if hasattr(sa_col, "columns") else sa_col, "type", None
        )
        if isinstance(col_type, Geography):
            return attr_name
    return None


def _get_geo_column(model: type, *, explicit: str | None = None) -> str:
    """Get the PostGIS geography column name for a model.

    Resolution order:
    1. Explicit override passed by the caller.
    2. Hard-coded ``_GEO_COLUMN_MAP``.
    3. Introspection of the model's SA columns.
    """
    if explicit:
        return explicit

    model_name = model.__name__
    if model_name in _GEO_COLUMN_MAP:
        return _GEO_COLUMN_MAP[model_name]

    introspected = _introspect_geo_column(model)
    if introspected:
        return introspected

    raise ValueError(
        f"Model '{model_name}' has no known PostGIS geography column. "
        f"Known models: {list(_GEO_COLUMN_MAP.keys())}. "
        f"Pass an explicit geo_column or add an entry to _GEO_COLUMN_MAP."
    )


# ---------------------------------------------------------------------------
# Radius query
# ---------------------------------------------------------------------------


def _find_within_radius_sqlite_fallback(
    db: Session,
    model: type,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int = 50,
    filters: list[ClauseElement] | None = None,
) -> list[dict[str, Any]]:
    import math

    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r_earth = 6371000.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )
        return r_earth * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    stmt = select(model)
    if filters:
        for f in filters:
            stmt = stmt.where(f)

    all_records = db.exec(stmt).all()
    results: list[dict[str, Any]] = []
    radius_meters = radius_km * 1000.0

    for record in all_records:
        r_lat = getattr(record, "latitude", None)
        r_lng = getattr(record, "longitude", None)
        if r_lat is not None and r_lng is not None:
            dist = haversine(lat, lng, float(r_lat), float(r_lng))
            if dist <= radius_meters:
                record_dict = {
                    **{k: v for k, v in record.__dict__.items() if not k.startswith("_")},
                    "distance_meters": round(dist, 2),
                }
                results.append(record_dict)

    results.sort(key=lambda x: x["distance_meters"])
    return results[:limit]


def find_within_radius(
    db: Session,
    model: type,
    lat: float,
    lng: float,
    radius_km: float,
    limit: int = 50,
    *,
    filters: list[ClauseElement] | None = None,
    geo_column: str | None = None,
) -> list[dict[str, Any]]:
    """Find all records of *model* within *radius_km* of (lat, lng).

    Uses PostGIS ``ST_DWithin`` for efficient spatial queries on geography
    columns and returns results sorted nearest-first. Falls back to Python
    Haversine distance when PostGIS functions are unavailable (e.g. SQLite).
    """
    limit = min(limit, 500)
    radius_meters = km_to_meters(radius_km)
    geo_col = _get_geo_column(model, explicit=geo_column)

    geom = getattr(model, geo_col)
    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)

    # Fall back to lat/lng point when the geography column is unset
    lat_col = getattr(model, "latitude", None)
    lng_col = getattr(model, "longitude", None)
    if lat_col is not None and lng_col is not None:
        effective_geom = func.coalesce(
            geom,
            func.ST_SetSRID(func.ST_MakePoint(lng_col, lat_col), 4326),
        )
        spatial_where = func.ST_DWithin(
            effective_geom,
            point,
            radius_meters,
        )
        distance_expr = func.ST_Distance(effective_geom, point).label("distance_meters")
    else:
        spatial_where = func.ST_DWithin(geom, point, radius_meters)
        distance_expr = func.ST_Distance(geom, point).label("distance_meters")

    stmt = select(model, distance_expr).where(spatial_where)

    # Apply additional non-spatial filters in the DB
    if filters:
        for f in filters:
            stmt = stmt.where(f)

    stmt = stmt.order_by(literal_column("distance_meters")).limit(limit)

    try:
        rows = db.exec(stmt).all()
    except Exception as exc:
        if (
            "no such function" in str(exc).lower()
            or "sqlite" in str(getattr(db.bind, "dialect", "")).lower()
        ):
            return _find_within_radius_sqlite_fallback(
                db=db,
                model=model,
                lat=lat,
                lng=lng,
                radius_km=radius_km,
                limit=limit,
                filters=filters,
            )
        raise exc

    results: list[dict[str, Any]] = []
    for row in rows:
        record = row[0]  # The model instance
        distance = row[1]  # distance_meters
        record_dict = {
            **{k: v for k, v in record.__dict__.items() if not k.startswith("_")},
            "distance_meters": round(float(distance), 2),
        }
        results.append(record_dict)

    return results
