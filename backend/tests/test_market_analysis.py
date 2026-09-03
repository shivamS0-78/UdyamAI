"""Unit and integration tests for Phase 6 - Market Analysis."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.market.competition import analyze_competition
from app.market.demand import calculate_demand_indicators
from app.market.infrastructure import analyze_relevant_infrastructure
from app.market.market_size import (
    calculate_population_and_household_reach,
    estimate_target_customers,
)
from app.market.pricing import analyze_market_pricing
from app.models.location import District, GramPanchayat, Population, Taluka, Village
from app.models.market import Market, MarketPrice
from app.schemas.market import LocationMarketAnalysisResponse
from app.services.market_service import MarketService

# ------------------------------------------------------------------ #
# Test Fixtures (Model Factories)
# ------------------------------------------------------------------ #


@pytest.fixture(name="sample_village")
def sample_village_fixture():
    district = District(id=uuid4(), name="Pune District", state="Maharashtra")
    taluka = Taluka(id=uuid4(), name="Haveli", district_id=district.id, district=district)
    gp = GramPanchayat(id=uuid4(), name="Wagholi GP", taluka_id=taluka.id, district_id=district.id)

    village = Village(
        id=uuid4(),
        name="Wagholi",
        district_id=district.id,
        taluka_id=taluka.id,
        gram_panchayat_id=gp.id,
        district=district,
        taluka=taluka,
        latitude=18.5793,
        longitude=73.9822,
    )
    return village


# ------------------------------------------------------------------ #
# Unit Tests: Calculation Engine
# ------------------------------------------------------------------ #


class TestMarketSizeAndTargeting:
    def test_calculate_population_and_household_reach(self):
        v1_id = str(uuid4())
        v2_id = str(uuid4())

        villages = [
            {"id": v1_id, "name": "Village A"},
            {"id": v2_id, "name": "Village B"},
        ]

        pop_data = {
            v1_id: {
                "population_total": 2500,
                "households": 500,
                "working_population": 1200,
                "source": "Census 2021",
                "source_url": "https://censusindia.gov.in",
                "data_year": 2021,
            },
            v2_id: {
                "population_total": 1500,
                "households": 300,
                "working_population": 700,
                "source": "Census 2021",
                "source_url": "https://censusindia.gov.in",
                "data_year": 2021,
            },
        }

        res = calculate_population_and_household_reach(villages, pop_data)

        assert res["estimated_population_reach"] == 4000
        assert res["estimated_household_reach"] == 800
        assert res["estimated_working_population"] == 1900
        assert len(res["provenance"]) >= 1
        assert res["provenance"][0]["dataset_name"] == "Census Population & Households"

    def test_population_is_not_customer_count(self):
        pop_reach = 10000
        hh_reach = 2000

        target_customers = estimate_target_customers(pop_reach, hh_reach, conversion_rate=0.05)

        assert target_customers == 500
        assert target_customers < pop_reach

    def test_custom_conversion_rate(self):
        pop_reach = 10000
        hh_reach = 2000

        target_customers = estimate_target_customers(pop_reach, hh_reach, conversion_rate=0.15)
        assert target_customers == 1500

    def test_household_targeting_customers(self):
        pop_reach = 10000
        hh_reach = 2000

        target_customers = estimate_target_customers(
            pop_reach, hh_reach, conversion_rate=0.10, household_targeting=True
        )
        assert target_customers == 200


class TestInfrastructureAndCompetition:
    def test_analyze_relevant_infrastructure(self):
        facilities = [
            {
                "id": uuid4(),
                "name": "Bank of India",
                "facility_type": "bank",
                "distance_meters": 1200,
                "capacity": None,
                "source": "RBI",
            },
            {
                "id": uuid4(),
                "name": "Cold Storage Unit",
                "facility_type": "cold_storage",
                "distance_meters": 4500,
                "capacity": 500,
                "source": "NHB",
            },
        ]

        res = analyze_relevant_infrastructure(facilities)

        assert res["total_facilities"] == 2
        assert res["facility_counts_by_type"]["bank"] == 1
        assert res["facility_counts_by_type"]["cold_storage"] == 1
        assert len(res["facility_summaries"]) == 2
        assert res["facility_summaries"][0]["distance_km"] == 1.2

    def test_analyze_competition_and_gaps(self):
        cat_id = str(uuid4())
        businesses = [
            {"id": uuid4(), "business_category_id": cat_id, "source": "MSME Directory"},
        ]

        res = analyze_competition(businesses, radius_km=5.0, target_category_id=cat_id)

        assert res["total_businesses_in_radius"] == 1
        assert res["direct_competitor_count"] == 1
        assert res["competition_density_per_km2"] < 0.5
        assert len(res["identified_market_gaps"]) >= 1


class TestPricingAndDemand:
    def test_analyze_market_pricing(self):
        markets = [{"id": uuid4(), "name": "Dist Mandi"}]
        prices = [
            {
                "market_id": markets[0]["id"],
                "commodity": "Onion",
                "modal_price": 2200.0,
                "source": "Agmarknet",
            },
            {
                "market_id": markets[0]["id"],
                "commodity": "Tomato",
                "modal_price": 1800.0,
                "source": "Agmarknet",
            },
        ]

        res = analyze_market_pricing(markets, prices)

        assert res["average_modal_price"] == 2000.0
        assert res["min_modal_price"] == 1800.0
        assert res["max_modal_price"] == 2200.0
        assert res["commodity_coverage_count"] == 2
        assert res["price_volatility"] in ("low", "medium", "high")

    def test_analyze_market_pricing_with_string_dates(self):
        markets = [{"id": str(uuid4()), "name": "Dist Mandi"}]
        prices = [
            {
                "market_id": markets[0]["id"],
                "commodity": "Onion",
                "modal_price": 2200.0,
                "recorded_date": "2026-08-31T00:00:00",
                "source": "Agmarknet",
            },
            {
                "market_id": markets[0]["id"],
                "commodity": "Tomato",
                "modal_price": 1800.0,
                "recorded_date": None,
                "source": "Agmarknet",
            },
        ]

        res = analyze_market_pricing(markets, prices)

        assert res["average_modal_price"] == 2000.0
        assert res["commodity_coverage_count"] == 2
        prov_years = [p["data_year"] for p in res["provenance"]]
        assert 2026 in prov_years

    def test_calculate_demand_indicators(self):
        res = calculate_demand_indicators(
            population_reach=5000,
            household_reach=1000,
            working_population=2500,
            economic_records=[],
            agriculture_records=[],
            radius_km=5.0,
        )

        assert res["working_population_ratio"] == 0.5
        assert res["average_household_size"] == 5.0
        assert "demand_score" in res


# ------------------------------------------------------------------ #
# Integration Tests: DB & Service Orchestrator
# ------------------------------------------------------------------ #


class TestMarketServiceOrchestrator:
    def test_analyze_village_market_with_mocked_db_and_models(self, sample_village: Village):
        mock_db = MagicMock()
        mock_db.get.return_value = sample_village

        pop_rec = Population(
            location_id=sample_village.id,
            year=2021,
            population_total=5000,
            households=1000,
            working_population=2500,
            source="Census 2021",
        )
        mkt_rec = Market(
            id=uuid4(),
            name="Wagholi Mandi",
            market_type="mandi",
            location_id=sample_village.id,
            latitude=18.58,
            longitude=73.98,
            source="Agmarknet",
        )
        price_rec = MarketPrice(
            id=uuid4(),
            market_id=mkt_rec.id,
            location_id=sample_village.id,
            commodity="Wheat",
            modal_price=2400.0,
            source="Agmarknet",
        )

        # Mock db.exec results for batch queries
        def exec_side_effect(stmt):
            mock_result = MagicMock()
            stmt_str = str(stmt)
            if "population" in stmt_str.lower():
                mock_result.all.return_value = [pop_rec]
            elif "market_prices" in stmt_str.lower():
                mock_result.all.return_value = [price_rec]
            else:
                mock_result.all.return_value = []
            return mock_result

        mock_db.exec.side_effect = exec_side_effect

        with (
            patch("app.services.market_service.find_nearby_villages") as mock_vils,
            patch("app.services.market_service.find_nearby_markets") as mock_mkts,
            patch("app.services.market_service.find_nearby_facilities") as mock_facs,
            patch("app.services.market_service.find_nearby_businesses") as mock_biz,
        ):
            mock_vils.return_value = [
                {"id": sample_village.id, "name": sample_village.name, "distance_meters": 0.0}
            ]
            mock_mkts.return_value = [
                {
                    "id": mkt_rec.id,
                    "name": mkt_rec.name,
                    "market_type": mkt_rec.market_type,
                    "distance_meters": 500.0,
                }
            ]
            mock_facs.return_value = []
            mock_biz.return_value = []

            res = MarketService.analyze_village_market(
                mock_db,
                village_id=sample_village.id,
                radii_km=[5.0, 10.0],
                target_conversion_rate=0.08,
            )

            assert isinstance(res, LocationMarketAnalysisResponse)
            assert res.village_id == sample_village.id
            assert res.village_name == "Wagholi"
            assert len(res.radius_analyses) == 2
            assert res.radius_analyses[0].estimated_population_reach == 5000
            assert res.radius_analyses[0].estimated_target_customers == 400

            # Verify provenance deduplication
            dataset_names = [p.dataset_name for p in res.provenance_summary]
            assert len(dataset_names) == len(set(dataset_names))

    def test_analyze_village_market_geo_lookup_resilience(self, sample_village: Village):
        mock_db = MagicMock()
        mock_db.get.return_value = sample_village
        mock_db.exec.return_value.all.return_value = []

        with patch(
            "app.services.market_service.find_nearby_villages",
            side_effect=Exception("Spatial PostGIS Error"),
        ):
            # Should not crash; gracefully catches spatial errors and returns analysis
            res = MarketService.analyze_village_market(mock_db, village_id=sample_village.id)
            assert res is not None
            assert res.village_id == sample_village.id

    def test_analyze_village_market_not_found(self):
        mock_db = MagicMock()
        mock_db.get.return_value = None

        with pytest.raises(Exception) as exc_info:
            MarketService.analyze_village_market(mock_db, village_id=uuid4())

        assert "not found" in str(exc_info.value)

    def test_analyze_village_market_mixed_id_types_and_string_dates(self, sample_village: Village):
        mock_db = MagicMock()
        mock_db.get.return_value = sample_village

        mkt_id = uuid4()
        pop_rec = Population(
            location_id=sample_village.id,
            year=2021,
            population_total=3000,
            households=600,
            working_population=1500,
            source="Census 2021",
        )
        price_rec = MarketPrice(
            id=uuid4(),
            market_id=mkt_id,
            location_id=sample_village.id,
            commodity="Rice",
            modal_price=3000.0,
            recorded_date="2026-08-30",
            source="Agmarknet",
        )

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            stmt_str = str(stmt)
            if "population" in stmt_str.lower():
                mock_result.all.return_value = [pop_rec]
            elif "market_prices" in stmt_str.lower():
                mock_result.all.return_value = [price_rec]
            else:
                mock_result.all.return_value = []
            return mock_result

        mock_db.exec.side_effect = exec_side_effect

        with (
            patch("app.services.market_service.find_nearby_villages") as mock_vils,
            patch("app.services.market_service.find_nearby_markets") as mock_mkts,
            patch("app.services.market_service.find_nearby_facilities") as mock_facs,
            patch("app.services.market_service.find_nearby_businesses") as mock_biz,
        ):
            # Return string IDs from geo lookups
            mock_vils.return_value = [
                {
                    "id": str(sample_village.id),
                    "name": sample_village.name,
                    "distance_meters": 100.0,
                }
            ]
            mock_mkts.return_value = [
                {
                    "id": str(mkt_id),
                    "name": "Mandi",
                    "market_type": "mandi",
                    "distance_meters": 500.0,
                }
            ]
            mock_facs.return_value = []
            mock_biz.return_value = []

            res = MarketService.analyze_village_market(
                mock_db,
                village_id=sample_village.id,
                radii_km=[5.0],
            )

            assert res.village_id == sample_village.id
            assert res.radius_analyses[0].estimated_population_reach == 3000
            assert len(res.radius_analyses[0].nearby_markets) == 1
            assert res.radius_analyses[0].nearby_markets[0].modal_price_sample == 3000.0

    def test_analyze_village_market_db_commit_error(self, sample_village: Village):
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.get.return_value = sample_village
        mock_db.exec.return_value.all.return_value = []
        mock_db.commit.side_effect = Exception("DB Connection Lost")

        with (
            patch("app.services.market_service.find_nearby_villages", return_value=[]),
            patch("app.services.market_service.find_nearby_markets", return_value=[]),
            patch("app.services.market_service.find_nearby_facilities", return_value=[]),
            patch("app.services.market_service.find_nearby_businesses", return_value=[]),
        ):
            run_id = uuid4()
            with pytest.raises(HTTPException) as exc_info:
                MarketService.analyze_village_market(
                    mock_db,
                    village_id=sample_village.id,
                    analysis_run_id=run_id,
                )

            assert exc_info.value.status_code == 500
            assert "Database commit error" in exc_info.value.detail
            mock_db.rollback.assert_called_once()


# ------------------------------------------------------------------ #
# API Endpoint Tests
# ------------------------------------------------------------------ #


class TestMarketAnalysisAPI:
    def test_post_analyze_endpoint(self, client):
        village_id = uuid4()
        with patch("app.api.routes.markets.MarketService.analyze_village_market") as mock_fn:
            mock_fn.return_value = LocationMarketAnalysisResponse(
                village_id=village_id,
                village_name="Test Village",
                radii_km=[5.0, 10.0],
                radius_analyses=[],
                provenance_summary=[],
            )

            response = client.post(
                "/markets/analyze",
                json={
                    "village_id": str(village_id),
                    "radii_km": [5.0, 10.0],
                    "target_conversion_rate": 0.08,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["village_name"] == "Test Village"
            assert data["radii_km"] == [5.0, 10.0]

    def test_get_analyze_endpoint(self, client):
        village_id = uuid4()
        with patch("app.api.routes.markets.MarketService.analyze_village_market") as mock_fn:
            mock_fn.return_value = LocationMarketAnalysisResponse(
                village_id=village_id,
                village_name="Test Village",
                radii_km=[5.0, 10.0],
                radius_analyses=[],
                provenance_summary=[],
            )

            response = client.get(
                f"/markets/analyze/{village_id}?radii=5.0&radii=10.0&target_conversion_rate=0.08"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["village_id"] == str(village_id)
