"""Tests for location normalization, matching, resolution, and deduplication."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.location import (
    District,
    GramPanchayat,
    Taluka,
    Village,
)
from app.services.location_service import (
    LocationService,
    normalize_for_match,
    normalize_name,
    remove_fillers,
    remove_punctuation,
    remove_suffixes,
)

# ---------------------------------------------------------------------------
# Normalizer Tests
# ---------------------------------------------------------------------------


class TestNormalizeName:
    def test_lowercase(self):
        assert normalize_name("PUNE") == "pune"

    def test_strip_whitespace(self):
        assert normalize_name("  Pune  ") == "pune"

    def test_collapse_whitespace(self):
        assert normalize_name("Pune   City") == "pune city"

    def test_strip_accents(self):
        assert normalize_name("São Paulo") == "sao paulo"

    def test_mixed_case(self):
        assert normalize_name("pUnE dIsTrIcT") == "pune district"


class TestRemoveSuffixes:
    def test_district(self):
        assert remove_suffixes("pune district") == "pune"

    def test_taluka(self):
        assert remove_suffixes("haveli taluka") == "haveli"

    def test_village(self):
        assert remove_suffixes("aundh village") == "aundh"

    def test_tehsil(self):
        assert remove_suffixes("bla tehsil") == "bla"

    def test_gram_panchayat(self):
        assert remove_suffixes("wadgaon gram panchayat") == "wadgaon"

    def test_municipal_council(self):
        assert remove_suffixes("pune municipal council") == "pune"

    def test_no_suffix(self):
        assert remove_suffixes("pune") == "pune"

    def test_suffix_in_middle_not_removed(self):
        # Only suffixes at end are removed
        assert remove_suffixes("district headquarters") == "district headquarters"


class TestRemoveFillers:
    def test_the(self):
        assert remove_fillers("the pune") == "pune"

    def test_of(self):
        assert remove_fillers("city of pune") == "city pune"

    def test_multiple_fillers(self):
        assert remove_fillers("the city of pune") == "city pune"

    def test_no_fillers(self):
        assert remove_fillers("pune") == "pune"


class TestRemovePunctuation:
    def test_parentheses(self):
        assert remove_punctuation("pune (rural)") == "pune rural"

    def test_commas(self):
        assert remove_punctuation("pune, maharashtra") == "pune maharashtra"

    def test_special_chars(self):
        assert remove_punctuation("pune-city!@#") == "pune city"

    def test_no_punctuation(self):
        assert remove_punctuation("pune") == "pune"


class TestNormalizeForMatch:
    def test_full_pipeline_basic(self):
        assert normalize_for_match("Pune") == "pune"

    def test_full_pipeline_with_suffix(self):
        assert normalize_for_match("Pune District") == "pune"

    def test_full_pipeline_with_parens(self):
        assert normalize_for_match("Pune (Rural)") == "pune rural"

    def test_full_pipeline_complex(self):
        assert normalize_for_match("  The Pune District  ") == "pune"

    def test_full_pipeline_filler_and_suffix(self):
        assert normalize_for_match("The City of Pune Municipal Corporation") == "city pune"

    def test_fuzzy_match_scenario(self):
        """Two differently-spelled names should normalize similarly."""
        a = normalize_for_match("Pune")
        b = normalize_for_match("PUNE")
        assert a == b

    def test_suffix_only_input(self):
        """Edge case: input is just a suffix — falls back to cleaned original."""
        result = normalize_for_match("District")
        # Normalization yields empty after removing suffix, so falls back
        # to the original stripped/lowercased name
        assert result == "district"


# ---------------------------------------------------------------------------
# Matcher Tests (mocked DB)
# ---------------------------------------------------------------------------


def _make_district(name="Pune", state="Maharashtra", lgd_code=None):
    return District(id=uuid4(), name=name, state=state, lgd_code=lgd_code)


def _make_taluka(name="Haveli", district_id=None, lgd_code=None):
    return Taluka(id=uuid4(), name=name, district_id=district_id or uuid4(), lgd_code=lgd_code)


def _make_gp(name="Wadgaon", taluka_id=None, district_id=None, lgd_code=None):
    return GramPanchayat(
        id=uuid4(),
        name=name,
        taluka_id=taluka_id or uuid4(),
        district_id=district_id or uuid4(),
        lgd_code=lgd_code,
    )


def _make_village(name="Aundh", taluka_id=None, lgd_code=None):
    return Village(
        id=uuid4(),
        name=name,
        district_id=uuid4(),
        taluka_id=taluka_id or uuid4(),
        gram_panchayat_id=uuid4(),
        lgd_code=lgd_code,
    )


class TestFindDistrict:
    def test_lgd_code_match(self):
        db = MagicMock()
        d = _make_district(lgd_code="2712")
        db.exec.return_value.first.return_value = d
        result = LocationService.find_district(db, "anything", lgd_code="2712")
        assert result == d

    def test_exact_name_match(self):
        db = MagicMock()
        d = _make_district(name="Pune")
        db.exec.return_value.all.return_value = [d]
        result = LocationService.find_district(db, "Pune")
        assert result == d

    def test_fuzzy_name_match(self):
        db = MagicMock()
        d = _make_district(name="Pune")
        db.exec.return_value.all.return_value = [d]
        # "Pne" is close enough to "Pune" with fuzzy threshold 0.85
        result = LocationService.find_district(db, "Pne", fuzzy_threshold=0.75)
        assert result == d

    def test_no_match(self):
        db = MagicMock()
        d = _make_district(name="Pune")
        db.exec.return_value.all.return_value = [d]
        result = LocationService.find_district(db, "Mumbai")
        assert result is None

    def test_state_filter(self):
        db = MagicMock()
        d2 = _make_district(name="Pune", state="Karnataka")
        # State filtering now happens in SQL, so mock returns pre-filtered results
        db.exec.return_value.all.return_value = [d2]
        result = LocationService.find_district(db, "Pune", state="Karnataka")
        assert result == d2


class TestFindTaluka:
    def test_exact_match(self):
        db = MagicMock()
        district_id = uuid4()
        t = _make_taluka(name="Haveli", district_id=district_id)
        db.exec.return_value.all.return_value = [t]
        result = LocationService.find_taluka(db, "Haveli", district_id=district_id)
        assert result == t

    def test_fuzzy_match(self):
        db = MagicMock()
        district_id = uuid4()
        t = _make_taluka(name="Haveli", district_id=district_id)
        db.exec.return_value.all.return_value = [t]
        result = LocationService.find_taluka(
            db, "Havli", district_id=district_id, fuzzy_threshold=0.80
        )
        assert result == t

    def test_scoped_to_district(self):
        db = MagicMock()
        d_id = uuid4()
        other_d_id = uuid4()
        t1 = _make_taluka(name="Haveli", district_id=d_id)
        t2 = _make_taluka(name="Haveli", district_id=other_d_id)
        db.exec.return_value.all.return_value = [t1, t2]
        result = LocationService.find_taluka(db, "Haveli", district_id=d_id)
        assert result == t1


class TestFindVillage:
    def test_exact_match(self):
        db = MagicMock()
        taluka_id = uuid4()
        v = _make_village(name="Aundh", taluka_id=taluka_id)
        db.exec.return_value.all.return_value = [v]
        result = LocationService.find_village(db, "Aundh", taluka_id=taluka_id)
        assert result == v

    def test_lgd_code_match(self):
        db = MagicMock()
        taluka_id = uuid4()
        v = _make_village(name="Aundh", taluka_id=taluka_id, lgd_code="999")
        db.exec.return_value.first.return_value = v
        result = LocationService.find_village(db, "Anything", taluka_id=taluka_id, lgd_code="999")
        assert result == v


# ---------------------------------------------------------------------------
# resolve_location Tests
# ---------------------------------------------------------------------------


class TestResolveLocation:
    @patch("app.services.location_service.LocationService.find_district")
    def test_resolve_existing_district(self, mock_find):
        db = MagicMock()
        d = _make_district(name="Pune")
        mock_find.return_value = d
        result = LocationService.resolve_location(db, "Pune", level="district")
        assert result == d.id

    @patch("app.services.location_service.LocationService.find_district")
    def test_resolve_new_district(self, mock_find):
        db = MagicMock()
        mock_find.return_value = None
        result = LocationService.resolve_location(
            db, "New District", level="district", state="Maharashtra"
        )
        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert isinstance(result, uuid4().__class__)

    @patch("app.services.location_service.LocationService.find_village")
    def test_resolve_existing_village(self, mock_find):
        db = MagicMock()
        v = _make_village(name="Aundh")
        mock_find.return_value = v
        taluka_id = uuid4()
        result = LocationService.resolve_location(db, "Aundh", level="village", taluka_id=taluka_id)
        assert result == v.id

    def test_resolve_missing_parent_raises(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="district_id is required"):
            LocationService.resolve_location(db, "Haveli", level="taluka")

    def test_resolve_invalid_level_raises(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="Invalid level"):
            LocationService.resolve_location(db, "X", level="invalid")


# ---------------------------------------------------------------------------
# Deduplication Tests
# ---------------------------------------------------------------------------


class TestDetectDuplicates:
    def test_detect_district_duplicates(self):
        db = MagicMock()
        d1 = _make_district(name="Pune")
        d2 = _make_district(name="PUNE")
        d3 = _make_district(name="Pune District")
        db.exec.return_value.all.return_value = [d1, d2, d3]

        groups = LocationService.detect_duplicates(db, level="district")
        assert len(groups) >= 1
        assert groups[0]["count"] == 3

    def test_detect_no_duplicates(self):
        db = MagicMock()
        d1 = _make_district(name="Pune")
        d2 = _make_district(name="Mumbai")
        db.exec.return_value.all.return_value = [d1, d2]

        groups = LocationService.detect_duplicates(db, level="district")
        assert len(groups) == 0

    def test_detect_empty_db(self):
        db = MagicMock()
        db.exec.return_value.all.return_value = []

        groups = LocationService.detect_duplicates(db, level="district")
        assert groups == []

    def test_detect_village_duplicates_scoped_to_taluka(self):
        db = MagicMock()
        taluka_id = uuid4()
        v1 = _make_village(name="Aundh", taluka_id=taluka_id)
        v2 = _make_village(name="AUNDH", taluka_id=taluka_id)
        v3 = _make_village(name="Aundh Village", taluka_id=taluka_id)
        db.exec.return_value.all.return_value = [v1, v2, v3]

        groups = LocationService.detect_duplicates(db, level="village")
        assert len(groups) >= 1


class TestMergeDuplicates:
    def test_merge_villages_reparents_domain_tables(self):
        db = MagicMock()
        keep_id = uuid4()
        merge_id = uuid4()

        # Mock execute to return a mock with rowcount
        mock_result = MagicMock()
        mock_result.rowcount = 3
        db.execute.return_value = mock_result

        summary = LocationService.merge_duplicates(
            db, keep_id=keep_id, merge_ids=[merge_id], level="village"
        )

        # Should have called db.execute for each domain table + delete
        assert db.execute.call_count >= len(
            [
                ("agriculture", "location_id"),
                ("analysis_runs", "location_id"),
                ("businesses", "location_id"),
                ("livestock", "location_id"),
                ("markets", "location_id"),
                ("population", "location_id"),
                ("weather", "location_id"),
            ]
        )
        assert "villages_deleted" in summary
        db.commit.assert_called_once()

    def test_merge_invalid_level_raises(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="Invalid level"):
            LocationService.merge_duplicates(
                db, keep_id=uuid4(), merge_ids=[uuid4()], level="invalid"
            )

    def test_merge_talukas(self):
        db = MagicMock()
        keep_id = uuid4()
        merge_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 2
        db.execute.return_value = mock_result
        db.exec.return_value.all.return_value = []

        summary = LocationService.merge_duplicates(
            db, keep_id=keep_id, merge_ids=[merge_id], level="taluka"
        )
        assert "talukas_deleted" in summary
        db.commit.assert_called_once()

    def test_merge_districts(self):
        db = MagicMock()
        keep_id = uuid4()
        merge_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 5
        db.execute.return_value = mock_result

        summary = LocationService.merge_duplicates(
            db, keep_id=keep_id, merge_ids=[merge_id], level="district"
        )
        assert "districts_deleted" in summary
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------


class TestNormalizeEndpoint:
    def test_normalize_basic(self, client):
        response = client.post(
            "/locations/normalize",
            json={"name": "Pune District", "level": "district"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original"] == "Pune District"
        assert data["normalized"] == "pune"
        assert data["level"] == "district"

    def test_normalize_with_suffix(self, client):
        response = client.post(
            "/locations/normalize",
            json={"name": "  Haveli Taluka  ", "level": "taluka"},
        )
        assert response.status_code == 200
        assert response.json()["normalized"] == "haveli"

    def test_normalize_with_parens(self, client):
        response = client.post(
            "/locations/normalize",
            json={"name": "Pune (Rural)", "level": "village"},
        )
        assert response.status_code == 200
        assert response.json()["normalized"] == "pune rural"


class TestDedupDetectEndpoint:
    def test_detect_duplicates(self, client):
        with patch("app.api.routes.locations.LocationService.detect_duplicates") as mock_detect:
            mock_detect.return_value = [
                {
                    "normalized_name": "pune",
                    "count": 2,
                    "records": [
                        {
                            "id": str(uuid4()),
                            "name": "Pune",
                            "normalized": "pune",
                            "lgd_code": None,
                        },
                        {
                            "id": str(uuid4()),
                            "name": "PUNE",
                            "normalized": "pune",
                            "lgd_code": None,
                        },
                    ],
                }
            ]
            response = client.get("/locations/dedup/detect?level=district")
            assert response.status_code == 200
            data = response.json()
            assert data["level"] == "district"
            assert data["total_groups"] == 1
            assert data["groups"][0]["count"] == 2


class TestDedupMergeEndpoint:
    def test_merge_duplicates(self, client):
        with patch("app.api.routes.locations.LocationService.merge_duplicates") as mock_merge:
            mock_merge.return_value = {
                "villages.taluka_id": 5,
                "villages_deleted": 1,
            }
            keep_id = uuid4()
            merge_id = uuid4()
            response = client.post(
                "/locations/dedup/merge",
                json={
                    "keep_id": str(keep_id),
                    "merge_ids": [str(merge_id)],
                    "level": "village",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["keep_id"] == str(keep_id)
            assert data["merged_count"] == 1
            assert data["summary"]["villages_deleted"] == 1
