"""Infrastructure Service for UdyamAI.

Provides reusable data-access functions for Infrastructure domain data.
"""

from uuid import UUID

from sqlmodel import Session, select

from app.models.infrastructure import Infrastructure


class InfrastructureService:
    @staticmethod
    def get_infrastructure(
        db: Session,
        location_id: UUID | None = None,
        facility_type: str | None = None,
        limit: int = 50,
    ) -> list[Infrastructure]:
        """List infrastructure records with optional filters.

        Args:
            db: Database session.
            location_id: Filter by village location UUID.
            facility_type: Filter by facility type (e.g. "hospital", "school").
            limit: Maximum results (default 50, max 200).
        """
        limit = min(limit, 200)
        statement = select(Infrastructure).order_by(Infrastructure.name)

        if location_id is not None:
            statement = statement.where(Infrastructure.location_id == location_id)
        if facility_type is not None:
            statement = statement.where(Infrastructure.facility_type == facility_type)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_infrastructure_by_id(db: Session, infrastructure_id: UUID) -> Infrastructure | None:
        """Get a single infrastructure record by ID."""
        return db.get(Infrastructure, infrastructure_id)

    @staticmethod
    def get_facility_types(db: Session) -> list[str]:
        """Get distinct facility types in the database."""
        from sqlalchemy import distinct

        statement = (
            select(distinct(Infrastructure.facility_type))
            .where(Infrastructure.facility_type.is_not(None))
            .order_by(Infrastructure.facility_type)
        )
        return [row[0] for row in db.exec(statement).all()]
