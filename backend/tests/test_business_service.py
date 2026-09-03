"""Unit tests for BusinessService query functions."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models.business import Business, BusinessCategory, BusinessModel
from app.services.business_service import BusinessService

# ------------------------------------------------------------------ #
# Business category queries
# ------------------------------------------------------------------ #


class TestGetBusinessCategories:
    def test_returns_active_categories(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            BusinessCategory(id=uuid4(), name="Dairy", sector="Agriculture"),
            BusinessCategory(id=uuid4(), name="Retail", sector="Services"),
        ]
        results = BusinessService.get_business_categories(mock_db)
        assert len(results) == 2
        assert results[0].name == "Dairy"

    def test_returns_empty_list(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []
        assert BusinessService.get_business_categories(mock_db) == []

    def test_executes_statement_once(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []
        BusinessService.get_business_categories(mock_db)
        mock_db.exec.assert_called_once()


# ------------------------------------------------------------------ #
# Business model (reference data) queries
# ------------------------------------------------------------------ #


class TestGetBusinessModels:
    def test_returns_all_models(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            BusinessModel(id=uuid4(), business_category_id=uuid4(), name="Dairy Farm"),
            BusinessModel(id=uuid4(), business_category_id=uuid4(), name="Poultry Unit"),
        ]
        results = BusinessService.get_business_models(mock_db)
        assert len(results) == 2

    def test_filters_by_category_id(self):
        category_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            BusinessModel(id=uuid4(), business_category_id=category_id, name="Dairy Farm"),
        ]
        results = BusinessService.get_business_models(mock_db, business_category_id=category_id)
        assert len(results) == 1
        assert results[0].business_category_id == category_id

    def test_limit_capped_at_200(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []
        BusinessService.get_business_models(mock_db, limit=500)
        # Should not raise, limit capped internally


# ------------------------------------------------------------------ #
# Business queries
# ------------------------------------------------------------------ #


class TestGetBusinesses:
    def test_returns_all_businesses(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Business(id=uuid4(), name="Shop A"),
            Business(id=uuid4(), name="Shop B"),
        ]
        results = BusinessService.get_businesses(mock_db)
        assert len(results) == 2

    def test_filters_by_category_id(self):
        category_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Business(id=uuid4(), name="Dairy Co", business_category_id=category_id),
        ]
        results = BusinessService.get_businesses(mock_db, business_category_id=category_id)
        assert len(results) == 1
        assert results[0].business_category_id == category_id

    def test_filters_by_location_id(self):
        location_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Business(id=uuid4(), name="Village Kirana", location_id=location_id),
        ]
        results = BusinessService.get_businesses(mock_db, location_id=location_id)
        assert len(results) == 1
        assert results[0].location_id == location_id

    def test_filters_by_category_and_location(self):
        category_id = uuid4()
        location_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Business(
                id=uuid4(),
                name="Combo",
                business_category_id=category_id,
                location_id=location_id,
            ),
        ]
        results = BusinessService.get_businesses(
            mock_db, business_category_id=category_id, location_id=location_id
        )
        assert len(results) == 1
        assert results[0].business_category_id == category_id
        assert results[0].location_id == location_id

    def test_limit_capped_at_200(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []
        BusinessService.get_businesses(mock_db, limit=500)
        # Should not raise, limit capped internally


class TestGetBusinessById:
    def test_returns_business(self):
        business_id = uuid4()
        mock_db = MagicMock()
        mock_db.get.return_value = Business(id=business_id, name="Test Business")
        result = BusinessService.get_business_by_id(mock_db, business_id)
        assert result is not None
        assert result.name == "Test Business"
        mock_db.get.assert_called_once_with(Business, business_id)

    def test_returns_none_when_not_found(self):
        mock_db = MagicMock()
        mock_db.get.return_value = None
        assert BusinessService.get_business_by_id(mock_db, uuid4()) is None


# ------------------------------------------------------------------ #
# Nearby businesses (PostGIS wrapper)
# ------------------------------------------------------------------ #


class TestGetNearbyBusinesses:
    @patch("app.services.business_service.find_nearby_businesses")
    def test_delegates_to_geo_module(self, mock_find):
        mock_db = MagicMock()
        mock_find.return_value = [{"name": "Nearby Shop", "distance_meters": 1200.0}]
        results = BusinessService.get_nearby_businesses(mock_db, lat=18.52, lng=73.85)
        assert results == [{"name": "Nearby Shop", "distance_meters": 1200.0}]
        mock_find.assert_called_once_with(
            db=mock_db,
            lat=18.52,
            lng=73.85,
            radius_km=10.0,
            category_id=None,
            limit=50,
        )

    @patch("app.services.business_service.find_nearby_businesses")
    def test_passes_explicit_params(self, mock_find):
        mock_db = MagicMock()
        category_id = uuid4()
        mock_find.return_value = []
        BusinessService.get_nearby_businesses(
            mock_db, lat=19.99, lng=73.5, radius_km=25.0, category_id=category_id, limit=10
        )
        mock_find.assert_called_once_with(
            db=mock_db,
            lat=19.99,
            lng=73.5,
            radius_km=25.0,
            category_id=category_id,
            limit=10,
        )
