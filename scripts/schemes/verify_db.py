#!/usr/bin/env python3
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
os.environ["DATABASE_URL"] = f"sqlite:///{(PROJECT_ROOT / 'udyamai.db').as_posix()}"

sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from sqlmodel import Session, select
from app.database import engine
from app.models.scheme import Scheme, SchemeRule, SchemeEligibilityRule

if __name__ == "__main__":
    with Session(engine) as db:
        schemes = db.exec(select(Scheme)).all()
        rules = db.exec(select(SchemeRule)).all()
        elig = db.exec(select(SchemeEligibilityRule)).all()
        print("\n================ DATABASE VERIFICATION REPORT ================", flush=True)
        print(f"Total Active Schemes in DB: {len(schemes)}", flush=True)
        print(f"Total Scheme Financial Rules in DB: {len(rules)}", flush=True)
        print(f"Total Scheme Eligibility Criteria in DB: {len(elig)}", flush=True)
        print("--------------------------------------------------------------", flush=True)
        for idx, s in enumerate(schemes, 1):
            print(f"{idx:02d}. [{s.state}] {s.name} | Agency: {s.agency_name}", flush=True)
        print("==============================================================\n", flush=True)
