#!/usr/bin/env python3
"""Import official government schemes and eligibility rules into database.

Usage:
    python scripts/schemes/import_schemes.py [--file data/raw/schemes/schemes_master_dataset.json] [--dry-run]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from uuid import uuid4

from sqlalchemy import delete
from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.provenance import DataSource
from app.models.scheme import Scheme, SchemeEligibilityRule, SchemeRule


def _clear_scheme_children(db: Session, scheme_id) -> None:
    db.exec(delete(SchemeRule).where(SchemeRule.scheme_id == scheme_id))
    db.exec(delete(SchemeEligibilityRule).where(SchemeEligibilityRule.scheme_id == scheme_id))


def import_schemes(json_path: Path, dry_run: bool = False) -> None:
    init_db()
    if not json_path.exists():
        print(f"Error: file not found: {json_path}", flush=True)
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    imported_count = 0
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    with Session(engine) as db:
        for item in data:
            name = item.get("name")
            if not name:
                continue

            existing = db.exec(select(Scheme).where(Scheme.name == name)).first()
            if existing:
                scheme = existing
                scheme.description = item.get("description", scheme.description)
                scheme.agency_name = item.get("agency_name", scheme.agency_name)
                scheme.state = item.get("state", scheme.state)
                scheme.official_url = item.get("official_url", scheme.official_url)
                scheme.source = item.get("source", scheme.source)
                scheme.last_verified_at = now_utc
                db.add(scheme)
            else:
                scheme = Scheme(
                    id=uuid4(),
                    name=name,
                    description=item.get("description"),
                    agency_name=item.get("agency_name"),
                    state=item.get("state", "Maharashtra"),
                    official_url=item.get("official_url"),
                    source=item.get("source", "Government Scheme Portal"),
                    active=item.get("active", True),
                    last_verified_at=now_utc,
                )
                db.add(scheme)

            if not dry_run:
                db.commit()
                db.refresh(scheme)
            else:
                db.flush()

            _clear_scheme_children(db, scheme.id)

            # Process SchemeRules
            for r in item.get("rules", []):
                eff_from = (
                    datetime.strptime(r["effective_from"], "%Y-%m-%d").date()
                    if r.get("effective_from")
                    else None
                )
                rule = SchemeRule(
                    scheme_id=scheme.id,
                    min_project_cost=r.get("min_project_cost"),
                    max_project_cost=r.get("max_project_cost"),
                    beneficiary_contribution_percent=r.get("beneficiary_contribution_percent"),
                    loan_percent=r.get("loan_percent"),
                    max_loan_amount=r.get("max_loan_amount"),
                    interest_rate=r.get("interest_rate"),
                    tenure_months=r.get("tenure_months"),
                    moratorium_months=r.get("moratorium_months"),
                    payment_frequency=r.get("payment_frequency", "monthly"),
                    eligible_business_categories=r.get("eligible_business_categories"),
                    eligible_locations=r.get("eligible_locations"),
                    eligible_beneficiary_categories=r.get("eligible_beneficiary_categories"),
                    other_conditions=r.get("other_conditions"),
                    effective_from=eff_from,
                )
                db.add(rule)

            # Process SchemeEligibilityRules
            for er in item.get("eligibility_rules", []):
                elig_rule = SchemeEligibilityRule(
                    scheme_id=scheme.id,
                    rule_type=er.get("rule_type"),
                    field_name=er.get("field_name"),
                    operator=er.get("operator"),
                    expected_value=er.get("expected_value"),
                    description=er.get("description"),
                )
                db.add(elig_rule)

            imported_count += 1
            if not dry_run:
                db.commit()

        # Record data source provenance
        ds = db.exec(
            select(DataSource).where(
                DataSource.name == "Government Scheme Registries", DataSource.dataset_name == "schemes"
            )
        ).first()
        if not ds:
            ds = DataSource(
                name="Government Scheme Registries",
                dataset_name="schemes",
                url="https://myscheme.gov.in",
                last_updated_at=now_utc,
            )
            db.add(ds)

        if not dry_run:
            db.commit()
            print(f"Successfully imported/updated {imported_count} government schemes.", flush=True)
        else:
            db.rollback()
            print(f"Dry-run: validated {imported_count} government schemes.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import government schemes JSON into database")
    parser.add_argument(
        "--file", default="data/raw/schemes/schemes_master_dataset.json", help="Path to schemes JSON"
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    args = parser.parse_args()
    import_schemes(Path(args.file), dry_run=args.dry_run)
