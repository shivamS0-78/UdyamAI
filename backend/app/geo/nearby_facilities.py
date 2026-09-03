"""Find nearby infrastructure facilities using PostGIS radius queries."""

from sqlmodel import Session

from app.geo.radius import find_within_radius
from app.models.infrastructure import Infrastructure


def find_nearby_facilities(
    db: Session,
    lat: float,
    lng: float,
    radius_km: float = 10.0,
    facility_type: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Find infrastructure facilities within radius_km of (lat, lng).

    Uses PostGIS ST_DWithin on Infrastructure.geog for efficient spatial queries.
    Optionally filters by facility type (e.g. "hospital", "bank", "road").

    Args:
        db: Database session.
        lat: Center latitude.
        lng: Center longitude.
        radius_km: Search radius in kilometers (default 10, max 50).
        facility_type: Optional filter by facility type string.
        limit: Maximum results (default 50, max 200).

    Returns:
        List of infrastructure dicts with distance_meters included.
    """
    radius_km = min(radius_km, 50.0)

    # Push facility type filter into the SQL query for efficiency
    filters = []
    if facility_type is not None:
        filters.append(Infrastructure.facility_type == facility_type)

    return find_within_radius(
        db=db,
        model=Infrastructure,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        limit=limit,
        filters=filters or None,
    )
