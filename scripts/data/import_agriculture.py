#!/usr/bin/env python3
"""Import agriculture (crop area/production) CSVs into the agriculture table.

Usage:
    python scripts/data/import_agriculture.py --file data/raw/agriculture/file.csv [--dry-run]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

try:
    from app.ingestion.cli import run_cli
except ImportError as exc:
    print(
        f"Error: Failed to import ingestion pipeline: {exc}\n"
        "Make sure you run this script from the project root and that\n"
        "backend/app/ingestion/cli.py exists with all dependencies."
    )
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(run_cli("agriculture"))
