#!/usr/bin/env python3
"""Combined importer: runs schemes + all domain CSV imports against Supabase.

Single init_db() call to avoid repeated schema-creation overhead (~28s each).
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "schemes"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "data"))

from app.database import get_engine, init_db
from app.ingestion.cli import run_cli_all
from import_schemes import import_schemes
from seed_infrastructure import seed_infrastructure

# ── Monkey-patch init_db to no-op (already called once) ────
import app.ingestion.cli as cli_mod
import import_schemes as schemes_mod
cli_mod.init_db = lambda: None
schemes_mod.init_db = lambda: None

t0 = time.time()
print("=" * 60, flush=True)
print("Phase 0: Creating schema (single init_db call)...", flush=True)
print("=" * 60, flush=True)
init_db()
print(f"  Schema ready in {time.time() - t0:.1f}s\n", flush=True)

# ── Phase 1: Schemes ───────────────────────────────────────
print("=" * 60, flush=True)
print("Phase 1: Importing government schemes...", flush=True)
print("=" * 60, flush=True)
t1 = time.time()
json_path = PROJECT_ROOT / "data" / "raw" / "schemes" / "schemes_master_dataset.json"
import_schemes(json_path, dry_run=False)
print(f"  Schemes done in {time.time() - t1:.1f}s\n", flush=True)

# ── Phase 2: All domain CSV data ───────────────────────────
print("=" * 60, flush=True)
print("Phase 2: Importing all domain CSV data...", flush=True)
print("=" * 60, flush=True)
t2 = time.time()
code = run_cli_all()
print(f"\n  All domain imports done in {time.time() - t2:.1f}s\n", flush=True)

# ── Phase 3: Seed infrastructure ───────────────────────────
if code == 0:
    print("=" * 60, flush=True)
    print("Phase 3: Seeding infrastructure records...", flush=True)
    print("=" * 60, flush=True)
    t3 = time.time()
    seed_infrastructure()
    print(f"  Infrastructure done in {time.time() - t3:.1f}s\n", flush=True)

total = time.time() - t0
print("=" * 60, flush=True)
print(f"ALL IMPORTS COMPLETE in {total:.1f}s", flush=True)
print("=" * 60, flush=True)
sys.exit(code)
