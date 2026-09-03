"""Data ingestion pipeline — CSV import with validation, normalization, provenance.

Public entrypoint: :func:`run_import`.
"""

from app.ingestion.importer import DOMAIN_SPECS, Provenance, run_import
from app.ingestion.report import ImportReport, RowError

__all__ = ["DOMAIN_SPECS", "ImportReport", "Provenance", "RowError", "run_import"]
