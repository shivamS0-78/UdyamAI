"""Import report types — outcome of one ingestion run."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RowError:
    """One rejected row — where it failed and why."""

    line_number: int
    message: str
    field: str | None = None

    def __str__(self) -> str:
        where = f" [{self.field}]" if self.field else ""
        return f"line {self.line_number}{where}: {self.message}"


@dataclass
class ImportReport:
    """Outcome of one :func:`app.ingestion.run_import` call."""

    domain: str
    file_path: str
    dry_run: bool = False
    total_rows: int = 0
    imported: int = 0
    updated: int = 0
    rejected: int = 0
    errors: list[RowError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    created_locations: list[str] = field(default_factory=list)
    # In-memory resolution cache shared across the whole import run, so the
    # same district/taluka/village/market/category is resolved once instead of
    # re-queried on every row (critical when the DB round-trip is ~2s).
    location_cache: dict | None = None
    # Fresh per-run store of already-known dedup keys, keyed by model name.
    existing_keys: dict | None = None

    def summary(self) -> str:
        """Human-readable one-import summary (printed by the CLI scripts)."""
        mode = " (dry-run)" if self.dry_run else ""
        lines = [
            f"[{self.domain}] {self.file_path}{mode}",
            f"  rows: {self.total_rows} | imported: {self.imported} | rejected: {self.rejected}",
        ]
        if self.updated:
            lines.append(f"  rows updated (merged): {self.updated}")
        if self.created_locations:
            lines.append(f"  locations created: {len(self.created_locations)}")
        for warning in self.warnings:
            lines.append(f"  warning: {warning}")
        for error in self.errors:
            lines.append(f"  error: {error}")
        return "\n".join(lines)
