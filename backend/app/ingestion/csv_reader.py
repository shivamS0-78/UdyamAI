"""CSV reading for the ingestion pipeline — stdlib only."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawRow:
    """One CSV data row with its original file line number."""

    line_number: int
    data: dict[str, str]


def read_csv_rows(file_path: str | Path) -> list[RawRow]:
    """Read a CSV file into :class:`RawRow` objects.

    Handles a UTF-8 BOM, strips whitespace from headers and values, and
    skips fully blank lines.  ``line_number`` is 1-based and counts the
    header as line 1, so it matches what a spreadsheet editor shows.
    """
    rows: list[RawRow] = []
    with open(file_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return rows
        fieldnames = [(name or "").strip() for name in reader.fieldnames]
        for line_number, raw in enumerate(reader, start=2):
            data: dict[str, str] = {}
            has_value = False
            for key, value in zip(fieldnames, raw.values(), strict=False):
                key = key.strip()
                if not key:
                    continue
                value = (value or "").strip()
                if value:
                    has_value = True
                data[key] = value
            if not has_value:
                continue
            rows.append(RawRow(line_number=line_number, data=data))
    return rows
