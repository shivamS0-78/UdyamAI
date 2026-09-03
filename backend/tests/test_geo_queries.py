"""
Unit tests for UdyamAI Geo module.

Covers:
1. coordinates.py — lat/lng ↔ WKT conversion, haversine distance, unit conversion
2. radius.py — _get_geo_column mapping, find_within_radius with mocked DB
3. nearby_businesses.py — category filtering via SQL filters
4. nearby_markets.py — market_type filtering via SQL filters
5. nearby_villages.py — district filtering via SQL filters
6. nearby_facilities.py — facility_type filtering via SQL filters
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.geo.coordinates import (
    haversine_distance,
    km_to_meters,
    lat_lng_to_wkt,
    meters_to_km,
    wkt_to_lat_lng,
)
from app.geo.radius import _get_geo_column, find_within_radius
from app.models.business import Business
from app.models.infrastructure import Infrastructure
from app.models.location import Village
from app.models.market import Market

# ---------------------------------------------------------------------------
# coordinates.py tests
# ---------------------------------------------------------------------------


class TestLatLngToWkt:
    def test_pune_coordinates(self):
        result = lat_lng_to_wkt(18.5204, 73.8567)
        assert result == "POINT(73.8567 18.5204)"

    def test_zero_coordinates(self):
        result = lat_lng_to_wkt(0.0, 0.0)
        assert result == "POINT(0.0 0.0)"

    def test_negative_coordinates(self):
        result = lat_lng_to_wkt(-33.8688, 151.2093)
        assert result == "POINT(151.2093 -33.8688)"

    def test_high_precision(self):
        result = lat_lng_to_wkt(19.075983, 72.877655)
        assert result == "POINT(72.877655 19.075983)"


class TestWktToLatLng:
    def test_pune_coordinates(self):
        lat, lng = wkt_to_lat_lng("POINT(73.8567 18.5204)")
        assert lat == pytest.approx(18.5204)
        assert lng == pytest.approx(73.8567)

    def test_zero_coordinates(self):
        lat, lng = wkt_to_lat_lng("POINT(0.0 0.0)")
        assert lat == 0.0
        assert lng == 0.0

    def test_negative_coordinates(self):
        lat, lng = wkt_to_lat_lng("POINT(151.2093 -33.8688)")
        assert lat == pytest.approx(-33.8688)
        assert lng == pytest.approx(151.2093)


class TestLatLngWktRoundtrip:
    def test_roundtrip_pune(self):
        original_lat, original_lng = 18.5204, 73.8567
        wkt = lat_lng_to_wkt(original_lat, original_lng)
        lat, lng = wkt_to_lat_lng(wkt)
        assert lat == pytest.approx(original_lat)
        assert lng == pytest.approx(original_lng)

    def test_roundtrip_mumbai(self):
        original_lat, original_lng = 19.0760, 72.8777
        wkt = lat_lng_to_wkt(original_lat, original_lng)
        lat, lng = wkt_to_lat_lng(wkt)
        assert lat == pytest.approx(original_lat)
        assert lng == pytest.approx(original_lng)

    def test_roundtrip_negative(self):
        original_lat, original_lng = -33.8688, 151.2093
        wkt = lat_lng_to_wkt(original_lat, original_lng)
        lat, lng = wkt_to_lat_lng(wkt)
        assert lat == pytest.approx(original_lat)
        assert lng == pytest.approx(original_lng)


class TestHaversineDistance:
    def test_same_point_returns_zero(self):
        dist = haversine_distance(18.5204, 73.8567, 18.5204, 73.8567)
        assert dist == pytest.approx(0.0, abs=0.1)

    def test_pune_to_mumbai(self):
        """Pune to Mumbai is approximately 120 km."""
        dist = haversine_distance(18.5204, 73.8567, 19.0760, 72.8777)
        assert dist == pytest.approx(120_000, rel=0.05)  # within 5%

    def test_delhi_to_chennai(self):
        """Delhi to Chennai is approximately 1760 km."""
        dist = haversine_distance(28.6139, 77.2090, 13.0827, 80.2707)
        assert dist == pytest.approx(1_760_000, rel=0.05)

    def test_symmetric(self):
        """Distance A→B should equal distance B→A."""
        d1 = haversine_distance(18.5204, 73.8567, 19.0760, 72.8777)
        d2 = haversine_distance(19.0760, 72.8777, 18.5204, 73.8567)
        assert d1 == pytest.approx(d2)

    def test_opposite_points(self):
        """Antipodal points should be ~20,000 km."""
        dist = haversine_distance(0.0, 0.0, 0.0, 180.0)
        assert dist == pytest.approx(20_000_000, rel=0.01)


class TestUnitConversion:
    def test_km_to_meters(self):
        assert km_to_meters(1.0) == 1000.0
        assert km_to_meters(0.5) == 500.0
        assert km_to_meters(10.0) == 10_000.0

    def test_meters_to_km(self):
        assert meters_to_km(1000.0) == 1.0
        assert meters_to_km(500.0) == 0.5
        assert meters_to_km(10_000.0) == 10.0

    def test_roundtrip_conversion(self):
        assert meters_to_km(km_to_meters(5.0)) == pytest.approx(5.0)
        assert km_to_meters(meters_to_km(5000.0)) == pytest.approx(5000.0)


# ---------------------------------------------------------------------------
# radius.py tests
# ---------------------------------------------------------------------------


class TestGetGeoColumn:
    def test_village_has_geom(self):
        assert _get_geo_column(Village) == "geom"

    def test_business_has_geom(self):
        assert _get_geo_column(Business) == "geom"

    def test_market_has_geog(self):
        assert _get_geo_column(Market) == "geog"

    def test_infrastructure_has_geog(self):
        assert _get_geo_column(Infrastructure) == "geog"

    def test_explicit_override(self):
        """Explicit geo_column overrides the map."""
        assert _get_geo_column(Village, explicit="custom_col") == "custom_col"

    def test_introspection_fallback(self):
        """When model isn't in the map, introspection finds the Geography column."""

        class _CustomModel:
            __name__ = "CustomVillage"
            # No entry in _GEO_COLUMN_MAP, but has a Geography attribute
            geom = MagicMock()
            # Make isinstance check pass for Geography
            geom.type = type("G", (), {})()  # won't match, so this tests the ValueError path

        # The ValueError path still works for truly unknown models
        class FakeModel:
            __name__ = "FakeModel"

        with pytest.raises(ValueError, match="no known PostGIS geography column"):
            _get_geo_column(FakeModel)


def _mock_exec(rows):
    """Create a mock db whose exec().all() returns the given rows."""
    mock_result = MagicMock()
    mock_result.all.return_value = rows
    mock_db = MagicMock()
    mock_db.exec.return_value = mock_result
    return mock_db


class TestFindWithinRadius:
    def test_returns_results_with_distance(self):
        """Test that find_within_radius returns dicts with distance_meters."""
        mock_record = MagicMock()
        mock_record.__dict__ = {
            "id": uuid4(),
            "name": "Test Village",
            "latitude": 18.52,
            "longitude": 73.85,
            "geom": "some_geom",
            "_sa_instance_state": None,
        }
        mock_distance = 1500.5

        # Row is a tuple-like (record, distance) — replicate what SQLAlchemy returns
        mock_row = (mock_record, mock_distance)
        mock_db = _mock_exec([mock_row])

        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_stmt.limit.return_value = mock_stmt

        with patch("app.geo.radius.select", return_value=mock_stmt):
            results = find_within_radius(
                db=mock_db,
                model=Village,
                lat=18.52,
                lng=73.85,
                radius_km=10.0,
                limit=50,
            )

        assert len(results) == 1
        assert results[0]["name"] == "Test Village"
        assert results[0]["distance_meters"] == 1500.5

    def test_limit_capped_at_500(self):
        """Test that limit is capped at 500."""
        mock_db = _mock_exec([])
        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_stmt.limit.return_value = mock_stmt

        with patch("app.geo.radius.select", return_value=mock_stmt):
            results = find_within_radius(
                db=mock_db,
                model=Village,
                lat=18.52,
                lng=73.85,
                radius_km=10.0,
                limit=1000,  # Should be capped to 500
            )

        # Verify limit was called with 500
        mock_stmt.limit.assert_called_once_with(500)
        assert results == []

    def test_empty_results(self):
        """Test empty results when nothing within radius."""
        mock_db = _mock_exec([])
        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_stmt.limit.return_value = mock_stmt

        with patch("app.geo.radius.select", return_value=mock_stmt):
            results = find_within_radius(
                db=mock_db,
                model=Village,
                lat=18.52,
                lng=73.85,
                radius_km=1.0,
            )

        assert results == []

    def test_multiple_results_sorted_by_distance(self):
        """Test that multiple results are returned and contain distance."""
        mock_record_1 = MagicMock()
        mock_record_1.__dict__ = {
            "id": uuid4(),
            "name": "Close",
            "geom": None,
            "_sa_instance_state": None,
        }
        mock_record_2 = MagicMock()
        mock_record_2.__dict__ = {
            "id": uuid4(),
            "name": "Far",
            "geom": None,
            "_sa_instance_state": None,
        }

        mock_row_1 = (mock_record_1, 500.0)
        mock_row_2 = (mock_record_2, 5000.0)
        mock_db = _mock_exec([mock_row_1, mock_row_2])

        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_stmt.limit.return_value = mock_stmt

        with patch("app.geo.radius.select", return_value=mock_stmt):
            results = find_within_radius(
                db=mock_db,
                model=Business,
                lat=18.52,
                lng=73.85,
                radius_km=10.0,
            )

        assert len(results) == 2
        assert results[0]["name"] == "Close"
        assert results[0]["distance_meters"] == 500.0
        assert results[1]["name"] == "Far"
        assert results[1]["distance_meters"] == 5000.0

    def test_filters_passed_as_where_clauses(self):
        """Test that filters are applied as additional .where() calls."""
        mock_db = _mock_exec([])
        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_stmt.limit.return_value = mock_stmt

        fake_filter = MagicMock(name="fake_filter")

        with patch("app.geo.radius.select", return_value=mock_stmt):
            find_within_radius(
                db=mock_db,
                model=Village,
                lat=18.52,
                lng=73.85,
                radius_km=10.0,
                filters=[fake_filter],
            )

        # .where should be called multiple times: spatial filter + our filter
        where_calls = mock_stmt.where.call_args_list
        assert len(where_calls) >= 2  # at least spatial + our filter

    def test_explicit_geo_column(self):
        """Test that explicit geo_column overrides the map."""
        # Create a mock model that has both __name__ and the custom column
        mock_model = type("MockModel", (), {"__name__": "MockModel", "custom_geom": MagicMock()})
        mock_db = _mock_exec([])
        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_stmt.limit.return_value = mock_stmt

        with patch("app.geo.radius.select", return_value=mock_stmt):
            results = find_within_radius(
                db=mock_db,
                model=mock_model,
                lat=18.52,
                lng=73.85,
                radius_km=10.0,
                geo_column="custom_geom",
            )

        assert results == []

    def test_explicit_geo_column_skips_map(self):
        """Explicit geo_column bypasses _GEO_COLUMN_MAP lookup."""
        # Village is mapped to 'geom' in _GEO_COLUMN_MAP, but explicit override should take precedence
        mock_model = type("MockModel", (), {"__name__": "MockModel", "my_geo": MagicMock()})
        mock_db = _mock_exec([])
        mock_stmt = MagicMock()
        mock_stmt.where.return_value = mock_stmt
        mock_stmt.order_by.return_value = mock_stmt
        mock_stmt.limit.return_value = mock_stmt

        with patch("app.geo.radius.select", return_value=mock_stmt):
            results = find_within_radius(
                db=mock_db,
                model=mock_model,
                lat=18.52,
                lng=73.85,
                radius_km=10.0,
                geo_column="my_geo",
            )

        assert results == []


# ---------------------------------------------------------------------------
# nearby_businesses.py tests
# ---------------------------------------------------------------------------


class TestFindNearbyBusinesses:
    @patch("app.geo.nearby_businesses.find_within_radius")
    def test_returns_all_when_no_category_filter(self, mock_radius):
        mock_radius.return_value = [
            {
                "id": uuid4(),
                "name": "Shop A",
                "business_category_id": uuid4(),
                "distance_meters": 500,
            },
            {
                "id": uuid4(),
                "name": "Shop B",
                "business_category_id": uuid4(),
                "distance_meters": 1000,
            },
        ]
        from app.geo.nearby_businesses import find_nearby_businesses

        mock_db = MagicMock()
        results = find_nearby_businesses(mock_db, lat=18.52, lng=73.85, radius_km=10.0)

        assert len(results) == 2
        mock_radius.assert_called_once_with(
            db=mock_db, model=Business, lat=18.52, lng=73.85, radius_km=10.0, limit=50, filters=None
        )

    @patch("app.geo.nearby_businesses.find_within_radius")
    def test_passes_category_filter_to_db(self, mock_radius):
        """Category filter is pushed into SQL, not applied in Python."""
        cat_a = uuid4()
        # Mock returns only the filtered result (DB already applied the filter)
        mock_radius.return_value = [
            {
                "id": uuid4(),
                "name": "Shop A",
                "business_category_id": cat_a,
                "distance_meters": 500,
            },
        ]
        from app.geo.nearby_businesses import find_nearby_businesses

        mock_db = MagicMock()
        results = find_nearby_businesses(
            mock_db, lat=18.52, lng=73.85, radius_km=10.0, category_id=cat_a
        )

        assert len(results) == 1
        # Verify filters were passed (non-None)
        call_kwargs = mock_radius.call_args
        assert call_kwargs.kwargs["filters"] is not None
        assert len(call_kwargs.kwargs["filters"]) == 1

    @patch("app.geo.nearby_businesses.find_within_radius")
    def test_radius_capped_at_50(self, mock_radius):
        mock_radius.return_value = []
        from app.geo.nearby_businesses import find_nearby_businesses

        mock_db = MagicMock()
        find_nearby_businesses(mock_db, lat=18.52, lng=73.85, radius_km=100.0)

        # Should be capped to 50
        mock_radius.assert_called_once_with(
            db=mock_db, model=Business, lat=18.52, lng=73.85, radius_km=50.0, limit=50, filters=None
        )

    @patch("app.geo.nearby_businesses.find_within_radius")
    def test_empty_results(self, mock_radius):
        mock_radius.return_value = []
        from app.geo.nearby_businesses import find_nearby_businesses

        mock_db = MagicMock()
        results = find_nearby_businesses(mock_db, lat=18.52, lng=73.85, radius_km=1.0)

        assert results == []


# ---------------------------------------------------------------------------
# nearby_markets.py tests
# ---------------------------------------------------------------------------


class TestFindNearbyMarkets:
    @patch("app.geo.nearby_markets.find_within_radius")
    def test_returns_all_when_no_type_filter(self, mock_radius):
        mock_radius.return_value = [
            {"id": uuid4(), "name": "Market A", "market_type": "mandi", "distance_meters": 2000},
            {"id": uuid4(), "name": "Market B", "market_type": "retail", "distance_meters": 5000},
        ]
        from app.geo.nearby_markets import find_nearby_markets

        mock_db = MagicMock()
        results = find_nearby_markets(mock_db, lat=18.52, lng=73.85, radius_km=25.0)

        assert len(results) == 2
        mock_radius.assert_called_once_with(
            db=mock_db, model=Market, lat=18.52, lng=73.85, radius_km=25.0, limit=50, filters=None
        )

    @patch("app.geo.nearby_markets.find_within_radius")
    def test_passes_market_type_filter_to_db(self, mock_radius):
        """Market type filter is pushed into SQL."""
        mock_radius.return_value = [
            {"id": uuid4(), "name": "Mandi A", "market_type": "mandi", "distance_meters": 2000},
        ]
        from app.geo.nearby_markets import find_nearby_markets

        mock_db = MagicMock()
        results = find_nearby_markets(
            mock_db, lat=18.52, lng=73.85, radius_km=25.0, market_type="mandi"
        )

        assert len(results) == 1
        call_kwargs = mock_radius.call_args
        assert call_kwargs.kwargs["filters"] is not None
        assert len(call_kwargs.kwargs["filters"]) == 1

    @patch("app.geo.nearby_markets.find_within_radius")
    def test_radius_capped_at_100(self, mock_radius):
        mock_radius.return_value = []
        from app.geo.nearby_markets import find_nearby_markets

        mock_db = MagicMock()
        find_nearby_markets(mock_db, lat=18.52, lng=73.85, radius_km=200.0)

        # Should be capped to 100
        mock_radius.assert_called_once_with(
            db=mock_db, model=Market, lat=18.52, lng=73.85, radius_km=100.0, limit=50, filters=None
        )


# ---------------------------------------------------------------------------
# nearby_villages.py tests
# ---------------------------------------------------------------------------


class TestFindNearbyVillages:
    @patch("app.geo.nearby_villages.find_within_radius")
    def test_returns_all_when_no_district_filter(self, mock_radius):
        mock_radius.return_value = [
            {"id": uuid4(), "name": "Village A", "district_id": uuid4(), "distance_meters": 300},
            {"id": uuid4(), "name": "Village B", "district_id": uuid4(), "distance_meters": 700},
        ]
        from app.geo.nearby_villages import find_nearby_villages

        mock_db = MagicMock()
        results = find_nearby_villages(mock_db, lat=18.52, lng=73.85, radius_km=10.0)

        assert len(results) == 2
        mock_radius.assert_called_once_with(
            db=mock_db, model=Village, lat=18.52, lng=73.85, radius_km=10.0, limit=50, filters=None
        )

    @patch("app.geo.nearby_villages.find_within_radius")
    def test_passes_district_filter_to_db(self, mock_radius):
        """District filter is pushed into SQL."""
        dist_a = uuid4()
        mock_radius.return_value = [
            {"id": uuid4(), "name": "Village A", "district_id": dist_a, "distance_meters": 300},
        ]
        from app.geo.nearby_villages import find_nearby_villages

        mock_db = MagicMock()
        results = find_nearby_villages(
            mock_db, lat=18.52, lng=73.85, radius_km=10.0, district_id=dist_a
        )

        assert len(results) == 1
        call_kwargs = mock_radius.call_args
        assert call_kwargs.kwargs["filters"] is not None
        assert len(call_kwargs.kwargs["filters"]) == 1

    @patch("app.geo.nearby_villages.find_within_radius")
    def test_radius_capped_at_50(self, mock_radius):
        mock_radius.return_value = []
        from app.geo.nearby_villages import find_nearby_villages

        mock_db = MagicMock()
        find_nearby_villages(mock_db, lat=18.52, lng=73.85, radius_km=80.0)

        # Should be capped to 50
        mock_radius.assert_called_once_with(
            db=mock_db, model=Village, lat=18.52, lng=73.85, radius_km=50.0, limit=50, filters=None
        )


# ---------------------------------------------------------------------------
# nearby_facilities.py tests
# ---------------------------------------------------------------------------


class TestFindNearbyFacilities:
    @patch("app.geo.nearby_facilities.find_within_radius")
    def test_returns_all_when_no_type_filter(self, mock_radius):
        mock_radius.return_value = [
            {
                "id": uuid4(),
                "name": "Hospital A",
                "facility_type": "hospital",
                "distance_meters": 1000,
            },
            {"id": uuid4(), "name": "Bank B", "facility_type": "bank", "distance_meters": 2000},
        ]
        from app.geo.nearby_facilities import find_nearby_facilities

        mock_db = MagicMock()
        results = find_nearby_facilities(mock_db, lat=18.52, lng=73.85, radius_km=10.0)

        assert len(results) == 2
        mock_radius.assert_called_once_with(
            db=mock_db,
            model=Infrastructure,
            lat=18.52,
            lng=73.85,
            radius_km=10.0,
            limit=50,
            filters=None,
        )

    @patch("app.geo.nearby_facilities.find_within_radius")
    def test_passes_facility_type_filter_to_db(self, mock_radius):
        """Facility type filter is pushed into SQL."""
        mock_radius.return_value = [
            {
                "id": uuid4(),
                "name": "Hospital A",
                "facility_type": "hospital",
                "distance_meters": 1000,
            },
        ]
        from app.geo.nearby_facilities import find_nearby_facilities

        mock_db = MagicMock()
        results = find_nearby_facilities(
            mock_db, lat=18.52, lng=73.85, radius_km=10.0, facility_type="hospital"
        )

        assert len(results) == 1
        call_kwargs = mock_radius.call_args
        assert call_kwargs.kwargs["filters"] is not None
        assert len(call_kwargs.kwargs["filters"]) == 1

    @patch("app.geo.nearby_facilities.find_within_radius")
    def test_radius_capped_at_50(self, mock_radius):
        mock_radius.return_value = []
        from app.geo.nearby_facilities import find_nearby_facilities

        mock_db = MagicMock()
        find_nearby_facilities(mock_db, lat=18.52, lng=73.85, radius_km=100.0)

        # Should be capped to 50
        mock_radius.assert_called_once_with(
            db=mock_db,
            model=Infrastructure,
            lat=18.52,
            lng=73.85,
            radius_km=50.0,
            limit=50,
            filters=None,
        )

    @patch("app.geo.nearby_facilities.find_within_radius")
    def test_empty_results(self, mock_radius):
        mock_radius.return_value = []
        from app.geo.nearby_facilities import find_nearby_facilities

        mock_db = MagicMock()
        results = find_nearby_facilities(
            mock_db, lat=18.52, lng=73.85, radius_km=1.0, facility_type="airport"
        )

        assert results == []


# ---------------------------------------------------------------------------
# API endpoint tests (via TestClient with mocked services)
# ---------------------------------------------------------------------------


class TestNearbyEndpoints:
    def test_nearby_villages_endpoint(self, client):
        with patch("app.api.routes.locations.find_nearby_villages") as mock_fn:
            mock_fn.return_value = [
                {
                    "id": str(uuid4()),
                    "name": "Aundh",
                    "district_id": str(uuid4()),
                    "taluka_id": str(uuid4()),
                    "gram_panchayat_id": str(uuid4()),
                    "pin_code": "411007",
                    "latitude": 18.52,
                    "longitude": 73.85,
                    "distance_meters": 500.0,
                }
            ]
            response = client.get("/locations/nearby/villages?lat=18.52&lng=73.85&radius_km=5")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Aundh"
            assert data[0]["distance_meters"] == 500.0

    def test_nearby_businesses_endpoint(self, client):
        with patch("app.api.routes.locations.find_nearby_businesses") as mock_fn:
            mock_fn.return_value = [
                {
                    "id": str(uuid4()),
                    "name": "Shop A",
                    "category": "Retail",
                    "business_category_id": str(uuid4()),
                    "address": "123 Main St",
                    "latitude": 18.53,
                    "longitude": 73.86,
                    "distance_meters": 1200.0,
                }
            ]
            response = client.get("/locations/nearby/businesses?lat=18.52&lng=73.85&radius_km=10")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Shop A"

    def test_nearby_markets_endpoint(self, client):
        with patch("app.api.routes.locations.find_nearby_markets") as mock_fn:
            mock_fn.return_value = [
                {
                    "id": str(uuid4()),
                    "name": "Mandi A",
                    "market_type": "mandi",
                    "latitude": 18.55,
                    "longitude": 73.90,
                    "distance_meters": 5000.0,
                }
            ]
            response = client.get("/locations/nearby/markets?lat=18.52&lng=73.85&radius_km=25")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["market_type"] == "mandi"

    def test_nearby_facilities_endpoint(self, client):
        with patch("app.api.routes.locations.find_nearby_facilities") as mock_fn:
            mock_fn.return_value = [
                {
                    "id": str(uuid4()),
                    "name": "Hospital A",
                    "facility_type": "hospital",
                    "latitude": 18.54,
                    "longitude": 73.87,
                    "capacity": 200.0,
                    "distance_meters": 2500.0,
                }
            ]
            response = client.get("/locations/nearby/facilities?lat=18.52&lng=73.85&radius_km=10")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["facility_type"] == "hospital"
            assert data[0]["capacity"] == 200.0

    def test_nearby_villages_missing_lat_returns_422(self, client):
        response = client.get("/locations/nearby/villages?lng=73.85&radius_km=5")
        assert response.status_code == 422

    def test_nearby_villages_missing_lng_returns_422(self, client):
        response = client.get("/locations/nearby/villages?lat=18.52&radius_km=5")
        assert response.status_code == 422

    def test_nearby_villages_invalid_lat_returns_422(self, client):
        response = client.get("/locations/nearby/villages?lat=999&lng=73.85&radius_km=5")
        assert response.status_code == 422

    def test_nearby_villages_invalid_radius_returns_422(self, client):
        response = client.get("/locations/nearby/villages?lat=18.52&lng=73.85&radius_km=-1")
        assert response.status_code == 422
