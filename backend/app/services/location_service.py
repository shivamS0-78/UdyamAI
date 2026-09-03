"""Location service — CRUD, name normalization, matching, resolution, and deduplication."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from uuid import UUID

from sqlmodel import Session, select

from app.models.location import District, GramPanchayat, Taluka, Village

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Suffixes to strip during normalization (case-insensitive)
_LOCATION_SUFFIXES = [
    "district",
    "taluka",
    "tehsil",
    "village",
    "gram panchayat",
    "panchayat",
    "nagar panchayat",
    "municipal council",
    "municipal corporation",
    "city",
    "town",
]

# Articles / filler words to remove
_FILLER_WORDS = {"the", "of", "and", "or", "at", "in", "on", "for", "to", "a", "an"}

# Default fuzzy matching threshold
DEFAULT_FUZZY_THRESHOLD = 0.85

# Domain tables that reference villages.id via location_id — used for FK
# re-parenting during village-level merges.
_VILLAGE_FK_TABLES: list[tuple[str, str]] = [
    ("agriculture", "location_id"),
    ("analysis_runs", "location_id"),
    ("businesses", "location_id"),
    ("competitor_analyses", "location_id"),
    ("economic_indicators", "location_id"),
    ("infrastructure", "location_id"),
    ("livestock", "location_id"),
    ("market_analyses", "location_id"),
    ("market_prices", "location_id"),
    ("markets", "location_id"),
    ("population", "location_id"),
    ("profiles", "location_id"),
    ("weather", "location_id"),
]


# ---------------------------------------------------------------------------
# Name Normalization  (pure functions — no DB dependency)
# ---------------------------------------------------------------------------


def _strip_accents(text: str) -> str:
    """Remove diacritical marks (accents) from Unicode text."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")


def normalize_name(name: str) -> str:
    """Lowercase, strip accents, collapse whitespace, strip."""
    text = _strip_accents(name.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_suffixes(name: str) -> str:
    """Remove common location-type suffixes from a normalized name."""
    text = name
    for suffix in _LOCATION_SUFFIXES:
        # Match suffix at end of string, word-boundary aware
        pattern = r"\b" + re.escape(suffix) + r"\s*$"
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text.strip()


def remove_fillers(name: str) -> str:
    """Remove filler words (articles, prepositions) from a normalized name."""
    words = name.split()
    cleaned = [w for w in words if w not in _FILLER_WORDS]
    return " ".join(cleaned)


def remove_punctuation(name: str) -> str:
    """Replace parentheses and special chars with spaces, then re-collapse."""
    text = re.sub(r"[()\[\]{}.,;:!?\"'/\\@#$%^&*+=|<>~`-]", " ", name)
    return re.sub(r"\s+", " ", text).strip()


def normalize_for_match(name: str) -> str:
    """Full normalization pipeline: produce a canonical form for matching.

    Steps: strip accents → lowercase → remove punctuation → remove suffixes →
    remove fillers → collapse whitespace.
    """
    text = normalize_name(name)
    text = remove_punctuation(text)
    text = remove_suffixes(text)
    text = remove_fillers(text)
    text = re.sub(r"\s+", " ", text).strip()
    # If normalization yields empty string (e.g. input was only a suffix),
    # fall back to the original stripped/lowercased name.
    if not text:
        text = normalize_name(name)
    return text


# ---------------------------------------------------------------------------
# Matching  (DB-aware — LGD code → exact → fuzzy)
# ---------------------------------------------------------------------------


def _fuzzy_ratio(a: str, b: str) -> float:
    """Return similarity ratio between two strings (0.0–1.0)."""
    return SequenceMatcher(None, a, b).ratio()


def _in_savepoint(db) -> bool:
    """True when *db* is a real session inside a nested (savepoint) transaction."""
    if type(db).__name__ == "MagicMock":
        return False  # mocks report truthy for everything — treat as top-level
    try:
        return bool(db.in_nested_transaction())
    except (AttributeError, TypeError):  # non-Session stand-ins (tests)
        return False


def _persist_new(db, record) -> UUID:
    """Add + flush a record, committing only when NOT inside a savepoint.

    The ingestion pipeline wraps each imported row in ``db.begin_nested()``.
    An inner ``db.commit()`` would close the savepoint's transaction, so any
    later statement in that row (e.g. the ``refresh`` below) fails with
    "Can't operate on closed transaction inside context manager".  Inside a
    savepoint the record stays pending in the outer transaction and is
    persisted by the pipeline's end-of-file commit; outside one the commit is
    kept so standalone callers still see the record immediately.
    """
    # No refresh after flush: id and created_at are client-side defaults, so
    # the id is already populated — and refresh() inside a savepoint can fail
    # on some servers once the outer transaction is long-lived.
    db.add(record)
    db.flush()
    if not _in_savepoint(db):
        db.commit()
    return record.id


class LocationService:
    """Unified location service: CRUD, normalization, matching, resolution, dedup."""

    # -----------------------------------------------------------------------
    # Basic Queries (existing)
    # -----------------------------------------------------------------------

    @staticmethod
    def get_districts(db: Session) -> list[District]:
        statement = select(District).order_by(District.name)
        return db.exec(statement).all()

    @staticmethod
    def get_talukas(db: Session, district_id: UUID | None = None) -> list[Taluka]:
        statement = select(Taluka)
        if district_id:
            statement = statement.where(Taluka.district_id == district_id)
        statement = statement.order_by(Taluka.name)
        return db.exec(statement).all()

    @staticmethod
    def get_villages(db: Session, taluka_id: UUID | None = None) -> list[Village]:
        statement = select(Village)
        if taluka_id:
            statement = statement.where(Village.taluka_id == taluka_id)
        statement = statement.order_by(Village.name)
        return db.exec(statement).all()

    # -----------------------------------------------------------------------
    # Matching — find existing records (LGD → exact → fuzzy)
    # -----------------------------------------------------------------------

    @staticmethod
    def find_district(
        db: Session,
        name: str,
        state: str | None = None,
        lgd_code: str | None = None,
        fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
    ) -> District | None:
        """Find a district by LGD code, exact normalized name, or fuzzy match.

        Priority:
        1. LGD code exact match (if provided)
        2. Normalized name exact match (same state if provided)
        3. Fuzzy match ≥ threshold (same state if provided)
        """
        norm = normalize_for_match(name)

        # 1. LGD code
        if lgd_code:
            stmt = select(District).where(District.lgd_code == lgd_code)
            result = db.exec(stmt).first()
            if result:
                return result

        # 2. Exact normalized name — narrow by state in SQL
        stmt = select(District)
        if state:
            stmt = stmt.where(District.state.ilike(state))
        candidates = db.exec(stmt).all()

        for d in candidates:
            if normalize_for_match(d.name) == norm:
                return d

        # 3. Fuzzy
        best_match: District | None = None
        best_ratio = 0.0
        for d in candidates:
            ratio = _fuzzy_ratio(norm, normalize_for_match(d.name))
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = d

        if best_ratio >= fuzzy_threshold:
            return best_match
        return None

    @staticmethod
    def find_taluka(
        db: Session,
        name: str,
        district_id: UUID,
        lgd_code: str | None = None,
        fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
    ) -> Taluka | None:
        """Find a taluka within a district by LGD code, exact, or fuzzy match."""
        norm = normalize_for_match(name)

        # 1. LGD code
        if lgd_code:
            stmt = select(Taluka).where(
                Taluka.lgd_code == lgd_code, Taluka.district_id == district_id
            )
            result = db.exec(stmt).first()
            if result:
                return result

        # 2. Exact normalized name
        stmt = select(Taluka).where(Taluka.district_id == district_id)
        talukas = db.exec(stmt).all()

        for t in talukas:
            if normalize_for_match(t.name) == norm:
                return t

        # 3. Fuzzy
        best_match: Taluka | None = None
        best_ratio = 0.0
        for t in talukas:
            ratio = _fuzzy_ratio(norm, normalize_for_match(t.name))
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = t

        if best_ratio >= fuzzy_threshold:
            return best_match
        return None

    @staticmethod
    def find_gram_panchayat(
        db: Session,
        name: str,
        taluka_id: UUID,
        district_id: UUID,
        lgd_code: str | None = None,
        fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
    ) -> GramPanchayat | None:
        """Find a gram panchayat within a taluka by LGD code, exact, or fuzzy match."""
        norm = normalize_for_match(name)

        # 1. LGD code
        if lgd_code:
            stmt = select(GramPanchayat).where(
                GramPanchayat.lgd_code == lgd_code,
                GramPanchayat.taluka_id == taluka_id,
            )
            result = db.exec(stmt).first()
            if result:
                return result

        # 2. Exact normalized name
        stmt = select(GramPanchayat).where(
            GramPanchayat.taluka_id == taluka_id,
            GramPanchayat.district_id == district_id,
        )
        gps = db.exec(stmt).all()

        for gp in gps:
            if normalize_for_match(gp.name) == norm:
                return gp

        # 3. Fuzzy
        best_match: GramPanchayat | None = None
        best_ratio = 0.0
        for gp in gps:
            ratio = _fuzzy_ratio(norm, normalize_for_match(gp.name))
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = gp

        if best_ratio >= fuzzy_threshold:
            return best_match
        return None

    @staticmethod
    def find_village(
        db: Session,
        name: str,
        taluka_id: UUID,
        lgd_code: str | None = None,
        fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
    ) -> Village | None:
        """Find a village within a taluka by LGD code, exact, or fuzzy match."""
        norm = normalize_for_match(name)

        # 1. LGD code
        if lgd_code:
            stmt = select(Village).where(
                Village.lgd_code == lgd_code, Village.taluka_id == taluka_id
            )
            result = db.exec(stmt).first()
            if result:
                return result

        # 2. Exact normalized name
        stmt = select(Village).where(Village.taluka_id == taluka_id)
        villages = db.exec(stmt).all()

        for v in villages:
            if normalize_for_match(v.name) == norm:
                return v

        # 3. Fuzzy
        best_match: Village | None = None
        best_ratio = 0.0
        for v in villages:
            ratio = _fuzzy_ratio(norm, normalize_for_match(v.name))
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = v

        if best_ratio >= fuzzy_threshold:
            return best_match
        return None

    # -----------------------------------------------------------------------
    # Resolution — normalize → match → create if not found
    # -----------------------------------------------------------------------

    @staticmethod
    def resolve_location(
        db: Session,
        name: str,
        level: str = "village",
        district_id: UUID | None = None,
        taluka_id: UUID | None = None,
        gram_panchayat_id: UUID | None = None,
        state: str | None = None,
        lgd_code: str | None = None,
        fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
    ) -> UUID:
        """Resolve a raw location name to a canonical UUID.

        If no match is found, creates a new record.  Returns the UUID of the
        canonical record at the requested *level*.

        Parameters
        ----------
        level : str
            One of ``"district"``, ``"taluka"``, ``"gram_panchayat"``, ``"village"``.
        district_id, taluka_id, gram_panchayat_id : UUID, optional
            Parent IDs — required when creating records at child levels.
        """
        if level == "district":
            match = LocationService.find_district(
                db,
                name,
                state=state,
                lgd_code=lgd_code,
                fuzzy_threshold=fuzzy_threshold,
            )
            if match:
                return match.id
            return _persist_new(
                db,
                District(name=name.strip(), state=state or "Maharashtra", lgd_code=lgd_code),
            )

        if level == "taluka":
            if not district_id:
                raise ValueError("district_id is required to resolve/create a taluka")
            match = LocationService.find_taluka(
                db,
                name,
                district_id=district_id,
                lgd_code=lgd_code,
                fuzzy_threshold=fuzzy_threshold,
            )
            if match:
                return match.id
            return _persist_new(
                db,
                Taluka(name=name.strip(), district_id=district_id, lgd_code=lgd_code),
            )

        if level == "gram_panchayat":
            if not taluka_id or not district_id:
                raise ValueError(
                    "taluka_id and district_id are required to resolve/create a gram panchayat"
                )
            match = LocationService.find_gram_panchayat(
                db,
                name,
                taluka_id=taluka_id,
                district_id=district_id,
                lgd_code=lgd_code,
                fuzzy_threshold=fuzzy_threshold,
            )
            if match:
                return match.id
            return _persist_new(
                db,
                GramPanchayat(
                    name=name.strip(),
                    taluka_id=taluka_id,
                    district_id=district_id,
                    lgd_code=lgd_code,
                ),
            )

        if level == "village":
            if not taluka_id:
                raise ValueError("taluka_id is required to resolve/create a village")
            match = LocationService.find_village(
                db,
                name,
                taluka_id=taluka_id,
                lgd_code=lgd_code,
                fuzzy_threshold=fuzzy_threshold,
            )
            if match:
                return match.id
            return _persist_new(
                db,
                Village(
                    name=name.strip(),
                    district_id=district_id,
                    taluka_id=taluka_id,
                    gram_panchayat_id=gram_panchayat_id,
                    lgd_code=lgd_code,
                ),
            )

        raise ValueError(
            f"Invalid level: {level!r}. Must be district|taluka|gram_panchayat|village"
        )

    # -----------------------------------------------------------------------
    # Deduplication — detect & merge
    # -----------------------------------------------------------------------

    @staticmethod
    def detect_duplicates(
        db: Session,
        level: str = "village",
        state: str | None = None,
        fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD,
    ) -> list[dict]:
        """Detect groups of duplicate locations at the given hierarchy level.

        Returns a list of groups, each group being a dict:
        ``{"name": "<normalized>", "records": [<serialized>, ...]}``
        """
        if level == "district":
            return LocationService._detect_duplicates_district(db, state, fuzzy_threshold)
        if level == "taluka":
            return LocationService._detect_duplicates_taluka(db, state, fuzzy_threshold)
        if level == "gram_panchayat":
            return LocationService._detect_duplicates_gp(db, state, fuzzy_threshold)
        if level == "village":
            return LocationService._detect_duplicates_village(db, state, fuzzy_threshold)
        raise ValueError(f"Invalid level: {level!r}")

    @staticmethod
    def _detect_duplicates_district(db: Session, state: str | None, threshold: float) -> list[dict]:
        stmt = select(District)
        if state:
            stmt = stmt.where(District.state.ilike(state))
        districts = db.exec(stmt).all()

        return LocationService._group_by_normalized(districts, threshold)

    @staticmethod
    def _detect_duplicates_taluka(db: Session, state: str | None, threshold: float) -> list[dict]:
        stmt = select(Taluka)
        talukas = db.exec(stmt).all()
        # Group by parent district first, then fuzzy match within group
        by_district: dict[UUID, list[Taluka]] = defaultdict(list)
        for t in talukas:
            by_district[t.district_id].append(t)

        groups: list[dict] = []
        for district_id, items in by_district.items():
            for g in LocationService._group_by_normalized(items, threshold):
                g["district_id"] = str(district_id)
                groups.append(g)
        return groups

    @staticmethod
    def _detect_duplicates_gp(db: Session, state: str | None, threshold: float) -> list[dict]:
        gps = db.exec(select(GramPanchayat)).all()
        by_taluka: dict[UUID, list[GramPanchayat]] = defaultdict(list)
        for gp in gps:
            by_taluka[gp.taluka_id].append(gp)

        groups: list[dict] = []
        for taluka_id, items in by_taluka.items():
            for g in LocationService._group_by_normalized(items, threshold):
                g["taluka_id"] = str(taluka_id)
                groups.append(g)
        return groups

    @staticmethod
    def _detect_duplicates_village(db: Session, state: str | None, threshold: float) -> list[dict]:
        villages = db.exec(select(Village)).all()
        by_taluka: dict[UUID, list[Village]] = defaultdict(list)
        for v in villages:
            by_taluka[v.taluka_id].append(v)

        groups: list[dict] = []
        for taluka_id, items in by_taluka.items():
            for g in LocationService._group_by_normalized(items, threshold):
                g["taluka_id"] = str(taluka_id)
                groups.append(g)
        return groups

    @staticmethod
    def _group_by_normalized(records: list, threshold: float) -> list[dict]:
        """Group records by normalized name using single-linkage clustering.

        Records are grouped together if any pair in the group has a fuzzy
        ratio ≥ *threshold*.
        """
        if not records:
            return []

        norm_map: list[tuple[str, object]] = [(normalize_for_match(r.name), r) for r in records]

        # Union-find for clustering
        parent = list(range(len(norm_map)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        # Compare every pair within the group
        for i in range(len(norm_map)):
            for j in range(i + 1, len(norm_map)):
                ratio = _fuzzy_ratio(norm_map[i][0], norm_map[j][0])
                if ratio >= threshold:
                    union(i, j)

        # Build groups
        clusters: dict[int, list] = defaultdict(list)
        for i, (_norm, rec) in enumerate(norm_map):
            clusters[find(i)].append(rec)

        # Build a lookup from record id → normalized key (reuse norm_map)
        norm_by_id = {id(rec): norm for norm, rec in norm_map}

        result: list[dict] = []
        for members in clusters.values():
            if len(members) < 2:
                continue  # no duplicate
            group_records = []
            for m in members:
                group_records.append(
                    {
                        "id": str(m.id),
                        "name": m.name,
                        "normalized": norm_by_id[id(m)],
                        "lgd_code": getattr(m, "lgd_code", None),
                    }
                )
            # Use the normalized key from the first member (deterministic)
            result.append(
                {
                    "normalized_name": norm_by_id[id(members[0])],
                    "count": len(members),
                    "records": group_records,
                }
            )
        return result

    # Whitelist of valid table names for raw-SQL operations
    _VALID_TABLE_NAMES: set[str] = {
        "districts",
        "talukas",
        "gram_panchayats",
        "villages",
        "agriculture",
        "analysis_runs",
        "businesses",
        "competitor_analyses",
        "economic_indicators",
        "infrastructure",
        "livestock",
        "market_analyses",
        "market_prices",
        "markets",
        "population",
        "profiles",
        "weather",
    }
    _VALID_FK_COLUMNS: set[str] = {
        "location_id",
        "taluka_id",
        "district_id",
        "gram_panchayat_id",
    }

    @staticmethod
    def _validate_sql_ident(name: str, allowed: set[str], label: str) -> None:
        """Raise if *name* is not in the allowed set (SQL safety guard)."""
        if name not in allowed:
            raise ValueError(f"Invalid {label}: {name!r}")

    @staticmethod
    def merge_duplicates(
        db: Session,
        keep_id: UUID,
        merge_ids: list[UUID],
        level: str = "village",
    ) -> dict:
        """Merge duplicate locations into *keep_id*.

        1. Re-parent all FK references from *merge_ids* → *keep_id*.
        2. Delete the merged records.

        Returns a summary dict with counts of updated rows per table.
        All DB changes run in a single transaction — commit on success,
        rollback on any error.
        """
        from sqlalchemy import text

        # --- Input validation ---
        if not merge_ids:
            raise ValueError("merge_ids must contain at least one id")
        if keep_id in merge_ids:
            raise ValueError("keep_id cannot be in merge_ids")

        _TABLE_MAP = {
            "district": "districts",
            "taluka": "talukas",
            "gram_panchayat": "gram_panchayats",
            "village": "villages",
        }
        if level not in _TABLE_MAP:
            raise ValueError(f"Invalid level: {level!r}")
        table = _TABLE_MAP[level]
        LocationService._validate_sql_ident(table, LocationService._VALID_TABLE_NAMES, "table")

        try:
            # Verify keep record exists (inside transaction)
            exists = db.execute(
                text(f"SELECT 1 FROM {table} WHERE id = :id LIMIT 1"),
                {"id": str(keep_id)},
            ).first()
            if not exists:
                raise ValueError(f"keep_id {keep_id} not found in {level}s")

            if level == "district":
                summary = LocationService._merge_districts(db, keep_id, merge_ids)
            elif level == "taluka":
                summary = LocationService._merge_talukas(db, keep_id, merge_ids)
            elif level == "gram_panchayat":
                summary = LocationService._merge_gps(db, keep_id, merge_ids)
            elif level == "village":
                summary = LocationService._merge_villages(db, keep_id, merge_ids)
            else:
                raise ValueError(f"Invalid level: {level!r}")

            db.commit()
        except Exception:
            db.rollback()
            raise

        return summary

    # --- Village merge (re-parents domain tables) ---

    @staticmethod
    def _merge_villages(db: Session, keep_id: UUID, merge_ids: list[UUID]) -> dict:
        from sqlalchemy import text

        summary: dict[str, int] = {}

        # Re-parent domain tables that reference villages.id
        for table_name, fk_col in _VILLAGE_FK_TABLES:
            LocationService._validate_sql_ident(
                table_name, LocationService._VALID_TABLE_NAMES, "table"
            )
            LocationService._validate_sql_ident(fk_col, LocationService._VALID_FK_COLUMNS, "column")
            for mid in merge_ids:
                result = db.execute(
                    text(f"UPDATE {table_name} SET {fk_col} = :keep WHERE {fk_col} = :merge"),
                    {"keep": str(keep_id), "merge": str(mid)},
                )
                summary[f"{table_name}.{fk_col}"] = (
                    summary.get(f"{table_name}.{fk_col}", 0) + result.rowcount
                )

        # Delete merged village records
        for mid in merge_ids:
            db.execute(text("DELETE FROM villages WHERE id = :id"), {"id": str(mid)})
        summary["villages_deleted"] = len(merge_ids)

        return summary

    # --- Taluka merge (re-parent GP + villages, then village FKs) ---

    @staticmethod
    def _merge_talukas(db: Session, keep_id: UUID, merge_ids: list[UUID]) -> dict:
        from sqlalchemy import text

        summary: dict[str, int] = {}

        for mid in merge_ids:
            # Re-parent gram_panchayats
            result = db.execute(
                text("UPDATE gram_panchayats SET taluka_id = :keep WHERE taluka_id = :merge"),
                {"keep": str(keep_id), "merge": str(mid)},
            )
            summary["gram_panchayats.taluka_id"] = (
                summary.get("gram_panchayats.taluka_id", 0) + result.rowcount
            )

            # Re-parent villages
            result = db.execute(
                text("UPDATE villages SET taluka_id = :keep WHERE taluka_id = :merge"),
                {"keep": str(keep_id), "merge": str(mid)},
            )
            summary["villages.taluka_id"] = summary.get("villages.taluka_id", 0) + result.rowcount

        # Delete merged taluka records
        for mid in merge_ids:
            db.execute(text("DELETE FROM talukas WHERE id = :id"), {"id": str(mid)})
        summary["talukas_deleted"] = len(merge_ids)

        return summary

    # --- District merge (re-parent talukas + GP + villages, then village FKs) ---

    @staticmethod
    def _merge_districts(db: Session, keep_id: UUID, merge_ids: list[UUID]) -> dict:
        from sqlalchemy import text

        summary: dict[str, int] = {}

        for mid in merge_ids:
            # Re-parent talukas
            result = db.execute(
                text("UPDATE talukas SET district_id = :keep WHERE district_id = :merge"),
                {"keep": str(keep_id), "merge": str(mid)},
            )
            summary["talukas.district_id"] = summary.get("talukas.district_id", 0) + result.rowcount

            # Re-parent gram_panchayats
            result = db.execute(
                text("UPDATE gram_panchayats SET district_id = :keep WHERE district_id = :merge"),
                {"keep": str(keep_id), "merge": str(mid)},
            )
            summary["gram_panchayats.district_id"] = (
                summary.get("gram_panchayats.district_id", 0) + result.rowcount
            )

            # Re-parent villages
            result = db.execute(
                text("UPDATE villages SET district_id = :keep WHERE district_id = :merge"),
                {"keep": str(keep_id), "merge": str(mid)},
            )
            summary["villages.district_id"] = (
                summary.get("villages.district_id", 0) + result.rowcount
            )

        # Delete merged district records
        for mid in merge_ids:
            db.execute(text("DELETE FROM districts WHERE id = :id"), {"id": str(mid)})
        summary["districts_deleted"] = len(merge_ids)

        return summary

    # --- Gram Panchayat merge (re-parent villages) ---

    @staticmethod
    def _merge_gps(db: Session, keep_id: UUID, merge_ids: list[UUID]) -> dict:
        from sqlalchemy import text

        summary: dict[str, int] = {}

        for mid in merge_ids:
            result = db.execute(
                text(
                    "UPDATE villages SET gram_panchayat_id = :keep WHERE gram_panchayat_id = :merge"
                ),
                {"keep": str(keep_id), "merge": str(mid)},
            )
            summary["villages.gram_panchayat_id"] = (
                summary.get("villages.gram_panchayat_id", 0) + result.rowcount
            )

        # Delete merged GP records
        for mid in merge_ids:
            db.execute(text("DELETE FROM gram_panchayats WHERE id = :id"), {"id": str(mid)})
        summary["gram_panchayats_deleted"] = len(merge_ids)

        return summary
