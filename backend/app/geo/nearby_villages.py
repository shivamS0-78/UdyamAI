"""Find nearby villages using PostGIS radius queries."""

from uuid import UUID

from sqlmodel import Session

from app.geo.radius import find_within_radius
from app.models.location import Village


def find_nearby_villages(
    db: Session,
    lat: float,
    lng: float,
    radius_km: float = 10.0,
    district_id: UUID | None = None,
    limit: int = 50,
) -> list[dict]:
    """Find villages within radius_km of (lat, lng).

    Uses PostGIS ST_DWithin on Village.geom for efficient spatial queries.
    Optionally filters by district.

    Args:
        db: Database session.
        lat: Center latitude.
        lng: Center longitude.
        radius_km: Search radius in kilometers (default 10, max 50).
        district_id: Optional filter by District UUID.
        limit: Maximum results (default 50, max 200).

    Returns:
        List of village dicts with distance_meters included.
    """
    radius_km = min(radius_km, 50.0)

    # Push district filter into the SQL query for efficiency
    filters = []
    if district_id is not None:
        filters.append(Village.district_id == district_id)

    return find_within_radius(
        db=db,
        model=Village,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        limit=limit,
        filters=filters or None,
    )
