"""Scheme Service for UdyamAI.

Provides reusable data-access functions for Scheme, SchemeRule,
SchemeEligibilityRule, and SchemeMatch domain data.

NOTE: This service provides DATA LOOKUP only. Eligibility checking,
scheme matching, and scoring logic belongs to Backend 1 (analysis engine).
"""

from datetime import date
from uuid import UUID

from sqlmodel import Session, col, select

from app.models.scheme import (
    Scheme,
    SchemeEligibilityRule,
    SchemeMatch,
    SchemeRule,
)


class SchemeService:
    # ------------------------------------------------------------------ #
    # Schemes
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_schemes(
        db: Session,
        state: str | None = None,
        agency_name: str | None = None,
        active_only: bool = True,
        limit: int = 50,
    ) -> list[Scheme]:
        """List schemes with optional filters.

        Args:
            db: Database session.
            state: Filter by state (e.g. "Maharashtra", "Central").
            agency_name: Filter by sponsoring agency (e.g. "KVIC", "NABARD").
            active_only: Only return active schemes (default True).
            limit: Maximum results (default 50, max 200).
        """
        limit = min(limit, 200)
        statement = select(Scheme).order_by(Scheme.name)

        if active_only:
            statement = statement.where(Scheme.active)
        if state is not None:
            statement = statement.where(Scheme.state == state)
        if agency_name is not None:
            statement = statement.where(Scheme.agency_name == agency_name)

        statement = statement.limit(limit)
        return db.exec(statement).all()

    @staticmethod
    def get_scheme_by_id(db: Session, scheme_id: UUID) -> Scheme | None:
        """Get a single scheme by ID."""
        return db.get(Scheme, scheme_id)

    @staticmethod
    def get_scheme_by_name(db: Session, name: str) -> Scheme | None:
        """Get a single scheme by exact name match."""
        statement = select(Scheme).where(Scheme.name == name).limit(1)
        return db.exec(statement).first()

    # ------------------------------------------------------------------ #
    # Scheme Rules
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_scheme_rules(
        db: Session,
        scheme_id: UUID,
        active_only: bool = True,
    ) -> list[SchemeRule]:
        """Get all rules for a scheme.

        Args:
            db: Database session.
            scheme_id: Scheme UUID to get rules for.
            active_only: If True, only return rules within effective date range.
        """
        statement = (
            select(SchemeRule)
            .where(SchemeRule.scheme_id == scheme_id)
            .order_by(col(SchemeRule.created_at).desc())
        )

        rules = db.exec(statement).all()

        if active_only:
            today = date.today()
            rules = [
                r
                for r in rules
                if (r.effective_from is None or r.effective_from <= today)
                and (r.effective_until is None or r.effective_until >= today)
            ]

        return rules

    @staticmethod
    def get_rule_by_id(db: Session, rule_id: UUID) -> SchemeRule | None:
        """Get a single scheme rule by ID."""
        return db.get(SchemeRule, rule_id)

    @staticmethod
    def get_latest_rule(db: Session, scheme_id: UUID) -> SchemeRule | None:
        """Get the most recent active rule for a scheme.

        Useful for getting the current/latest version of scheme parameters.
        """
        today = date.today()
        statement = (
            select(SchemeRule)
            .where(SchemeRule.scheme_id == scheme_id)
            .where((SchemeRule.effective_from.is_(None)) | (SchemeRule.effective_from <= today))
            .where((SchemeRule.effective_until.is_(None)) | (SchemeRule.effective_until >= today))
            .order_by(col(SchemeRule.created_at).desc())
            .limit(1)
        )
        return db.exec(statement).first()

    # ------------------------------------------------------------------ #
    # Scheme Eligibility Rules
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_eligibility_rules(
        db: Session,
        scheme_id: UUID,
    ) -> list[SchemeEligibilityRule]:
        """Get all eligibility rules for a scheme.

        Returns rules that define conditions for scheme eligibility
        (e.g. age range, income limit, category requirements).
        """
        statement = (
            select(SchemeEligibilityRule)
            .where(SchemeEligibilityRule.scheme_id == scheme_id)
            .order_by(SchemeEligibilityRule.rule_type)
        )
        return db.exec(statement).all()

    @staticmethod
    def get_eligibility_rules_by_type(
        db: Session,
        scheme_id: UUID,
        rule_type: str,
    ) -> list[SchemeEligibilityRule]:
        """Get eligibility rules filtered by rule type.

        Rule types include: "age", "income", "category", "location", "business", etc.
        """
        statement = (
            select(SchemeEligibilityRule)
            .where(SchemeEligibilityRule.scheme_id == scheme_id)
            .where(SchemeEligibilityRule.rule_type == rule_type)
            .order_by(SchemeEligibilityRule.field_name)
        )
        return db.exec(statement).all()

    # ------------------------------------------------------------------ #
    # Scheme Matches (data lookup only — no scoring logic)
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_scheme_matches(
        db: Session,
        analysis_run_id: UUID,
    ) -> list[SchemeMatch]:
        """Get existing scheme matches for an analysis run.

        NOTE: This retrieves PRE-COMPUTED matches. The actual matching
        logic (scoring, eligibility checking) is done by Backend 1.
        """
        statement = (
            select(SchemeMatch)
            .where(SchemeMatch.analysis_run_id == analysis_run_id)
            .order_by(col(SchemeMatch.match_score).desc())
        )
        return db.exec(statement).all()

    @staticmethod
    def get_match_by_id(db: Session, match_id: UUID) -> SchemeMatch | None:
        """Get a single scheme match by ID."""
        return db.get(SchemeMatch, match_id)

    # ------------------------------------------------------------------ #
    # Aggregation helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_states(db: Session) -> list[str]:
        """Get distinct states that have schemes."""
        from sqlalchemy import distinct

        statement = (
            select(distinct(Scheme.state)).where(Scheme.state.is_not(None)).order_by(Scheme.state)
        )
        return [row[0] for row in db.exec(statement).all()]

    @staticmethod
    def get_agencies(db: Session) -> list[str]:
        """Get distinct agency names."""
        from sqlalchemy import distinct

        statement = (
            select(distinct(Scheme.agency_name))
            .where(Scheme.agency_name.is_not(None))
            .order_by(Scheme.agency_name)
        )
        return [row[0] for row in db.exec(statement).all()]

    @staticmethod
    def get_rule_types(db: Session, scheme_id: UUID) -> list[str]:
        """Get distinct eligibility rule types for a scheme."""
        from sqlalchemy import distinct

        statement = (
            select(distinct(SchemeEligibilityRule.rule_type))
            .where(SchemeEligibilityRule.scheme_id == scheme_id)
            .where(SchemeEligibilityRule.rule_type.is_not(None))
            .order_by(SchemeEligibilityRule.rule_type)
        )
        return [row[0] for row in db.exec(statement).all()]
