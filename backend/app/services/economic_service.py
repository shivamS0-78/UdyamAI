"""Economic Indicator Service for UdyamAI.

Provides reusable data-access functions for EconomicIndicator domain data.
"""

from uuid import UUID

from sqlmodel import Session, select

from app.models.economic import EconomicIndicator


class EconomicService:
    @staticmethod
    def get_economic_indicators(
        db: Session,
        location_id: UUID | None = None,
        indicator_name: str | None = None,
        year: int | None = None,
        limit: int = 50,
    ) -> list[EconomicIndicator]:
        """List economic indicator records with optional filters.

        Args:
            db: Database session.
            location_id: Filter by village location UUID.
            indicator_name: Filter by indicator name (e.g. "GDP_per_capita").
            year: Filter by year.
            limit: Maximum results (default 50, max 200).
        """
        limit = min(limit, 200)
        statement = select(EconomicIndicator).order_by(EconomicIndicator.indicator_name)

        if location_id is not None:
            statement = statement.where(EconomicIndicator.location_id == location_id)
        if indicator_name is not None:
            statement = statement.where(EconomicIndicator.indicator_name == indicator_name)
        if year is not None:
            statement = statement.where(EconomicIndicator.year == year)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_economic_indicator_by_id(db: Session, indicator_id: UUID) -> EconomicIndicator | None:
        """Get a single economic indicator record by ID."""
        return db.get(EconomicIndicator, indicator_id)

    @staticmethod
    def get_indicator_names(db: Session, location_id: UUID | None = None) -> list[str]:
        """Get distinct indicator names available at a location."""
        from sqlalchemy import distinct

        statement = select(distinct(EconomicIndicator.indicator_name)).where(
            EconomicIndicator.indicator_name.is_not(None)
        )

        if location_id is not None:
            statement = statement.where(EconomicIndicator.location_id == location_id)

        statement = statement.order_by(EconomicIndicator.indicator_name)
        return [row[0] for row in db.exec(statement).all()]
