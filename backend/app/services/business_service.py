"""Business Service for UdyamAI.

Provides reusable data-access functions for Business,
BusinessCategory, and BusinessModel domain data.
"""

from uuid import UUID

from sqlmodel import Session, select

from app.geo.nearby_businesses import find_nearby_businesses
from app.models.business import Business, BusinessCategory, BusinessModel


class BusinessService:
    # ------------------------------------------------------------------ #
    # Business categories
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_business_categories(db: Session) -> list[BusinessCategory]:
        statement = (
            select(BusinessCategory).where(BusinessCategory.active).order_by(BusinessCategory.name)
        )
        return db.exec(statement).all()

    # ------------------------------------------------------------------ #
    # Business models (reference/master data)
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_business_models(
        db: Session,
        business_category_id: UUID | None = None,
        limit: int = 100,
    ) -> list[BusinessModel]:
        """List business models with optional category filter."""
        limit = min(limit, 200)
        statement = select(BusinessModel).order_by(BusinessModel.name)

        if business_category_id is not None:
            statement = statement.where(BusinessModel.business_category_id == business_category_id)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    # ------------------------------------------------------------------ #
    # Businesses
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_businesses(
        db: Session,
        business_category_id: UUID | None = None,
        location_id: UUID | None = None,
        limit: int = 50,
    ) -> list[Business]:
        """List businesses with optional category and location filters."""
        limit = min(limit, 200)
        statement = select(Business).order_by(Business.created_at)

        if business_category_id is not None:
            statement = statement.where(Business.business_category_id == business_category_id)
        if location_id is not None:
            statement = statement.where(Business.location_id == location_id)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_business_by_id(db: Session, business_id: UUID) -> Business | None:
        return db.get(Business, business_id)

    @staticmethod
    def get_nearby_businesses(
        db: Session,
        lat: float,
        lng: float,
        radius_km: float = 10.0,
        category_id: UUID | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Find businesses within radius_km of (lat, lng) via PostGIS.

        Thin wrapper over the geo module so callers can stay at the
        service layer (see docs/architecture/data-flow.md).
        """
        return find_nearby_businesses(
            db=db,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            category_id=category_id,
            limit=limit,
        )
