"""Command-line interface for the data ingestion pipeline.

The ``scripts/data/import_*.py`` files are thin wrappers around
:func:`run_cli`; ``scripts/data/import_all.py`` wraps :func:`run_cli_all`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlmodel import Session

from app.database import engine, init_db
from app.ingestion.importer import DOMAIN_SPECS, run_import


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--file", required=False, help="Path to the CSV file to import")
    parser.add_argument("--dry-run", action="store_true", help="Validate only — write nothing")
    parser.add_argument("--source", help="Override the provenance source name")
    parser.add_argument("--source-url", help="Provenance: URL the dataset came from")
    parser.add_argument("--data-year", type=int, help="Provenance: reference year of the dataset")


def run_cli(domain: str, argv: list[str] | None = None) -> int:
    """Run one domain import from CLI args.  Returns a process exit code."""
    parser = argparse.ArgumentParser(description=f"Import {domain} CSV data into Supabase")
    _add_common_args(parser)
    if domain == "markets":
        parser.add_argument(
            "--kind",
            choices=["markets", "market_prices"],
            default="markets",
            help="Whether this CSV holds market locations or daily prices",
        )
    args = parser.parse_args(argv)

    actual_domain = args.kind if domain == "markets" else domain
    init_db()
    # expire_on_commit=False: run_import touches instance attributes (e.g. .id
    # when publishing created rows into the shared dedup-key map) after its
    # final commit; with the default True each access would re-SELECT the row
    # — an extra round-trip per created row against a high-latency DB.
    with Session(engine, expire_on_commit=False) as db:
        report = run_import(
            db,
            actual_domain,
            args.file,
            source=args.source,
            source_url=args.source_url,
            data_year=args.data_year,
            dry_run=args.dry_run,
        )
    print(report.summary())
    return 1 if report.rejected else 0


def run_cli_all(argv: list[str] | None = None) -> int:
    """Unified runner: one file via --domain/--file, or every CSV under data/raw/."""
    parser = argparse.ArgumentParser(
        description="Run data imports — a single file, or every CSV under data/raw/<domain>/"
    )
    parser.add_argument("--domain", choices=sorted(DOMAIN_SPECS), help="Domain to import")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Import every CSV found under data/raw/<domain>/ for every domain",
    )
    parser.add_argument(
        "--data-dir",
        default="data/raw",
        help="Root folder scanned in --all mode (default: data/raw)",
    )
    parser.add_argument(
        "--skip-samples",
        action="store_true",
        help="In --all mode, skip files named sample.csv (seed/test data)",
    )
    _add_common_args(parser)
    args = parser.parse_args(argv)

    jobs = []
    if args.all:
        domain_order = ["locations"] + [d for d in sorted(DOMAIN_SPECS) if d != "locations"]
        for domain in domain_order:
            domain_dir = Path(args.data_dir) / domain
            for csv_path in sorted(domain_dir.glob("*.csv")):
                if args.skip_samples and csv_path.name.lower() == "sample.csv":
                    print(f"  skipped sample/test file: {csv_path}")
                    continue
                jobs.append((domain, csv_path))

        if not jobs:
            print(f"no CSV files found under {args.data_dir}/")
            return 0
    elif args.domain and args.file:
        jobs = [(args.domain, args.file)]
    else:
        parser.error("either --all, or both --domain and --file, are required")
        return 2

    # One shared memo across every file so locations/markets/categories
    # resolved in an earlier file are reused, not re-queried per row.  The
    # dedup key map is shared too: each domain table is scanned once per run
    # instead of once per file.
    location_cache: dict = {}
    existing_keys: dict = {}
    any_rejected = False
    for domain, path in jobs:
        # See run_cli: expire_on_commit=False avoids a per-row refresh SELECT
        # when run_import reads back .id after its final commit.
        with Session(engine, expire_on_commit=False) as db:
            report = run_import(
                db,
                domain,
                path,
                source=args.source,
                source_url=args.source_url,
                data_year=args.data_year,
                dry_run=args.dry_run,
                location_cache=location_cache,
                existing_keys=existing_keys,
            )
        print(report.summary())
        print()
        if report.rejected:
            any_rejected = True
    return 1 if any_rejected else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_cli_all())
