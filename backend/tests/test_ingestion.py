"""Unit tests for the data ingestion pipeline (validation, normalization, importer)."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

from app.ingestion import run_import
from app.ingestion.csv_reader import read_csv_rows
from app.ingestion.normalization import (
    clean_str,
    parse_date,
    resolve_village,
    to_bool,
    to_float,
    to_int,
)
from app.ingestion.validation import (
    AgricultureRow,
    MarketPriceRow,
    PopulationRow,
    WeatherRow,
)
from app.models.agriculture import Agriculture
from app.models.livestock import Livestock
from app.models.location import Population
from app.models.market import Market, MarketPrice
from app.models.provenance import DataSource

# Repo-root sample data — exercises the real CSVs end-to-end with a mocked DB.
# Walk up from the test file to find the data/raw directory, so this works
# both locally (backend/tests/ → project root) and inside Docker (/app/tests/ → /).
_HERE = Path(__file__).resolve().parent
SAMPLES: Path | None = None
for _ancestor in [_HERE, *_HERE.parents]:
    if (_ancestor / "data" / "raw").is_dir():
        SAMPLES = _ancestor / "data" / "raw"
        break
if SAMPLES is None:
    raise RuntimeError("Cannot locate data/raw sample directory")


def write_csv(content: str) -> Path:
    """Write CSV text to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".csv", delete=False)
    f.write(content)
    f.close()
    return Path(f.name)


class FakeDB:
    """Minimal stand-in for a SQLAlchemy Session, driven by ``found``.

    ``exec(...).first()`` returns ``found[0]`` when set; otherwise it (and
    ``all()``) fall back to whatever the test has ``add``-ed for the same
    model, so the dedup-key preload can see previously imported rows across
    runs that share this FakeDB.  ``get()`` reads that same store by ID.
    """

    def __init__(self, found=None):
        self.found = list(found or [])
        self.store: dict = {}
        self.added: list = []
        self.committed = False

    def exec(self, stmt):
        found = self.found
        store = self.store
        try:
            entity = stmt.column_descriptions[0]["entity"]
        except Exception:
            entity = None

        class _Result:
            def first(self):
                if found:
                    return found[0]
                if entity is not None:
                    return next((o for o in store.values() if isinstance(o, entity)), None)
                return None

            def all(self):
                if found:
                    return list(found)
                if entity is not None:
                    return [o for o in store.values() if isinstance(o, entity)]
                return []

        return _Result()

    def get(self, model, pk):
        return self.store.get(pk)

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()
        self.store[obj.id] = obj
        self.added.append(obj)

    def add_all(self, objs):
        for obj in objs:
            self.add(obj)

    def flush(self):
        pass

    def refresh(self, obj):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


# ------------------------------------------------------------------ #
# csv_reader
# ------------------------------------------------------------------ #


class TestCSVReader:
    def test_reads_rows_with_line_numbers(self):
        path = write_csv("a,b\n1,2\n3,4\n")
        rows = read_csv_rows(path)
        assert len(rows) == 2
        assert rows[0].line_number == 2
        assert rows[0].data == {"a": "1", "b": "2"}
        assert rows[1].line_number == 3

    def test_strips_bom_and_whitespace(self):
        path = write_csv("﻿ name ,  value \n  x , y \n")
        rows = read_csv_rows(path)
        assert rows[0].data == {"name": "x", "value": "y"}

    def test_skips_blank_lines(self):
        path = write_csv("a,b\n1,2\n,,\n3,4\n")
        rows = read_csv_rows(path)
        assert [r.data for r in rows] == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]

    def test_empty_file_returns_no_rows(self):
        path = write_csv("")
        assert read_csv_rows(path) == []


# ------------------------------------------------------------------ #
# Normalization helpers
# ------------------------------------------------------------------ #


class TestNormalizationHelpers:
    def test_clean_str_missing_markers(self):
        assert clean_str("  ") is None
        assert clean_str("NA") is None
        assert clean_str("N/A") is None
        assert clean_str("-") is None
        assert clean_str(" null ") is None

    def test_clean_str_keeps_values(self):
        assert clean_str("  Pune  ") == "Pune"

    def test_to_int_handles_commas_and_missing(self):
        assert to_int("1,234") == 1234
        assert to_int("") is None
        assert to_int(None) is None

    def test_to_int_rejects_garbage(self):
        with pytest.raises(ValueError):
            to_int("abc")

    def test_to_float(self):
        assert to_float(" 87.5 ") == 87.5
        assert to_float("1,234.5") == 1234.5
        assert to_float("") is None
        with pytest.raises(ValueError):
            to_float("not_a_number")

    def test_parse_date_formats(self):
        assert parse_date("2024-06-15").isoformat() == "2024-06-15"
        assert parse_date("15/06/2024").isoformat() == "2024-06-15"
        assert parse_date("15-06-2024").isoformat() == "2024-06-15"
        assert parse_date("") is None

    def test_parse_date_rejects_garbage(self):
        with pytest.raises(ValueError):
            parse_date("not-a-date")

    def test_to_bool(self):
        assert to_bool("yes") is True
        assert to_bool("0") is False
        assert to_bool("") is None
        with pytest.raises(ValueError):
            to_bool("maybe")


# ------------------------------------------------------------------ #
# Row validation
# ------------------------------------------------------------------ #


class TestRowValidation:
    def test_population_row_parses_and_ignores_extras(self):
        row = PopulationRow.model_validate(
            {
                "village_name": "Wadgaon",
                "district_name": "Pune",
                "taluka_name": "Haveli",
                "year": "2021",
                "population_total": "1,234",
                "junk_column": "ignored",
            }
        )
        assert row.year == 2021
        assert row.population_total == 1234
        assert row.literacy_rate is None

    def test_population_row_missing_year_rejected(self):
        with pytest.raises(ValidationError):
            PopulationRow.model_validate({"village_name": "x", "year": ""})

    def test_population_row_bad_year_rejected(self):
        with pytest.raises(ValidationError):
            PopulationRow.model_validate({"village_name": "x", "year": "not_a_number"})

    def test_agriculture_row_requires_crop(self):
        with pytest.raises(ValidationError):
            AgricultureRow.model_validate({"crop_name": "", "year": "2023"})

    def test_weather_row_parses_indian_date(self):
        row = WeatherRow.model_validate({"date": "15/06/2024", "drought_indicator": "yes"})
        assert row.date.isoformat() == "2024-06-15"
        assert row.drought_indicator is True

    def test_market_price_row_needs_market_or_village(self):
        with pytest.raises(ValidationError):
            MarketPriceRow.model_validate({"commodity": "Onion", "recorded_date": "2024-06-01"})

    def test_market_price_row_with_village_only_ok(self):
        row = MarketPriceRow.model_validate(
            {"commodity": "Onion", "recorded_date": "2024-06-01", "village_name": "Ozar"}
        )
        assert row.village_name == "Ozar"


# ------------------------------------------------------------------ #
# resolve_village
# ------------------------------------------------------------------ #


class TestResolveVillage:
    def _row(self, **overrides):
        data = {
            "village_name": "Wadgaon",
            "district_name": "Pune",
            "taluka_name": "Haveli",
            "year": "2021",
        }
        data.update(overrides)
        return PopulationRow.model_validate(data)

    def test_no_village_name_returns_none(self):
        report = MagicMock()
        row = self._row(village_name="")
        assert resolve_village(MagicMock(), row, report) is None

    def test_existing_hierarchy_resolved_without_creation(self):
        mock_db = MagicMock()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            mock_ls.find_district.return_value = MagicMock(id=uuid4())
            mock_ls.find_taluka.return_value = MagicMock(id=uuid4())
            mock_ls.find_village.return_value = MagicMock(id=uuid4())
            report = MagicMock()
            report.created_locations = []
            village_id = resolve_village(mock_db, self._row(), report)
        assert village_id is not None
        mock_ls.resolve_location.assert_not_called()  # nothing was created
        assert report.created_locations == []

    def test_missing_hierarchy_creates_and_records(self):
        mock_db = MagicMock()
        report = MagicMock()
        report.created_locations = []
        ids = [uuid4(), uuid4(), uuid4()]
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            mock_ls.find_district.return_value = None
            mock_ls.find_taluka.return_value = None
            mock_ls.find_village.return_value = None
            mock_ls.resolve_location.side_effect = ids
            result = resolve_village(mock_db, self._row(), report)
        assert result == ids[2]
        assert mock_ls.resolve_location.call_count == 3

    def test_dry_run_refuses_creation(self):
        mock_db = MagicMock()
        report = MagicMock()
        report.created_locations = []
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            mock_ls.find_district.return_value = None
            with pytest.raises(ValueError, match="dry-run"):
                resolve_village(mock_db, self._row(), report, allow_create=False)

    def test_taluka_without_district_rejected(self):
        mock_db = MagicMock()
        row = self._row(district_name="")
        with pytest.raises(ValueError, match="district_name"):
            resolve_village(mock_db, row, MagicMock())

    def test_village_without_parents_rejected(self):
        mock_db = MagicMock()
        row = PopulationRow.model_validate(
            {"village_name": "X", "year": "2021", "district_name": "", "taluka_name": ""}
        )
        with pytest.raises(ValueError, match="without district_name"):
            resolve_village(mock_db, row, MagicMock())


# ------------------------------------------------------------------ #
# run_import
# ------------------------------------------------------------------ #


class TestRunImport:
    def test_unknown_domain_raises(self):
        with pytest.raises(ValueError, match="unknown domain"):
            run_import(MagicMock(), "nope", "x.csv")

    def test_population_sample_imports_with_one_rejection(self):
        mock_db = MagicMock()
        report = run_import(mock_db, "population", SAMPLES / "population" / "sample.csv")
        assert report.total_rows == 6
        assert report.imported == 5
        assert report.rejected == 1
        assert "not_a_number" in report.errors[0].message or report.errors[0].field == "year"
        assert mock_db.add_all.call_count == 1
        assert len(mock_db.add_all.call_args[0][0]) == 5
        assert mock_db.commit.call_count >= 1

    def test_provenance_stamped_on_rows(self):
        mock_db = MagicMock()
        report = run_import(
            mock_db,
            "population",
            SAMPLES / "population" / "sample.csv",
            source="Census 2021",
            source_url="https://censusindia.gov.in",
            data_year=2021,
        )
        rows = mock_db.add_all.call_args[0][0]
        for row in rows:
            assert row.source == "Census 2021"
            assert row.source_url == "https://censusindia.gov.in"
            assert row.data_year == 2021
        assert report.imported == 5

    def test_agriculture_sample(self):
        mock_db = MagicMock()
        report = run_import(mock_db, "agriculture", SAMPLES / "agriculture" / "sample.csv")
        assert report.imported == 5
        assert report.rejected == 1  # missing crop_name
        rows = mock_db.add_all.call_args[0][0]
        assert rows[0].crop_name == "Onion"
        assert rows[3].crop_name == "Bajra"  # messy whitespace stripped by pydantic? (kept)
        assert rows[0].location_id is not None

    def test_weather_sample(self):
        mock_db = MagicMock()
        report = run_import(mock_db, "weather", SAMPLES / "weather" / "sample.csv")
        assert report.imported == 5
        assert report.rejected == 1  # bad date
        rows = mock_db.add_all.call_args[0][0]
        assert rows[1].rainfall_mm is None  # missing value → NULL, not 0

    def test_market_prices_sample(self):
        mock_db = MagicMock()
        report = run_import(mock_db, "market_prices", SAMPLES / "market_prices" / "sample.csv")
        assert report.imported == 5
        assert report.rejected == 1  # no market_name or village_name
        rows = mock_db.add_all.call_args[0][0]
        assert rows[0].commodity == "Onion"

    def test_dry_run_writes_nothing(self):
        mock_db = MagicMock()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            # existing hierarchy — resolution succeeds read-only in dry-run;
            # each village resolves to its own ID so rows don't merge
            mock_ls.find_district.return_value = MagicMock(id=uuid4())
            mock_ls.find_taluka.return_value = MagicMock(id=uuid4())
            mock_ls.find_village.side_effect = lambda *a, **k: MagicMock(id=uuid4())
            report = run_import(
                mock_db, "population", SAMPLES / "population" / "sample.csv", dry_run=True
            )
        assert report.imported == 5
        assert report.dry_run is True
        mock_db.add_all.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_bad_row_does_not_stop_good_rows(self):
        path = write_csv(
            "district_name,taluka_name,village_name,year,population_total\n"
            "Pune,Haveli,A,2021,100\n"
            "Pune,Haveli,B,xx,100\n"
            "Pune,Haveli,C,2021,300\n"
        )
        mock_db = MagicMock()
        report = run_import(mock_db, "population", path)
        assert report.imported == 2
        assert report.rejected == 1
        assert report.errors[0].line_number == 3

    def test_data_source_provenance_recorded(self):
        mock_db = MagicMock()
        run_import(mock_db, "population", SAMPLES / "population" / "sample.csv")
        # existing DataSource mock is returned by db.exec().first()
        added = mock_db.add.call_args_list
        assert len(added) >= 1  # updated existing or added new DataSource row

    def test_locations_sample_writes_hierarchy_directly(self):
        mock_db = MagicMock()
        report = run_import(mock_db, "locations", SAMPLES / "locations" / "sample.csv")
        assert report.imported == 5
        assert report.rejected == 1  # district_name missing
        # hierarchy writes happen via resolve_location, nothing bulk-inserted
        mock_db.add_all.assert_not_called()


# ------------------------------------------------------------------ #
# Merge-on-reimport + shared cache
# ------------------------------------------------------------------ #


class TestMergeAndCache:
    def test_market_second_row_merges_into_first(self):
        path = write_csv("market_name,market_type\nPune Mandi,APMC\nPune Mandi,APMC\n")
        db = FakeDB()  # no existing markets
        report = run_import(db, "markets", path)
        assert report.imported == 1
        assert report.updated == 1
        assert report.rejected == 0

    def test_market_cache_stores_ids_not_instances(self):
        # Regression: the cache used to hold ORM instances, which go stale
        # (expired + detached) once the creating session commits and closes.
        path = write_csv("market_name,market_type\nPune Mandi,APMC\n")
        db = FakeDB()
        report = run_import(db, "markets", path)
        market_entries = [v for k, v in report.location_cache.items() if k[0] == "market"]
        assert market_entries, "market lookup should be cached"
        assert all(isinstance(v, UUID) for v in market_entries)

    def test_reimport_merges_corrected_values(self):
        # Re-importing a corrected CSV must update the existing row (incoming
        # non-None values win) instead of stacking a duplicate.
        db = FakeDB()
        village_id = uuid4()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            mock_ls.find_district.return_value = MagicMock(id=uuid4())
            mock_ls.find_taluka.return_value = MagicMock(id=uuid4())
            mock_ls.find_village.return_value = MagicMock(id=village_id)
            first = write_csv(
                "district_name,taluka_name,village_name,year,population_total\n"
                "Pune,Haveli,Wadgaon,2021,1000\n"
            )
            report1 = run_import(db, "population", first)
            corrected = write_csv(
                "district_name,taluka_name,village_name,year,population_total\n"
                "Pune,Haveli,Wadgaon,2021,1500\n"
            )
            report2 = run_import(db, "population", corrected)
        assert report1.imported == 1
        assert report1.updated == 0
        assert report2.imported == 0
        assert report2.updated == 1
        merged = next(o for o in db.store.values() if type(o).__name__ == "Population")
        assert merged.population_total == 1500

    def test_dry_run_rejects_every_missing_market(self):
        # Regression: a failed "not found" lookup used to poison the cache, so
        # only the first row was rejected and the rest were silently accepted
        # with market_id=None.
        path = write_csv(
            "market_name,commodity,recorded_date\n"
            "Pune Mandi,Onion,2024-06-01\n"
            "Pune Mandi,Potato,2024-06-01\n"
            "Pune Mandi,Tomato,2024-06-01\n"
        )
        db = FakeDB()
        report = run_import(db, "market_prices", path, dry_run=True)
        assert report.rejected == 3
        assert report.imported == 0

    def test_shared_cache_merges_across_files(self):
        # --all mode: file 2 shares the cache AND the database, so a market
        # created by file 1 is merged into rather than re-inserted.
        cache: dict = {}
        db = FakeDB()
        report1 = run_import(
            db, "markets", write_csv("market_name\nPune Mandi\n"), location_cache=cache
        )
        report2 = run_import(
            db, "markets", write_csv("market_name\nPune Mandi\n"), location_cache=cache
        )
        assert report1.imported == 1
        assert report2.imported == 0
        assert report2.updated == 1

    def test_shared_existing_keys_merges_across_files(self):
        # --all mode shares the dedup key map too: file 2 must merge into
        # file 1's committed row (via the written-back ID) instead of either
        # duplicating it or crashing on a stale in-memory instance.
        db = FakeDB()
        cache: dict = {}
        keys: dict = {}
        village_id = uuid4()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            mock_ls.find_district.return_value = MagicMock(id=uuid4())
            mock_ls.find_taluka.return_value = MagicMock(id=uuid4())
            mock_ls.find_village.return_value = MagicMock(id=village_id)
            first = write_csv(
                "district_name,taluka_name,village_name,year,population_total\n"
                "Pune,Haveli,Wadgaon,2021,1000\n"
            )
            report1 = run_import(db, "population", first, location_cache=cache, existing_keys=keys)
            corrected = write_csv(
                "district_name,taluka_name,village_name,year,population_total\n"
                "Pune,Haveli,Wadgaon,2021,1500\n"
            )
            report2 = run_import(
                db, "population", corrected, location_cache=cache, existing_keys=keys
            )
        assert report1.imported == 1
        assert report2.imported == 0
        assert report2.updated == 1

    def test_businesses_same_name_different_village_do_not_merge(self):
        # Dedup key includes district/taluka/village, so same-named
        # businesses in different villages are distinct records.
        db = FakeDB()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            mock_ls.find_district.return_value = MagicMock(id=uuid4())
            mock_ls.find_taluka.return_value = MagicMock(id=uuid4())
            mock_ls.find_village.side_effect = lambda *a, **k: MagicMock(id=uuid4())
            path = write_csv(
                "business_name,category_name,district_name,taluka_name,village_name\n"
                "Shree Traders,Dairy,Pune,Haveli,Wadgaon\n"
                "Shree Traders,Dairy,Pune,Haveli,Uruli\n"
            )
            report = run_import(db, "businesses", path)
        assert report.imported == 2
        assert report.updated == 0

    def test_shared_cache_re_resolves_market_in_fresh_db(self):
        # A market created in file 1 is cached by ID; file 2 has a fresh DB
        # where that ID no longer exists, so it must re-resolve instead of
        # crashing on a stale cached instance.
        cache: dict = {}
        db1 = FakeDB()
        run_import(
            db1,
            "market_prices",
            write_csv("market_name,commodity,recorded_date\nPune Mandi,Onion,2024-06-01\n"),
            location_cache=cache,
        )
        db2 = FakeDB()
        report2 = run_import(
            db2,
            "market_prices",
            write_csv("market_name,commodity,recorded_date\nPune Mandi,Onion,2024-06-01\n"),
            location_cache=cache,
        )
        assert report2.imported == 1  # re-created in the fresh DB, no crash

    def test_dry_run_rejects_every_missing_category(self):
        path = write_csv("business_name,category_name\nShree Traders,Dairy\nShree Traders,Dairy\n")
        db = FakeDB()
        report = run_import(db, "businesses", path, dry_run=True)
        assert report.rejected == 2
        assert report.imported == 0


# ------------------------------------------------------------------ #
# Real-session row isolation (regression)
# ------------------------------------------------------------------ #


class TestRealSessionRowIsolation:
    """A failing row must not roll back merges applied to earlier rows.

    Regression for the bug where a row-level ``db.rollback()`` silently
    discarded every pending merge/creation from earlier rows of the same
    file (while the report still counted them as updated).  Runs against a
    real SQLite session so savepoint semantics actually apply.
    """

    @staticmethod
    def _engine():
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Population.__table__.create(engine)
        DataSource.__table__.create(engine)
        return engine

    def test_failing_row_does_not_discard_earlier_merge(self):
        engine = self._engine()
        village_id = uuid4()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            mock_ls.find_district.return_value = MagicMock(id=uuid4())
            mock_ls.find_taluka.return_value = MagicMock(id=uuid4())
            mock_ls.find_village.return_value = MagicMock(id=village_id)
            first = write_csv(
                "district_name,taluka_name,village_name,year,population_total\n"
                "Pune,Haveli,Wagholi,2021,1000\n"
            )
            with Session(engine, expire_on_commit=False) as db:
                report1 = run_import(db, "population", first)
            # Re-import: row 1 corrects the figure (merge into the 2021 row),
            # row 2 is unplaceable and fails.  Row 2's failure must not undo
            # row 1's correction.
            corrected = write_csv(
                "district_name,taluka_name,village_name,year,population_total\n"
                "Pune,Haveli,Wagholi,2021,1500\n"
                "X,,Y,2021,10\n"
            )
            with Session(engine, expire_on_commit=False) as db:
                report2 = run_import(db, "population", corrected)
        assert report1.imported == 1
        assert report1.rejected == 0
        assert report2.updated == 1  # row 1 merged into the existing record
        assert report2.rejected == 1  # row 2 rejected, isolated
        with Session(engine) as check:
            row = check.exec(select(Population)).one()
            assert row.population_total == 1500  # merge survived the bad row


# ------------------------------------------------------------------ #
# Location-scoped market dedup (regression)
# ------------------------------------------------------------------ #


def _market_tables(engine) -> None:
    """Create markets / market_prices with plain SQL (SQLite can't parse the
    PostGIS ``geography(POINT)`` column type the models declare)."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE markets ("
                "id VARCHAR(32) PRIMARY KEY, name VARCHAR, market_type VARCHAR, "
                "location_id VARCHAR(32), latitude FLOAT, longitude FLOAT, "
                "geog VARCHAR, source VARCHAR, source_url VARCHAR, "
                "created_at DATETIME)"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE market_prices ("
                "id VARCHAR(32) PRIMARY KEY, market_id VARCHAR(32), location_id VARCHAR(32), "
                "market_name VARCHAR, commodity VARCHAR, commodity_variety VARCHAR, "
                "unit VARCHAR, min_price FLOAT, max_price FLOAT, modal_price FLOAT, "
                "arrival_quantity FLOAT, arrival_unit VARCHAR, recorded_date DATE, "
                "source VARCHAR, source_url VARCHAR, created_at DATETIME)"
            )
        )
    DataSource.__table__.create(engine)


def _patch_location_service(mock_ls, village_ids: dict[str, UUID]) -> None:
    """Point the mock location service at fixed per-village UUIDs."""
    mock_ls.find_district.return_value = MagicMock(id=uuid4())
    mock_ls.find_taluka.return_value = MagicMock(id=uuid4())
    mock_ls.find_village.side_effect = lambda db, name, **kw: MagicMock(  # noqa: ARG005
        id=village_ids.get(name, uuid4())
    )


class TestLocationScopedMarketDedup:
    """Same-named mandis in different villages are distinct markets.

    Regression for the bug where markets were deduplicated by name alone, so
    two same-named mandis in different villages silently collapsed into one
    row (each re-import overwriting location_id/coords with the latest row's).
    Runs against a real SQLite session so the scoped SELECTs actually filter.
    """

    def test_same_name_different_villages_stay_distinct(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        _market_tables(engine)
        wagholi, uruli = uuid4(), uuid4()
        path = write_csv(
            "district_name,taluka_name,village_name,market_name,market_type\n"
            "Pune,Haveli,Wagholi,Main Market,APMC\n"
            "Pune,Haveli,Uruli,Main Market,APMC\n"
        )
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            _patch_location_service(mock_ls, {"Wagholi": wagholi, "Uruli": uruli})
            with Session(engine, expire_on_commit=False) as db:
                report = run_import(db, "markets", path)
        assert report.imported == 2
        assert report.updated == 0
        with Session(engine) as check:
            markets = check.exec(select(Market).order_by(Market.name)).all()
        assert len(markets) == 2
        assert {m.location_id for m in markets} == {wagholi, uruli}

    def test_same_name_same_village_merges_on_reimport(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        _market_tables(engine)
        wagholi = uuid4()
        first = write_csv(
            "district_name,taluka_name,village_name,market_name,market_type\n"
            "Pune,Haveli,Wagholi,Pune Mandi,APMC\n"
        )
        corrected = write_csv(
            "district_name,taluka_name,village_name,market_name,market_type\n"
            "Pune,Haveli,Wagholi,Pune Mandi,Regulated Market\n"
        )
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            _patch_location_service(mock_ls, {"Wagholi": wagholi})
            with Session(engine, expire_on_commit=False) as db:
                report1 = run_import(db, "markets", first)
            with Session(engine, expire_on_commit=False) as db:
                report2 = run_import(db, "markets", corrected)
        assert report1.imported == 1
        assert report2.updated == 1  # merged into the existing row, not a copy
        with Session(engine) as check:
            markets = check.exec(select(Market)).all()
        assert len(markets) == 1
        assert markets[0].market_type == "Regulated Market"
        assert markets[0].location_id == wagholi

    def test_price_rows_attach_to_the_right_village_market(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        _market_tables(engine)
        wagholi, uruli = uuid4(), uuid4()
        path = write_csv(
            "market_name,district_name,taluka_name,village_name,commodity,recorded_date\n"
            "Main Market,Pune,Haveli,Wagholi,Onion,2024-01-01\n"
            "Main Market,Pune,Haveli,Uruli,Potato,2024-01-01\n"
        )
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            _patch_location_service(mock_ls, {"Wagholi": wagholi, "Uruli": uruli})
            with Session(engine, expire_on_commit=False) as db:
                report = run_import(db, "market_prices", path)
        assert report.imported == 2
        with Session(engine) as check:
            markets = check.exec(select(Market)).all()
            prices = check.exec(select(MarketPrice)).all()
        by_id = {m.id: m for m in markets}
        assert {m.location_id for m in markets} == {wagholi, uruli}
        by_commodity = {p.commodity: p for p in prices}
        assert by_id[by_commodity["Onion"].market_id].location_id == wagholi
        assert by_id[by_commodity["Potato"].market_id].location_id == uruli

    def test_village_less_row_merges_single_same_name_market(self):
        # Legacy flow: a row without location columns still merges into the
        # one market that shares its name — but must reject when the name is
        # ambiguous (two same-named markets exist elsewhere).
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        _market_tables(engine)
        wagholi, uruli = uuid4(), uuid4()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            _patch_location_service(mock_ls, {"Wagholi": wagholi, "Uruli": uruli})
            with Session(engine, expire_on_commit=False) as db:
                run_import(db, "markets", write_csv("market_name\nPune Mandi\n"))
            with Session(engine, expire_on_commit=False) as db:
                report2 = run_import(db, "markets", write_csv("market_name\nPune Mandi\n"))
        assert report2.updated == 1
        with Session(engine) as check:
            assert len(check.exec(select(Market)).all()) == 1

        # Two markets now share the name (in different villages)…
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            _patch_location_service(mock_ls, {"Wagholi": wagholi, "Uruli": uruli})
            with Session(engine, expire_on_commit=False) as db:
                run_import(
                    db,
                    "markets",
                    write_csv(
                        "district_name,taluka_name,village_name,market_name\n"
                        "Pune,Haveli,Wagholi,Pune Mandi\n"
                        "Pune,Haveli,Uruli,Pune Mandi\n"
                    ),
                )
            # …so a village-less row can no longer pick one: it is rejected.
            with Session(engine, expire_on_commit=False) as db:
                report3 = run_import(db, "markets", write_csv("market_name\nPune Mandi\n"))
        assert report3.rejected == 1
        assert "ambiguous" in report3.errors[0].message


# ------------------------------------------------------------------ #
# Normalized dedup keys (regression)
# ------------------------------------------------------------------ #


class TestNormalizedDedupKeys:
    """Free-text dedup-key columns are compared in canonical form.

    Regression for the bug where a re-import that only changed the case of a
    key column (e.g. ``Wheat`` → ``wheat``) produced a new row instead of
    merging into the existing record — both sides of the key must be
    normalized identically.
    """

    def test_agriculture_case_only_correction_merges(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Agriculture.__table__.create(engine)
        DataSource.__table__.create(engine)
        village_id = uuid4()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            _patch_location_service(mock_ls, {"Wagholi": village_id})
            first = write_csv(
                "district_name,taluka_name,village_name,crop_name,cultivated_area,production,year,season\n"
                "Pune,Haveli,Wagholi,Wheat,100,50,2021,Kharif\n"
            )
            with Session(engine, expire_on_commit=False) as db:
                report1 = run_import(db, "agriculture", first)
            corrected = write_csv(
                "district_name,taluka_name,village_name,crop_name,cultivated_area,production,year,season\n"
                "Pune,Haveli,Wagholi,wheat,150,60,2021,Kharif\n"
            )
            with Session(engine, expire_on_commit=False) as db:
                report2 = run_import(db, "agriculture", corrected)
        assert report1.imported == 1
        assert report2.updated == 1  # case-only change merged, not duplicated
        assert report2.imported == 0
        with Session(engine) as check:
            rows = check.exec(select(Agriculture)).all()
        assert len(rows) == 1
        assert rows[0].cultivated_area == 150
        assert rows[0].crop_name == "Wheat"  # stored value untouched by merge

    def test_livestock_case_only_correction_merges(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Livestock.__table__.create(engine)
        DataSource.__table__.create(engine)
        village_id = uuid4()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            _patch_location_service(mock_ls, {"Wagholi": village_id})
            first = write_csv(
                "district_name,taluka_name,village_name,animal_type,animal_count,year\n"
                "Pune,Haveli,Wagholi,Cow,100,2021\n"
            )
            with Session(engine, expire_on_commit=False) as db:
                report1 = run_import(db, "livestock", first)
            corrected = write_csv(
                "district_name,taluka_name,village_name,animal_type,animal_count,year\n"
                "Pune,Haveli,Wagholi,cow,120,2021\n"
            )
            with Session(engine, expire_on_commit=False) as db:
                report2 = run_import(db, "livestock", corrected)
        assert report1.imported == 1
        assert report2.updated == 1
        with Session(engine) as check:
            rows = check.exec(select(Livestock)).all()
        assert len(rows) == 1
        assert rows[0].animal_count == 120

    def test_market_price_commodity_case_only_correction_merges(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        _market_tables(engine)
        village_id = uuid4()
        with patch("app.ingestion.normalization.LocationService") as mock_ls:
            _patch_location_service(mock_ls, {"Wagholi": village_id})
            first = write_csv(
                "market_name,district_name,taluka_name,village_name,commodity,commodity_variety,min_price,recorded_date\n"
                "Pune Mandi,Pune,Haveli,Wagholi,Onion,Red,1500,2024-01-01\n"
            )
            with Session(engine, expire_on_commit=False) as db:
                report1 = run_import(db, "market_prices", first)
            corrected = write_csv(
                "market_name,district_name,taluka_name,village_name,commodity,commodity_variety,min_price,recorded_date\n"
                "Pune Mandi,Pune,Haveli,Wagholi,onion,red,1600,2024-01-01\n"
            )
            with Session(engine, expire_on_commit=False) as db:
                report2 = run_import(db, "market_prices", corrected)
        assert report1.imported == 1
        assert report2.updated == 1
        with Session(engine) as check:
            rows = check.exec(select(MarketPrice)).all()
        assert len(rows) == 1
        assert rows[0].min_price == 1600
