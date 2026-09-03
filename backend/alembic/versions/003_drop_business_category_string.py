"""drop legacy free-text category column from businesses

The Business model now uses business_category_id (FK to business_categories)
instead of the free-text category string. This migration drops the old column.

Revision ID: 003_drop_business_category_string
Revises: 002_add_document_chunk_unique_constraint
Create Date: 2026-09-01 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "003_drop_business_category_string"
down_revision = "002_add_document_chunk_unique_constraint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("businesses"):
        return

    columns = [c["name"] for c in inspector.get_columns("businesses")]
    if "category" in columns:
        op.drop_column("businesses", "category")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("businesses"):
        return

    columns = [c["name"] for c in inspector.get_columns("businesses")]
    if "category" not in columns:
        op.add_column("businesses", sa.Column("category", sa.String(), nullable=True))
