"""Find nearby markets using PostGIS radius queries."""

from sqlmodel import Session

from app.geo.radius import find_within_radius
from app.models.market import Market


def find_nearby_markets(
    db: Session,
    lat: float,
    lng: float,
    radius_km: float = 25.0,
    market_type: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Find markets within radius_km of (lat, lng).

    Uses PostGIS ST_DWithin on Market.geog for efficient spatial queries.
    Optionally filters by market type (e.g. "mandi", "retail", "wholesale").

    Args:
        db: Database session.
        lat: Center latitude.
        lng: Center longitude.
        radius_km: Search radius in kilometers (default 25, max 100).
        market_type: Optional filter by market type string.
        limit: Maximum results (default 50, max 200).

    Returns:
        List of market dicts with distance_meters included.
    """
    radius_km = min(radius_km, 100.0)

    # Push market type filter into the SQL query for efficiency
    filters = []
    if market_type is not None:
        filters.append(Market.market_type == market_type)

    return find_within_radius(
        db=db,
        model=Market,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        limit=limit,
        filters=filters or None,
    )
