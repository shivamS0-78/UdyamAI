"""Find nearby businesses using PostGIS radius queries."""

from uuid import UUID

from sqlmodel import Session, select

from app.geo.radius import find_within_radius
from app.models.business import Business, BusinessCategory


def _enrich_business_results(db: Session, results: list[dict]) -> list[dict]:
    """Attach human-readable category names to nearby business results."""
    if not results:
        return results

    category_ids = {
        row["business_category_id"]
        for row in results
        if row.get("business_category_id") is not None
    }
    if not category_ids:
        return results

    categories = db.exec(
        select(BusinessCategory).where(BusinessCategory.id.in_(category_ids))
    ).all()
    category_map = {cat.id: cat.name for cat in categories}

    enriched: list[dict] = []
    for row in results:
        cat_id = row.get("business_category_id")
        enriched.append(
            {
                **row,
                "category": category_map.get(cat_id) if cat_id else None,
            }
        )
    return enriched


def find_nearby_businesses(
    db: Session,
    lat: float,
    lng: float,
    radius_km: float = 10.0,
    category_id: UUID | None = None,
    limit: int = 50,
) -> list[dict]:
    """Find businesses within radius_km of (lat, lng).

    Uses PostGIS ST_DWithin on Business.geom for efficient spatial queries.
    Optionally filters by business category.

    Args:
        db: Database session.
        lat: Center latitude.
        lng: Center longitude.
        radius_km: Search radius in kilometers (default 10, max 50).
        category_id: Optional filter by BusinessCategory UUID.
        limit: Maximum results (default 50, max 500).

    Returns:
        List of business dicts with distance_meters included.
    """
    radius_km = min(radius_km, 50.0)

    # Push category filter into the SQL query for efficiency
    filters = []
    if category_id is not None:
        filters.append(Business.business_category_id == category_id)

    return _enrich_business_results(
        db,
        find_within_radius(
            db=db,
            model=Business,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            limit=limit,
            filters=filters or None,
        ),
    )
