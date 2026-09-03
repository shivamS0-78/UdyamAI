"""update scheme_matches match_status enum values

Migration to update match_status enum values from legacy states (not_matched, insufficient_information)
to canonical states (potential_match, not_match, missing_information, verification_required)
and enforce database-level check constraints.

Revision ID: 004_update_scheme_match_status_enum
Revises: 003_drop_business_category_string
Create Date: 2026-09-01 14:50:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "004_update_scheme_match_status_enum"
down_revision = "003_drop_business_category_string"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("scheme_matches"):
        return

    # Update existing legacy data records
    op.execute(
        "UPDATE scheme_matches SET match_status = 'not_match' WHERE match_status = 'not_matched';"
    )
    op.execute(
        "UPDATE scheme_matches SET match_status = 'missing_information' WHERE match_status = 'insufficient_information';"
    )

    # Drop existing check constraint if using PostgreSQL or SQLite with check constraints
    try:
        op.drop_constraint("scheme_matches_match_status_check", "scheme_matches", type_="check")
    except Exception:
        pass

    # Create new check constraint
    try:
        op.create_check_constraint(
            "scheme_matches_match_status_check",
            "scheme_matches",
            "match_status IN ('potential_match', 'not_match', 'missing_information', 'verification_required')",
        )
    except Exception:
        pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("scheme_matches"):
        return

    op.execute(
        "UPDATE scheme_matches SET match_status = 'not_matched' WHERE match_status = 'not_match';"
    )
    op.execute(
        "UPDATE scheme_matches SET match_status = 'insufficient_information' WHERE match_status = 'missing_information';"
    )

    try:
        op.drop_constraint("scheme_matches_match_status_check", "scheme_matches", type_="check")
    except Exception:
        pass

    try:
        op.create_check_constraint(
            "scheme_matches_match_status_check",
            "scheme_matches",
            "match_status IN ('potential_match', 'not_matched', 'insufficient_information')",
        )
    except Exception:
        pass
