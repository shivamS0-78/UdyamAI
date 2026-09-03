"""Unit and integration tests for Phase 7 - Competition Analysis."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.market.competition import analyze_competition
from app.schemas.market import CompetitionAnalysisDetailResponse
from app.services.market_service import MarketService


class TestPhase7CompetitionAnalysis:
    """Test suite for Phase 7 competition calculation engine."""

    def test_filter_by_category_dairy(self):
        """User selects Dairy -> Only Dairy businesses counted as direct competitors."""
        dairy_cat_id = str(uuid4())
        retail_cat_id = str(uuid4())

        businesses = [
            # Dairy competitors
            {
                "id": uuid4(),
                "business_category_id": dairy_cat_id,
                "category": "Dairy Processing",
                "distance_meters": 2000.0,
                "verified_at": datetime.utcnow(),
                "source": "MSME Directory",
            },
            {
                "id": uuid4(),
                "business_category_id": dairy_cat_id,
                "category": "Dairy Farm",
                "distance_meters": 4500.0,
                "verified_at": datetime.utcnow(),
                "source": "MSME Directory",
            },
            {
                "id": uuid4(),
                "business_category_id": dairy_cat_id,
                "category": "Dairy Retail",
                "distance_meters": 8000.0,
                "source": "Local Directory",
            },
            # Non-dairy businesses (general commercial, NOT direct competitors)
            {
                "id": uuid4(),
                "business_category_id": retail_cat_id,
                "category": "General Store",
                "distance_meters": 3000.0,
                "source": "Trade Registry",
            },
            {
                "id": uuid4(),
                "business_category_id": retail_cat_id,
                "category": "Garments",
                "distance_meters": 6000.0,
                "source": "Trade Registry",
            },
        ]

        # Run analysis for Dairy
        res = analyze_competition(
            businesses=businesses,
            radius_km=10.0,
            target_category_id=dairy_cat_id,
            target_category_name="Dairy",
        )

        assert res["total_businesses_in_radius"] == 5
        assert res["competitor_count"] == 3  # Only 3 dairy businesses, NOT all 5!
        assert res["direct_competitor_count"] == 3
        # Competitor density based on direct competitors (3 / (π * 10^2))
        expected_density = round(3 / (3.1415926535 * 100), 2)
        assert res["competitor_density"] == expected_density

        # Distance breakdown
        assert res["businesses_within_5km"] == 2  # 2 dairy competitors <= 5km
        assert res["businesses_within_10km"] == 3  # 3 dairy competitors <= 10km

    def test_filter_by_category_name_fuzzy(self):
        """Category name matching when target_category_id is None."""
        businesses = [
            {"id": uuid4(), "category": "Dairy Retail Outlet", "distance_meters": 1500.0},
            {"id": uuid4(), "category": "Dairy Collection Center", "distance_meters": 3500.0},
            {"id": uuid4(), "category": "Bakery", "distance_meters": 2500.0},
        ]

        res = analyze_competition(
            businesses=businesses,
            radius_km=5.0,
            target_category_name="Dairy",
        )

        assert res["competitor_count"] == 2
        assert res["total_businesses_in_radius"] == 3
        assert res["businesses_within_5km"] == 2

    def test_missing_distance_meters_not_in_5km_10km_buckets(self):
        """Businesses missing distance_meters should NOT be falsely categorized in 5km/10km buckets."""
        businesses = [
            {"id": uuid4(), "category": "Dairy", "distance_meters": None},  # Missing distance
            {"id": uuid4(), "category": "Dairy", "distance_meters": 4000.0},  # Within 5km & 10km
            {"id": uuid4(), "category": "Dairy", "distance_meters": 8000.0},  # Within 10km only
        ]

        res = analyze_competition(
            businesses=businesses,
            radius_km=10.0,
            target_category_name="Dairy",
        )

        assert res["competitor_count"] == 3  # All 3 are competitors
        assert res["businesses_within_5km"] == 1  # Only the 4000m business
        assert res["businesses_within_10km"] == 2  # The 4000m & 8000m businesses

    def test_empty_string_category_name_normalized(self):
        """Empty string category name '' should be normalized to None without filter crash."""
        businesses = [
            {"id": uuid4(), "category": "Dairy", "distance_meters": 2000.0},
            {"id": uuid4(), "category": "Retail", "distance_meters": 3000.0},
        ]

        res = analyze_competition(
            businesses=businesses,
            radius_km=5.0,
            target_category_name="   ",  # Whitespace only
        )

        # Should behave as no filter
        assert res["competitor_count"] == 2
        assert res["quality_indicator"]["has_category_filter"] is False

    def test_data_completeness_and_quality_indicator(self):
        """Completeness score and verified ratio reporting."""
        businesses = [
            {
                "id": uuid4(),
                "category": "Dairy",
                "verified_at": datetime.utcnow(),
                "source": "Official Registry",
            },
            {
                "id": uuid4(),
                "category": "Dairy",
                "verified_at": datetime.utcnow(),
                "source": "Official Registry",
            },
            {"id": uuid4(), "category": "Dairy", "verified_at": None, "source": "Unverified Feed"},
        ]

        res = analyze_competition(
            businesses=businesses,
            radius_km=5.0,
            target_category_name="Dairy",
        )

        quality = res["quality_indicator"]
        assert quality["total_records_count"] == 3
        assert quality["verified_records_count"] == 2
        assert quality["has_category_filter"] is True
        assert quality["confidence_level"] == "high"  # 2/3 >= 50% verified
        assert quality["completeness_score"] > 0.8
        assert "Official Registry" in quality["sources_covered"]

    def test_zero_fabrication_rule(self):
        """Never fabricate competitor counts when zero exist in DB."""
        businesses = []

        res = analyze_competition(
            businesses=businesses,
            radius_km=10.0,
            target_category_name="Dairy",
        )

        assert res["competitor_count"] == 0
        assert res["competitor_density"] == 0.0
        assert res["businesses_within_5km"] == 0
        assert res["businesses_within_10km"] == 0

        quality = res["quality_indicator"]
        assert quality["confidence_level"] == "low"
        assert "No businesses recorded in database" in quality["notes"]


class TestMarketServiceCompetitionOrchestration:
    """Test MarketService.analyze_competition_for_location."""

    def test_analyze_competition_for_location_service(self):
        mock_db = MagicMock()
        mock_db.get.return_value = None  # Fallback to lat/lng

        biz_data = [
            {
                "id": uuid4(),
                "business_category_id": uuid4(),
                "category": "Dairy Farm",
                "distance_meters": 3000.0,
                "verified_at": datetime.utcnow(),
                "source": "MSME Directory",
            }
        ]

        with patch("app.services.market_service.find_nearby_businesses", return_value=biz_data):
            res = MarketService.analyze_competition_for_location(
                db=mock_db,
                lat=18.52,
                lng=73.85,
                radius_km=10.0,
                category_name="Dairy",
            )

            assert isinstance(res, CompetitionAnalysisDetailResponse)
            assert res.competitor_count == 1
            assert res.businesses_within_5km == 1
            assert res.businesses_within_10km == 1
            assert res.target_category == "Dairy"
            assert res.quality_indicator["verified_records_count"] == 1

    def test_missing_coordinates_and_village_raises_400(self):
        """When no lat/lng and no village_id are provided, raise HTTPException 400."""
        from fastapi import HTTPException

        mock_db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            MarketService.analyze_competition_for_location(db=mock_db)

        assert exc_info.value.status_code == 400
        assert "required for competition analysis" in exc_info.value.detail

    def test_non_existent_village_id_raises_404(self):
        """When village_id does not exist in DB and no lat/lng supplied, raise 404."""
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            MarketService.analyze_competition_for_location(db=mock_db, village_id=uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    def test_village_missing_coordinates_raises_400(self):
        """When village exists in DB but has null latitude/longitude, raise 400."""
        from fastapi import HTTPException

        from app.models.location import Village

        mock_db = MagicMock()
        mock_village = Village(id=uuid4(), name="No Geo Vil", latitude=None, longitude=None)
        mock_db.get.return_value = mock_village

        with pytest.raises(HTTPException) as exc_info:
            MarketService.analyze_competition_for_location(db=mock_db, village_id=mock_village.id)

        assert exc_info.value.status_code == 400
        assert "missing latitude/longitude coordinates" in exc_info.value.detail

    def test_lat_lng_takes_precedence_over_village_id(self):
        """User provided lat/lng takes precedence over village DB lookup."""
        from app.models.location import Village

        mock_db = MagicMock()
        mock_village = Village(id=uuid4(), name="Test Vil", latitude=10.0, longitude=10.0)
        mock_db.get.return_value = mock_village

        with patch("app.services.market_service.find_nearby_businesses") as mock_find:
            mock_find.return_value = []
            res = MarketService.analyze_competition_for_location(
                db=mock_db,
                village_id=mock_village.id,
                lat=18.52,  # User override
                lng=73.85,  # User override
            )

            assert res is not None
            # Verify find_nearby_businesses was called with user's override lat/lng (18.52, 73.85), NOT village's (10.0, 10.0)
            mock_find.assert_called_once_with(
                mock_db,
                lat=18.52,
                lng=73.85,
                radius_km=10.0,
                category_id=None,
                limit=500,
            )


class TestCompetitionAPIEndpoints:
    """Test API route endpoints for Phase 7 Competition Analysis."""

    def test_post_competition_endpoint(self, client):
        v_id = uuid4()
        cat_id = uuid4()

        with patch(
            "app.api.routes.markets.MarketService.analyze_competition_for_location"
        ) as mock_fn:
            mock_fn.return_value = CompetitionAnalysisDetailResponse(
                competitor_count=2,
                competitor_density=0.01,
                businesses_within_5km=1,
                businesses_within_10km=2,
                total_businesses_in_radius=5,
                target_category="Dairy",
                category_distribution={"Dairy": 2, "Retail": 3},
                identified_market_gaps=["Low commercial saturation"],
                quality_indicator={
                    "completeness_score": 0.85,
                    "confidence_level": "high",
                    "verified_records_count": 4,
                    "total_records_count": 5,
                    "has_category_filter": True,
                    "target_category": "Dairy",
                    "sources_covered": ["MSME Directory"],
                    "notes": "Verified business coverage",
                },
                data_confidence="high",
                provenance=[],
            )

            response = client.post(
                "/markets/competition",
                json={
                    "village_id": str(v_id),
                    "radius_km": 10.0,
                    "business_category_id": str(cat_id),
                    "category_name": "Dairy",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["competitor_count"] == 2
            assert data["businesses_within_5km"] == 1
            assert data["businesses_within_10km"] == 2
            assert data["target_category"] == "Dairy"

    def test_get_competition_endpoint(self, client):
        v_id = uuid4()

        with patch(
            "app.api.routes.markets.MarketService.analyze_competition_for_location"
        ) as mock_fn:
            mock_fn.return_value = CompetitionAnalysisDetailResponse(
                competitor_count=0,
                competitor_density=0.0,
                businesses_within_5km=0,
                businesses_within_10km=0,
                total_businesses_in_radius=0,
                target_category="Dairy",
                category_distribution={},
                identified_market_gaps=["Zero direct competitors identified"],
                quality_indicator={
                    "completeness_score": 0.5,
                    "confidence_level": "low",
                    "verified_records_count": 0,
                    "total_records_count": 0,
                    "has_category_filter": True,
                    "target_category": "Dairy",
                    "sources_covered": ["Normalized Business Registry"],
                    "notes": "No businesses recorded in database",
                },
                data_confidence="low",
                provenance=[],
            )

            response = client.get(f"/markets/competition/{v_id}?category_name=Dairy")

            assert response.status_code == 200
            data = response.json()
            assert data["competitor_count"] == 0
            assert data["data_confidence"] == "low"

    def test_post_missing_location_fails_validation(self, client):
        """POST /markets/competition with no village_id and no lat/lng returns 422 validation error."""
        response = client.post(
            "/markets/competition",
            json={
                "radius_km": 10.0,
                "category_name": "Dairy",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "Either village_id or both latitude and longitude" in str(data)
