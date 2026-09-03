"""Weather Service for UdyamAI.

Provides reusable data-access functions for Weather domain data.
"""

from datetime import date
from uuid import UUID

from sqlmodel import Session, col, select

from app.models.weather import Weather


class WeatherService:
    @staticmethod
    def get_weather_records(
        db: Session,
        location_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        drought_only: bool = False,
        limit: int = 50,
    ) -> list[Weather]:
        """List weather records with optional filters.

        Args:
            db: Database session.
            location_id: Filter by village location UUID.
            start_date: Filter records on or after this date.
            end_date: Filter records on or before this date.
            drought_only: If True, return only drought-flagged records.
            limit: Maximum results (default 50, max 500).
        """
        limit = min(limit, 500)
        statement = select(Weather).order_by(col(Weather.date).desc())

        if location_id is not None:
            statement = statement.where(Weather.location_id == location_id)
        if start_date is not None:
            statement = statement.where(Weather.date >= start_date)
        if end_date is not None:
            statement = statement.where(Weather.date <= end_date)
        if drought_only:
            statement = statement.where(Weather.drought_indicator.is_(True))

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_weather_by_id(db: Session, weather_id: UUID) -> Weather | None:
        """Get a single weather record by ID."""
        return db.get(Weather, weather_id)
