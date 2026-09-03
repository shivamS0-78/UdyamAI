"""Population Service for UdyamAI.

Provides reusable data-access functions for Population domain data.
"""

from uuid import UUID

from sqlmodel import Session, col, select

from app.models.location import Population


class PopulationService:
    @staticmethod
    def get_population_records(
        db: Session,
        location_id: UUID | None = None,
        year: int | None = None,
        limit: int = 50,
    ) -> list[Population]:
        """List population records with optional filters.

        Args:
            db: Database session.
            location_id: Filter by village location UUID.
            year: Filter by census/survey year.
            limit: Maximum results (default 50, max 200).
        """
        limit = min(limit, 200)
        statement = select(Population).order_by(col(Population.year).desc())

        if location_id is not None:
            statement = statement.where(Population.location_id == location_id)
        if year is not None:
            statement = statement.where(Population.year == year)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_population_by_id(db: Session, population_id: UUID) -> Population | None:
        """Get a single population record by ID."""
        return db.get(Population, population_id)

    @staticmethod
    def get_available_years(db: Session, location_id: UUID | None = None) -> list[int]:
        """Get distinct years with population data."""
        from sqlalchemy import distinct

        statement = select(distinct(Population.year)).where(Population.year.is_not(None))

        if location_id is not None:
            statement = statement.where(Population.location_id == location_id)

        statement = statement.order_by(Population.year.desc())
        return [row[0] for row in db.exec(statement).all()]
