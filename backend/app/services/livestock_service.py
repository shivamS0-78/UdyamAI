"""Livestock Service for UdyamAI.

Provides reusable data-access functions for Livestock domain data.
"""

from uuid import UUID

from sqlmodel import Session, select

from app.models.livestock import Livestock


class LivestockService:
    @staticmethod
    def get_livestock_records(
        db: Session,
        location_id: UUID | None = None,
        animal_type: str | None = None,
        year: int | None = None,
        limit: int = 50,
    ) -> list[Livestock]:
        """List livestock records with optional filters.

        Args:
            db: Database session.
            location_id: Filter by village location UUID.
            animal_type: Filter by animal type (e.g. "cattle", "buffalo").
            year: Filter by year.
            limit: Maximum results (default 50, max 200).
        """
        limit = min(limit, 200)
        statement = select(Livestock).order_by(Livestock.animal_type)

        if location_id is not None:
            statement = statement.where(Livestock.location_id == location_id)
        if animal_type is not None:
            statement = statement.where(Livestock.animal_type == animal_type)
        if year is not None:
            statement = statement.where(Livestock.year == year)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_livestock_by_id(db: Session, livestock_id: UUID) -> Livestock | None:
        """Get a single livestock record by ID."""
        return db.get(Livestock, livestock_id)

    @staticmethod
    def get_animal_types(db: Session, location_id: UUID | None = None) -> list[str]:
        """Get distinct animal types available at a location."""
        from sqlalchemy import distinct

        statement = select(distinct(Livestock.animal_type)).where(
            Livestock.animal_type.is_not(None)
        )

        if location_id is not None:
            statement = statement.where(Livestock.location_id == location_id)

        statement = statement.order_by(Livestock.animal_type)
        return [row[0] for row in db.exec(statement).all()]
