#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Force SQLite database URL for fast offline execution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
os.environ["DATABASE_URL"] = f"sqlite:///{(PROJECT_ROOT / 'udyamai.db').as_posix()}"
os.environ["ALLOW_SQLITE_FALLBACK"] = "true"

sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "schemes"))

from import_schemes import import_schemes

if __name__ == "__main__":
    json_path = PROJECT_ROOT / "data" / "raw" / "schemes" / "schemes_master_dataset.json"
    print(f"Importing {json_path} into SQLite database...", flush=True)
    import_schemes(json_path, dry_run=False)
    print("Database import complete!", flush=True)
