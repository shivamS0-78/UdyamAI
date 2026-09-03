"""Agriculture Service for UdyamAI.

Provides reusable data-access functions for Agriculture domain data.
"""

from uuid import UUID

from sqlmodel import Session, col, select

from app.models.agriculture import Agriculture


class AgricultureService:
    @staticmethod
    def get_agriculture_records(
        db: Session,
        location_id: UUID | None = None,
        crop_name: str | None = None,
        crop_category: str | None = None,
        season: str | None = None,
        year: int | None = None,
        limit: int = 50,
    ) -> list[Agriculture]:
        """List agriculture records with optional filters.

        Args:
            db: Database session.
            location_id: Filter by village location UUID.
            crop_name: Filter by crop name.
            crop_category: Filter by crop category (e.g. "cereals", "pulses").
            season: Filter by season (e.g. "kharif", "rabi").
            year: Filter by year.
            limit: Maximum results (default 50, max 200).
        """
        limit = min(limit, 200)
        statement = select(Agriculture).order_by(col(Agriculture.crop_name).asc())

        if location_id is not None:
            statement = statement.where(Agriculture.location_id == location_id)
        if crop_name is not None:
            statement = statement.where(Agriculture.crop_name == crop_name)
        if crop_category is not None:
            statement = statement.where(Agriculture.crop_category == crop_category)
        if season is not None:
            statement = statement.where(Agriculture.season == season)
        if year is not None:
            statement = statement.where(Agriculture.year == year)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_agriculture_by_id(db: Session, agriculture_id: UUID) -> Agriculture | None:
        """Get a single agriculture record by ID."""
        return db.get(Agriculture, agriculture_id)

    @staticmethod
    def get_crop_names(db: Session, location_id: UUID | None = None) -> list[str]:
        """Get distinct crop names available at a location."""
        from sqlalchemy import distinct

        statement = select(distinct(Agriculture.crop_name)).where(
            Agriculture.crop_name.is_not(None)
        )

        if location_id is not None:
            statement = statement.where(Agriculture.location_id == location_id)

        statement = statement.order_by(Agriculture.crop_name)
        return [row[0] for row in db.exec(statement).all()]

    @staticmethod
    def get_seasons(db: Session) -> list[str]:
        """Get distinct seasons in the database."""
        from sqlalchemy import distinct

        statement = (
            select(distinct(Agriculture.season))
            .where(Agriculture.season.is_not(None))
            .order_by(Agriculture.season)
        )
        return [row[0] for row in db.exec(statement).all()]
