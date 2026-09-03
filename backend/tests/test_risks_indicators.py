"""Unit and API integration test suite for Phase 8 - Risk Indicators."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.market.risks import assess_market_risks
from app.schemas.market import MarketRiskAssessmentResponse
from app.services.market_service import MarketService


class TestPhase8RiskIndicatorsEngine:
    """Test deterministic risk evaluation engine."""

    def test_high_competitor_density_trigger(self):
        """Triggers high_competitor_density when density exceeds 5.0/km²."""
        res = assess_market_risks(competition_density=6.5)

        risk_types = [r["risk_type"] for r in res["risks"]]
        assert "high_competitor_density" in risk_types

        target_risk = next(r for r in res["risks"] if r["risk_type"] == "high_competitor_density")
        assert target_risk["severity"] == "medium"
        assert target_risk["value"] == 6.5
        assert target_risk["source"] == "Normalized Business Registry"

    def test_high_competitor_density_high_severity(self):
        """Competitor density >= 10.0 results in high severity."""
        res = assess_market_risks(competition_density=12.0)
        target_risk = next(r for r in res["risks"] if r["risk_type"] == "high_competitor_density")
        assert target_risk["severity"] == "high"
        assert target_risk["value"] == 12.0

    def test_seasonal_market_trigger(self):
        """Triggers seasonal_market when is_seasonal is True or volatility is seasonal."""
        res = assess_market_risks(is_seasonal=True, price_volatility_score=0.30)

        risk_types = [r["risk_type"] for r in res["risks"]]
        assert "seasonal_market" in risk_types

        target_risk = next(r for r in res["risks"] if r["risk_type"] == "seasonal_market")
        assert target_risk["severity"] == "medium"
        assert target_risk["value"] == 0.30
        assert target_risk["source"] == "Agmarknet & Crop Seasonality Data"

    def test_low_market_access_trigger_distant(self):
        """Triggers low_market_access when nearest market > 10.0km away."""
        res = assess_market_risks(
            nearby_markets_count=2, nearest_market_distance_km=14.5, radius_km=15.0
        )

        risk_types = [r["risk_type"] for r in res["risks"]]
        assert "low_market_access" in risk_types

        target_risk = next(r for r in res["risks"] if r["risk_type"] == "low_market_access")
        assert target_risk["severity"] == "medium"
        assert target_risk["value"] == 14.5
        assert target_risk["source"] == "Market & Mandi Registry"

    def test_low_market_access_trigger_zero_markets(self):
        """Triggers high severity low_market_access when zero markets exist in radius."""
        res = assess_market_risks(nearby_markets_count=0, radius_km=10.0)

        risk_types = [r["risk_type"] for r in res["risks"]]
        assert "low_market_access" in risk_types

        target_risk = next(r for r in res["risks"] if r["risk_type"] == "low_market_access")
        assert target_risk["severity"] == "high"
        assert target_risk["value"] == 0.0

    def test_single_market_dependency_trigger(self):
        """Triggers single_market_dependency when exactly 1 market exists in radius."""
        res = assess_market_risks(
            nearby_markets_count=1,
            nearest_market_distance_km=3.0,
            single_market_name="APMC Pune Mandi",
            radius_km=10.0,
        )

        risk_types = [r["risk_type"] for r in res["risks"]]
        assert "single_market_dependency" in risk_types
        assert (
            "low_market_access" not in risk_types
        )  # Within 10km, so low_market_access not triggered

        target_risk = next(r for r in res["risks"] if r["risk_type"] == "single_market_dependency")
        assert target_risk["severity"] == "medium"
        assert target_risk["value"] == 1

    def test_single_market_dependency_not_triggered_for_multiple_markets(self):
        """When nearby_markets_count != 1 (e.g. 2), single_market_dependency is NOT triggered and score is NOT incremented."""
        res_two = assess_market_risks(
            nearby_markets_count=2,
            nearest_market_distance_km=3.0,
            facility_counts={"bank": 1, "cold_storage": 1},
            population_reach=5000,
        )

        risk_types = [r["risk_type"] for r in res_two["risks"]]
        assert "single_market_dependency" not in risk_types
        assert res_two["risk_score"] == 0.0
        assert res_two["overall_market_risk_level"] == "low"

    def test_exact_threshold_boundaries(self):
        """Test boundary conditions for competitor density, volatility scores, and population reach."""
        # Competitor density boundary: 5.0 (no risk) vs 5.01 (medium)
        res_comp_exact = assess_market_risks(competition_density=5.0)
        assert "high_competitor_density" not in [r["risk_type"] for r in res_comp_exact["risks"]]

        res_comp_over = assess_market_risks(competition_density=5.01)
        assert "high_competitor_density" in [r["risk_type"] for r in res_comp_over["risks"]]
        assert res_comp_over["risks"][0]["value"] == 5.01

        # Price volatility score boundary: 0.19 (no risk) vs 0.20 (medium) vs 0.35 (high)
        res_vol_sub = assess_market_risks(price_volatility_score=0.19)
        assert "price_volatility" not in [r["risk_type"] for r in res_vol_sub["risks"]]

        res_vol_mid = assess_market_risks(price_volatility_score=0.20)
        risk_vol_mid = next(r for r in res_vol_mid["risks"] if r["risk_type"] == "price_volatility")
        assert risk_vol_mid["severity"] == "medium"
        assert risk_vol_mid["value"] == 0.20

        res_vol_high = assess_market_risks(price_volatility_score=0.35)
        risk_vol_high = next(
            r for r in res_vol_high["risks"] if r["risk_type"] == "price_volatility"
        )
        assert risk_vol_high["severity"] == "high"

        # Population reach boundary: 1000 (no risk) vs 999 (medium)
        res_pop_1000 = assess_market_risks(population_reach=1000)
        assert "low_demographic_demand" not in [r["risk_type"] for r in res_pop_1000["risks"]]

        res_pop_999 = assess_market_risks(population_reach=999)
        risk_pop = next(
            r for r in res_pop_999["risks"] if r["risk_type"] == "low_demographic_demand"
        )
        assert risk_pop["severity"] == "medium"
        assert risk_pop["value"] == 999

    def test_limited_infrastructure_trigger(self):
        """Triggers limited_infrastructure when financial or storage facilities are zero."""
        # Case A: Missing financial infrastructure
        res_fin = assess_market_risks(facility_counts={"warehouse": 2})
        assert "limited_infrastructure" in [r["risk_type"] for r in res_fin["risks"]]
        target_fin = next(r for r in res_fin["risks"] if r["risk_type"] == "limited_infrastructure")
        assert target_fin["severity"] == "medium"
        assert target_fin["value"] == "financial:0,logistics:2"

        # Case B: Missing both financial and logistics infrastructure
        res_both = assess_market_risks(facility_counts={})
        target_both = next(
            r for r in res_both["risks"] if r["risk_type"] == "limited_infrastructure"
        )
        assert target_both["severity"] == "high"
        assert target_both["value"] == "financial:0,logistics:0"

    def test_price_volatility_trigger(self):
        """Triggers price_volatility when price volatility is high."""
        res = assess_market_risks(price_volatility="high", price_volatility_score=0.28)

        risk_types = [r["risk_type"] for r in res["risks"]]
        assert "price_volatility" in risk_types

        target_risk = next(r for r in res["risks"] if r["risk_type"] == "price_volatility")
        assert target_risk["severity"] == "medium"
        assert target_risk["source"] == "Agmarknet Price Records"
        assert target_risk["value"] == 0.28

    def test_no_plausible_risks_when_data_is_healthy(self):
        """Do not create risks merely because they sound plausible when data is healthy."""
        res = assess_market_risks(
            competition_density=2.0,  # Below 5.0
            facility_counts={
                "bank": 1,
                "atm": 2,
                "cold_storage": 1,
                "warehouse": 3,
            },  # Sufficient infra
            price_volatility="low",  # Low volatility
            population_reach=5000,  # Healthy population
            nearby_markets_count=3,  # Multiple markets
            nearest_market_distance_km=2.5,  # Close market access
            is_seasonal=False,
        )

        assert res["overall_market_risk_level"] == "low"
        assert res["risk_score"] == 0.0
        assert len(res["risks"]) == 0
        assert len(res["identified_risk_flags"]) == 0

    def test_deterministic_risk_sorting(self):
        """Risks list is deterministically sorted alphabetically by risk_type key."""
        res = assess_market_risks(
            competition_density=6.0,
            facility_counts={},  # limited_infrastructure
            price_volatility="high",  # price_volatility
            population_reach=500,  # low_demographic_demand
        )
        risk_types = [r["risk_type"] for r in res["risks"]]
        assert len(risk_types) >= 3
        assert risk_types == sorted(risk_types)


class TestMarketServiceRiskOrchestration:
    """Test MarketService.assess_risks_for_location."""

    def test_assess_risks_for_location_service(self):
        mock_db = MagicMock()
        mock_db.get.return_value = None

        with (
            patch("app.services.market_service.find_nearby_businesses", return_value=[]),
            patch("app.services.market_service.find_nearby_facilities", return_value=[]),
            patch("app.services.market_service.find_nearby_markets", return_value=[]),
            patch("app.services.market_service.find_nearby_villages", return_value=[]),
        ):
            res = MarketService.assess_risks_for_location(
                db=mock_db, lat=18.52, lng=73.85, radius_km=10.0, is_seasonal=True
            )

            assert isinstance(res, MarketRiskAssessmentResponse)
            assert res.overall_market_risk_level in ("medium", "high")
            assert (
                len(res.risks) >= 2
            )  # low_market_access (0 markets) & limited_infrastructure & seasonal


class TestRiskAPIEndpoints:
    """Test API endpoints for Phase 8 Risk Indicators."""

    def test_post_risks_endpoint(self, client):
        v_id = uuid4()

        with patch("app.api.routes.markets.MarketService.assess_risks_for_location") as mock_fn:
            mock_fn.return_value = MarketRiskAssessmentResponse(
                overall_market_risk_level="high",
                risk_score=7.5,
                risks=[
                    {
                        "risk_type": "high_competitor_density",
                        "severity": "high",
                        "evidence": "Competitor density of 11.20 competitors/km² exceeds threshold.",
                        "source": "Normalized Business Registry",
                    },
                    {
                        "risk_type": "limited_infrastructure",
                        "severity": "medium",
                        "evidence": "Financial infrastructure gap: Zero banks or ATMs.",
                        "source": "Facilities & Infrastructure Registry",
                    },
                ],
                identified_risk_flags=[
                    "High Competitor Density (HIGH): Competitor density of 11.20 competitors/km²",
                    "Limited Infrastructure (MEDIUM): Financial infrastructure gap",
                ],
                provenance=[],
            )

            response = client.post(
                "/markets/risks",
                json={
                    "village_id": str(v_id),
                    "radius_km": 10.0,
                    "is_seasonal": True,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["overall_market_risk_level"] == "high"
            assert len(data["risks"]) == 2
            assert data["risks"][0]["risk_type"] == "high_competitor_density"

    def test_get_risks_endpoint(self, client):
        v_id = uuid4()

        with patch("app.api.routes.markets.MarketService.assess_risks_for_location") as mock_fn:
            mock_fn.return_value = MarketRiskAssessmentResponse(
                overall_market_risk_level="low",
                risk_score=0.0,
                risks=[],
                identified_risk_flags=[],
                provenance=[],
            )

            response = client.get(f"/markets/risks/{v_id}?radius_km=10.0")

            assert response.status_code == 200
            data = response.json()
            assert data["overall_market_risk_level"] == "low"
            assert data["risk_score"] == 0.0
