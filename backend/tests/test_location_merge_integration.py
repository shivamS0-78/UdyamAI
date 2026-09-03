"""Integration tests for location merge and deduplication operations.

Uses an in-memory SQLite database to exercise real DB behavior: FK updates,
deletes, transaction rollback, and input validation — things MagicMock tests
cannot catch.
"""

from uuid import UUID, uuid4

import pytest
import sqlalchemy.exc
from sqlalchemy import Column, Float, ForeignKey, Integer, MetaData, Table, Text, create_engine
from sqlmodel import Session

from app.services.location_service import LocationService

# ---------------------------------------------------------------------------
# SQLite test schema — mirrors the location tables with all columns the
# SQLModel ORM models expect, but without geoalchemy2 dependencies.
# ---------------------------------------------------------------------------

metadata = MetaData()

_districts = Table(
    "districts",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("state", Text, nullable=False, server_default="Maharashtra"),
    Column("lgd_code", Text, nullable=True),
    Column("created_at", Text, nullable=True),
)

_talukas = Table(
    "talukas",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("district_id", Text, ForeignKey("districts.id"), nullable=False),
    Column("lgd_code", Text, nullable=True),
    Column("created_at", Text, nullable=True),
)

_gram_panchayats = Table(
    "gram_panchayats",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("taluka_id", Text, ForeignKey("talukas.id"), nullable=False),
    Column("district_id", Text, ForeignKey("districts.id"), nullable=False),
    Column("lgd_code", Text, nullable=True),
    Column("created_at", Text, nullable=True),
)

_villages = Table(
    "villages",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("district_id", Text, ForeignKey("districts.id"), nullable=False),
    Column("taluka_id", Text, ForeignKey("talukas.id"), nullable=False),
    Column("gram_panchayat_id", Text, ForeignKey("gram_panchayats.id"), nullable=False),
    Column("lgd_code", Text, nullable=True),
    Column("pin_code", Text, nullable=True),
    Column("latitude", Float, nullable=True),
    Column("longitude", Float, nullable=True),
    Column("geom", Text, nullable=True),
    Column("created_at", Text, nullable=True),
)

# Domain tables that reference villages via location_id (subset for testing)
_businesses = Table(
    "businesses",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text),
    Column("location_id", Text, ForeignKey("villages.id"), nullable=False),
)

_population = Table(
    "population",
    metadata,
    Column("id", Text, primary_key=True),
    Column("location_id", Text, ForeignKey("villages.id"), nullable=False),
    Column("year", Integer),
    Column("population_total", Integer, nullable=True),
    Column("male_population", Integer, nullable=True),
    Column("female_population", Integer, nullable=True),
    Column("households", Integer, nullable=True),
    Column("working_population", Integer, nullable=True),
    Column("literacy_rate", Float, nullable=True),
    Column("source", Text, nullable=True),
    Column("source_url", Text, nullable=True),
    Column("data_year", Integer, nullable=True),
    Column("created_at", Text, nullable=True),
)


@pytest.fixture()
def db():
    """Create an in-memory SQLite DB with the location schema, yield a session,
    and dispose of the engine afterward."""
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _id() -> str:
    return str(uuid4())


def _insert_district(
    session: Session, name: str, state: str = "Maharashtra", lgd_code: str | None = None
) -> str:
    did = _id()
    session.execute(_districts.insert().values(id=did, name=name, state=state, lgd_code=lgd_code))
    session.commit()
    return did


def _insert_taluka(session: Session, name: str, district_id: str) -> str:
    tid = _id()
    session.execute(_talukas.insert().values(id=tid, name=name, district_id=district_id))
    session.commit()
    return tid


def _insert_gp(session: Session, name: str, taluka_id: str, district_id: str) -> str:
    gid = _id()
    session.execute(
        _gram_panchayats.insert().values(
            id=gid, name=name, taluka_id=taluka_id, district_id=district_id
        )
    )
    session.commit()
    return gid


def _insert_village(
    session: Session, name: str, district_id: str, taluka_id: str, gp_id: str
) -> str:
    vid = _id()
    session.execute(
        _villages.insert().values(
            id=vid,
            name=name,
            district_id=district_id,
            taluka_id=taluka_id,
            gram_panchayat_id=gp_id,
        )
    )
    session.commit()
    return vid


def _insert_business(session: Session, name: str, location_id: str) -> str:
    bid = _id()
    session.execute(_businesses.insert().values(id=bid, name=name, location_id=location_id))
    session.commit()
    return bid


def _insert_population(session: Session, location_id: str, year: int = 2021) -> str:
    pid = _id()
    session.execute(_population.insert().values(id=pid, location_id=location_id, year=year))
    session.commit()
    return pid


def _count_where(session: Session, table: Table, col_name: str, value: str) -> int:
    return len(session.execute(table.select().where(table.c[col_name] == value)).fetchall())


# ---------------------------------------------------------------------------
# Village merge integration tests
# ---------------------------------------------------------------------------

# Only the domain tables that exist in our test schema
_TEST_VILLAGE_FK_TABLES = [
    ("businesses", "location_id"),
    ("population", "location_id"),
]


class TestMergeVillagesIntegration:
    def test_merge_reparents_domain_tables(self, db: Session):
        """Merging villages moves all FK references to the keep record."""
        import app.services.location_service as svc

        original = svc._VILLAGE_FK_TABLES
        svc._VILLAGE_FK_TABLES = _TEST_VILLAGE_FK_TABLES
        try:
            dist = _insert_district(db, "Pune")
            tal = _insert_taluka(db, "Haveli", dist)
            gp = _insert_gp(db, "Wadgaon", tal, dist)

            keep_vid = _insert_village(db, "Aundh", dist, tal, gp)
            merge_vid = _insert_village(db, "Aundh B", dist, tal, gp)

            # Attach domain records to the merge village
            bid = _insert_business(db, "Shop 1", merge_vid)
            pid = _insert_population(db, merge_vid)

            summary = LocationService.merge_duplicates(
                db, UUID(keep_vid), [UUID(merge_vid)], level="village"
            )

            # Business should now point to keep
            biz_row = db.execute(_businesses.select().where(_businesses.c.id == bid)).fetchone()
            assert biz_row.location_id == keep_vid

            # Population should now point to keep
            pop_row = db.execute(_population.select().where(_population.c.id == pid)).fetchone()
            assert pop_row.location_id == keep_vid

            # Merge village should be deleted
            assert _count_where(db, _villages, "id", merge_vid) == 0

            # Keep village should still exist
            assert _count_where(db, _villages, "id", keep_vid) == 1

            assert summary["villages_deleted"] == 1
            assert summary.get("businesses.location_id", 0) >= 1
            assert summary.get("population.location_id", 0) >= 1
        finally:
            svc._VILLAGE_FK_TABLES = original

    def test_merge_keeps_domain_records_intact(self, db: Session):
        """Records already pointing to keep_id are not affected."""
        import app.services.location_service as svc

        original = svc._VILLAGE_FK_TABLES
        svc._VILLAGE_FK_TABLES = _TEST_VILLAGE_FK_TABLES
        try:
            dist = _insert_district(db, "Pune")
            tal = _insert_taluka(db, "Haveli", dist)
            gp = _insert_gp(db, "Wadgaon", tal, dist)

            keep_vid = _insert_village(db, "Aundh", dist, tal, gp)
            merge_vid = _insert_village(db, "Aundh B", dist, tal, gp)

            # Business on keep — should be untouched
            bid_keep = _insert_business(db, "Keep Shop", keep_vid)
            # Business on merge — should be moved
            bid_merge = _insert_business(db, "Merge Shop", merge_vid)

            LocationService.merge_duplicates(db, UUID(keep_vid), [UUID(merge_vid)], level="village")

            # Keep's business unchanged
            row = db.execute(_businesses.select().where(_businesses.c.id == bid_keep)).fetchone()
            assert row.location_id == keep_vid

            # Merge's business moved to keep
            row = db.execute(_businesses.select().where(_businesses.c.id == bid_merge)).fetchone()
            assert row.location_id == keep_vid
        finally:
            svc._VILLAGE_FK_TABLES = original

    def test_merge_multiple_villages(self, db: Session):
        """Merging multiple villages at once."""
        import app.services.location_service as svc

        original = svc._VILLAGE_FK_TABLES
        svc._VILLAGE_FK_TABLES = _TEST_VILLAGE_FK_TABLES
        try:
            dist = _insert_district(db, "Pune")
            tal = _insert_taluka(db, "Haveli", dist)
            gp = _insert_gp(db, "Wadgaon", tal, dist)

            keep_vid = _insert_village(db, "Aundh", dist, tal, gp)
            m1 = _insert_village(db, "Aundh 1", dist, tal, gp)
            m2 = _insert_village(db, "Aundh 2", dist, tal, gp)
            m3 = _insert_village(db, "Aundh 3", dist, tal, gp)

            _insert_business(db, "S1", m1)
            _insert_business(db, "S2", m2)
            _insert_business(db, "S3", m3)

            summary = LocationService.merge_duplicates(
                db, UUID(keep_vid), [UUID(m1), UUID(m2), UUID(m3)], level="village"
            )

            assert summary["villages_deleted"] == 3
            for mid in [m1, m2, m3]:
                assert _count_where(db, _villages, "id", mid) == 0
            assert _count_where(db, _villages, "id", keep_vid) == 1

            # All businesses moved to keep
            all_biz = db.execute(_businesses.select()).fetchall()
            assert all(row.location_id == keep_vid for row in all_biz)
        finally:
            svc._VILLAGE_FK_TABLES = original


# ---------------------------------------------------------------------------
# Taluka merge integration tests
# ---------------------------------------------------------------------------


class TestMergeTalukasIntegration:
    def test_merge_reparents_villages_and_gps(self, db: Session):
        """Merging talukas re-parents both GP and villages."""
        dist = _insert_district(db, "Pune")

        keep_tal = _insert_taluka(db, "Haveli", dist)
        merge_tal = _insert_taluka(db, "Haveli Rural", dist)

        # GP + villages under merge taluka
        gp1 = _insert_gp(db, "GP1", merge_tal, dist)
        v1 = _insert_village(db, "V1", dist, merge_tal, gp1)
        _insert_business(db, "Biz1", v1)

        # GP + village under keep taluka — should be untouched
        gp_keep = _insert_gp(db, "GP Keep", keep_tal, dist)
        _insert_village(db, "V Keep", dist, keep_tal, gp_keep)

        summary = LocationService.merge_duplicates(
            db, UUID(keep_tal), [UUID(merge_tal)], level="taluka"
        )

        # Merge taluka deleted
        assert _count_where(db, _talukas, "id", merge_tal) == 0

        # GP re-parented
        gp_row = db.execute(
            _gram_panchayats.select().where(_gram_panchayats.c.id == gp1)
        ).fetchone()
        assert gp_row.taluka_id == keep_tal

        # Village re-parented
        v_row = db.execute(_villages.select().where(_villages.c.id == v1)).fetchone()
        assert v_row.taluka_id == keep_tal

        # All businesses still exist
        all_biz = db.execute(_businesses.select()).fetchall()
        assert len(all_biz) == 1

        assert summary["talukas_deleted"] == 1


# ---------------------------------------------------------------------------
# District merge integration tests
# ---------------------------------------------------------------------------


class TestMergeDistrictsIntegration:
    def test_merge_reparents_talukas_gps_villages(self, db: Session):
        """Merging districts re-parents all children."""
        keep_dist = _insert_district(db, "Pune")
        merge_dist = _insert_district(db, "Pune Rural")

        # Children under merge district
        tal = _insert_taluka(db, "Haveli", merge_dist)
        gp = _insert_gp(db, "Wadgaon", tal, merge_dist)
        v = _insert_village(db, "Aundh", merge_dist, tal, gp)

        summary = LocationService.merge_duplicates(
            db, UUID(keep_dist), [UUID(merge_dist)], level="district"
        )

        assert summary["districts_deleted"] == 1
        assert _count_where(db, _districts, "id", merge_dist) == 0

        # Taluka re-parented
        tal_row = db.execute(_talukas.select().where(_talukas.c.id == tal)).fetchone()
        assert tal_row.district_id == keep_dist

        # GP re-parented
        gp_row = db.execute(_gram_panchayats.select().where(_gram_panchayats.c.id == gp)).fetchone()
        assert gp_row.district_id == keep_dist

        # Village re-parented
        v_row = db.execute(_villages.select().where(_villages.c.id == v)).fetchone()
        assert v_row.district_id == keep_dist


# ---------------------------------------------------------------------------
# GP merge integration tests
# ---------------------------------------------------------------------------


class TestMergeGPIntegration:
    def test_merge_reparents_villages(self, db: Session):
        """Merging GPs re-parents villages."""
        dist = _insert_district(db, "Pune")
        tal = _insert_taluka(db, "Haveli", dist)

        keep_gp = _insert_gp(db, "Wadgaon", tal, dist)
        merge_gp = _insert_gp(db, "Wadgaon Rural", tal, dist)

        v1 = _insert_village(db, "V1", dist, tal, merge_gp)
        _insert_business(db, "Biz1", v1)

        summary = LocationService.merge_duplicates(
            db, UUID(keep_gp), [UUID(merge_gp)], level="gram_panchayat"
        )

        assert summary["gram_panchayats_deleted"] == 1
        assert _count_where(db, _gram_panchayats, "id", merge_gp) == 0

        v_row = db.execute(_villages.select().where(_villages.c.id == v1)).fetchone()
        assert v_row.gram_panchayat_id == keep_gp


# ---------------------------------------------------------------------------
# Input validation integration tests
# ---------------------------------------------------------------------------


class TestMergeValidationIntegration:
    def test_empty_merge_ids_raises(self, db: Session):
        dist = _insert_district(db, "Pune")
        with pytest.raises(ValueError, match="merge_ids must contain at least one id"):
            LocationService.merge_duplicates(db, UUID(dist), [], level="district")

    def test_keep_id_in_merge_ids_raises(self, db: Session):
        dist = _insert_district(db, "Pune")
        with pytest.raises(ValueError, match="keep_id cannot be in merge_ids"):
            LocationService.merge_duplicates(db, UUID(dist), [UUID(dist)], level="district")

    def test_nonexistent_keep_id_raises(self, db: Session):
        fake_id = uuid4()
        with pytest.raises(ValueError, match="not found"):
            LocationService.merge_duplicates(db, fake_id, [uuid4()], level="district")

    def test_invalid_level_raises(self, db: Session):
        with pytest.raises(ValueError, match="Invalid level"):
            LocationService.merge_duplicates(db, uuid4(), [uuid4()], level="badlevel")


# ---------------------------------------------------------------------------
# Transaction rollback integration tests
# ---------------------------------------------------------------------------


class TestMergeTransactionSafety:
    def test_rollback_on_domain_table_error(self, db: Session):
        """If a domain-table UPDATE fails (simulated), the merge village
        should NOT be deleted — the whole operation rolls back."""
        dist = _insert_district(db, "Pune")
        tal = _insert_taluka(db, "Haveli", dist)
        gp = _insert_gp(db, "Wadgaon", tal, dist)

        keep_vid = _insert_village(db, "Aundh", dist, tal, gp)
        merge_vid = _insert_village(db, "Aundh B", dist, tal, gp)

        _insert_business(db, "Shop", merge_vid)

        # Monkey-patch _VILLAGE_FK_TABLES to include a bogus table that will
        # cause an SQL error on UPDATE.
        import app.services.location_service as svc

        original_tables = svc._VILLAGE_FK_TABLES
        svc._VILLAGE_FK_TABLES = original_tables + [("nonexistent_table_xyz", "location_id")]

        try:
            with pytest.raises(sqlalchemy.exc.OperationalError):
                LocationService.merge_duplicates(
                    db, UUID(keep_vid), [UUID(merge_vid)], level="village"
                )

            # After rollback, merge village should still exist
            assert _count_where(db, _villages, "id", merge_vid) == 1
            assert _count_where(db, _villages, "id", keep_vid) == 1

            # Business should still point to merge village (no partial update)
            biz = db.execute(_businesses.select()).fetchall()
            assert len(biz) == 1
            assert biz[0].location_id == merge_vid
        finally:
            svc._VILLAGE_FK_TABLES = original_tables


# ---------------------------------------------------------------------------
# Normalization + detection integration tests
# ---------------------------------------------------------------------------


class TestDetectDuplicatesIntegration:
    def test_detect_finds_duplicates_in_db(self, db: Session):
        """detect_duplicates actually queries the DB and groups by normalized name."""
        _insert_district(db, "Pune", state="Maharashtra")
        _insert_district(db, "PUNE", state="Maharashtra")
        _insert_district(db, "Pune District", state="Maharashtra")
        _insert_district(db, "Mumbai", state="Maharashtra")

        groups = LocationService.detect_duplicates(db, level="district")
        assert len(groups) == 1
        assert groups[0]["count"] == 3
        names_in_group = {r["name"] for r in groups[0]["records"]}
        assert names_in_group == {"Pune", "PUNE", "Pune District"}

    def test_detect_district_with_state_filter(self, db: Session):
        _insert_district(db, "Pune", state="Maharashtra")
        _insert_district(db, "Pune", state="Karnataka")

        groups = LocationService.detect_duplicates(db, level="district", state="Karnataka")
        # Should only find the Karnataka one — no duplicates (only 1)
        assert len(groups) == 0

    def test_detect_no_duplicates(self, db: Session):
        _insert_district(db, "Pune")
        _insert_district(db, "Mumbai")
        _insert_district(db, "Nagpur")

        groups = LocationService.detect_duplicates(db, level="district")
        assert len(groups) == 0
