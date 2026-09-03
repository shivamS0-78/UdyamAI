#!/usr/bin/env python3
"""Unified ingestion runner — one file, or every CSV under data/raw/<domain>/.

Usage:
    python scripts/data/import_all.py --domain population --file data/raw/population/file.csv
    python scripts/data/import_all.py --all [--dry-run]

With ``--all`` (and not ``--dry-run``) the run finishes by deriving
infrastructure facility records from the freshly imported markets and
businesses (see ``seed_infrastructure.py``).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

try:
    from app.ingestion.cli import run_cli_all
except ImportError as exc:
    print(
        f"Error: Failed to import ingestion pipeline: {exc}\n"
        "Make sure you run this script from the project root and that\n"
        "backend/app/ingestion/cli.py exists with all dependencies."
    )
    sys.exit(1)


def _seed_infrastructure() -> None:
    """Derive infrastructure records from the imported markets/businesses."""
    try:
        from seed_infrastructure import seed_infrastructure
    except ImportError as exc:
        print(f"Warning: could not import seed_infrastructure: {exc}")
        return
    seed_infrastructure()


if __name__ == "__main__":
    code = run_cli_all()
    if code == 0 and "--all" in sys.argv and "--dry-run" not in sys.argv:
        _seed_infrastructure()
    sys.exit(code)