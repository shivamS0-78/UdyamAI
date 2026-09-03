"""add unique constraint to document chunks

Revision ID: 002_add_document_chunk_unique_constraint
Revises: 001_add_finance_fields
Create Date: 2026-08-31 15:13:00.000000

"""

import sqlalchemy as sa

from alembic import op

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import UserDefinedType

    class Vector(UserDefinedType):
        def __init__(self, dim=None):
            self.dim = dim

        def get_col_spec(self, **kw):
            return f"VECTOR({self.dim})" if self.dim else "VECTOR"


# revision identifiers, used by Alembic.
revision = "002_add_document_chunk_unique_constraint"
down_revision = "001_add_finance_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Alter alembic_version table's version_num column length to VARCHAR(64) on PostgreSQL
    if bind is not None and bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")

    # Check and create 'documents' table if it doesn't exist
    if not inspector.has_table("documents"):
        op.create_table(
            "documents",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("source_name", sa.String(255), nullable=False),
            sa.Column("source_url", sa.String(), nullable=True),
            sa.Column("document_type", sa.String(100), nullable=False),
            sa.Column("language", sa.String(10), nullable=False),
            sa.Column("file_path", sa.String(), nullable=True),
            sa.Column("published_date", sa.Date(), nullable=True),
            sa.Column("effective_from", sa.Date(), nullable=True),
            sa.Column("effective_until", sa.Date(), nullable=True),
            sa.Column("last_verified_at", sa.DateTime(), nullable=True),
            sa.Column("content_hash", sa.String(64), unique=True, index=True, nullable=False),
            sa.Column("active", sa.Boolean(), index=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    # Check and create 'document_chunks' table if it doesn't exist
    if not inspector.has_table("document_chunks"):
        op.create_table(
            "document_chunks",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column(
                "document_id", sa.UUID(), sa.ForeignKey("documents.id"), nullable=False, index=True
            ),
            sa.Column("scheme_id", sa.UUID(), nullable=True),
            sa.Column("chunk_index", sa.Integer(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("page_number", sa.Integer(), nullable=True),
            sa.Column("section_title", sa.String(), nullable=True),
            sa.Column("embedding", Vector(1536), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    # Add unique constraint to document_chunks table using batch mode for SQLite compatibility
    existing_constraints = [c["name"] for c in inspector.get_unique_constraints("document_chunks")]
    if "uq_document_chunk_index" not in existing_constraints:
        with op.batch_alter_table("document_chunks", schema=None) as batch_op:
            batch_op.create_unique_constraint(
                "uq_document_chunk_index", ["document_id", "chunk_index"]
            )


def downgrade() -> None:
    # Drop unique constraint from document_chunks table using batch mode for SQLite compatibility
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("document_chunks"):
        existing_constraints = [
            c["name"] for c in inspector.get_unique_constraints("document_chunks")
        ]
        if "uq_document_chunk_index" in existing_constraints:
            with op.batch_alter_table("document_chunks", schema=None) as batch_op:
                batch_op.drop_constraint("uq_document_chunk_index", type_="unique")
