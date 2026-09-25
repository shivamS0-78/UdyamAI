"""Backfill PostGIS geography columns from latitude/longitude.

Revision ID: 007_backfill_geo_columns
Revises: 005_add_hnsw_vector_index

``find_within_radius`` now filters on the geography column alone
(``ST_DWithin(geom, point, radius)``) so PostgreSQL can use the GiST indexes
created in 006. That drops the previous ``COALESCE(geom, make_point(lat, lng))``
fallback, which means a row whose geography column is unset is no longer found
by a radius search even when it carries valid coordinates.

The locations importer historically wrote ``latitude``/``longitude`` onto an
existing village without touching ``geom``, so such rows can exist. This
migration makes the geography column authoritative by deriving it from the
coordinates wherever it is missing, and the importer now keeps both in sync.

Idempotent: it only touches rows where the geography column is NULL and both
coordinates are present, so re-running finds nothing to do.
"""

import logging

from alembic import op

logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision = "009_backfill_geo_columns"
down_revision = "008_performance_indexes"
branch_labels = None
depends_on = None

# (table, geography column) pairs — the geo column differs per table.
_GEO_COLUMNS: tuple[tuple[str, str], ...] = (
    ("villages", "geom"),
    ("businesses", "geom"),
    ("markets", "geog"),
    ("infrastructure", "geog"),
)


def upgrade():
    bind = op.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return

    for table, geo_column in _GEO_COLUMNS:
        try:
            op.execute(
                f"""
                UPDATE {table}
                SET {geo_column} = ST_SetSRID(
                        ST_MakePoint(longitude, latitude), 4326
                    )::geography
                WHERE {geo_column} IS NULL
                  AND latitude IS NOT NULL
                  AND longitude IS NOT NULL
                """
            )
        except Exception as exc:
            logger.warning(
                "Could not backfill %s.%s from coordinates: %s",
                table,
                geo_column,
                exc,
            )


def downgrade():
    # Purely a data repair: the derived points are indistinguishable from, and
    # no less correct than, the coordinates they came from, so there is nothing
    # to undo.
    pass
