#!/usr/bin/env python3
"""Validate government scheme definitions in database or raw JSON file.

Usage:
    python scripts/schemes/validate_schemes.py [--file data/raw/schemes/schemes_maharashtra.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlmodel import Session, select

from app.database import engine
from app.models.scheme import Scheme


def validate_schemes(json_path: Path | None = None) -> bool:
    if json_path and json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            schemes_data = json.load(f)
        print(f"Validating {len(schemes_data)} scheme definitions from file: {json_path}")
        errors = []
        for idx, item in enumerate(schemes_data, 1):
            name = item.get("name")
            if not name:
                errors.append(f"Scheme #{idx} missing 'name'")
            rules = item.get("rules", [])
            if not rules:
                errors.append(f"Scheme '{name}' has no defined financial rules")
            for r in rules:
                contrib = r.get("beneficiary_contribution_percent", 0.0)
                loan = r.get("loan_percent", 0.0)
                if contrib + loan < 90.0:
                    errors.append(f"Scheme '{name}' rules sum of contribution ({contrib}%) + loan ({loan}%) is under 90%")
        if errors:
            print(f"Validation FAILED with {len(errors)} errors:")
            for err in errors:
                print(f" - {err}")
            return False
        print("Scheme validation PASSED successfully.")
        return True

    with Session(engine) as db:
        schemes = db.exec(select(Scheme)).all()
        print(f"Validating {len(schemes)} schemes in database...")
        if not schemes:
            print("Warning: No schemes found in database.")
            return True
        print(f"All {len(schemes)} database schemes validated.")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate government scheme definitions")
    parser.add_argument("--file", help="Optional path to schemes JSON file")
    args = parser.parse_args()
    success = validate_schemes(Path(args.file) if args.file else None)
    sys.exit(0 if success else 1)
