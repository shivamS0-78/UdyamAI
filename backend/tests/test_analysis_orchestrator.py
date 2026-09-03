from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.business import BusinessCategory
from app.models.location import District, Taluka, Village
from app.models.user import Profile
from app.schemas.feasibility import AnalysisRunCreate
from app.schemas.finance import FinanceCalculateResponse
from app.services.analysis_orchestrator import AnalysisOrchestrator


class TestAnalysisOrchestrator:
    def test_run_analysis_pipeline_missing_location_fails(self):
        mock_db = MagicMock()
        payload = AnalysisRunCreate(available_capital=50000.0)

        with pytest.raises(HTTPException) as exc:
            AnalysisOrchestrator.run_analysis_pipeline(mock_db, payload)
        assert exc.value.status_code == 400
        assert "Location identifier" in str(exc.value.detail)

    @patch("app.services.analysis_orchestrator.advisor.generate_advice")
    @patch("app.services.analysis_orchestrator.FeasibilityService.calculate_feasibility")
    @patch("app.services.analysis_orchestrator.SchemeService.get_schemes")
    @patch("app.services.analysis_orchestrator.SchemeService.get_scheme_matches")
    @patch("app.services.analysis_orchestrator.MarketService.analyze_competition_for_location")
    @patch("app.services.analysis_orchestrator.MarketService.analyze_village_market")
    @patch("app.services.analysis_orchestrator.FinanceService.calculate_finance")
    @patch("app.services.analysis_orchestrator.AnalysisService.verify_business_category")
    @patch("app.services.analysis_orchestrator.AnalysisService.verify_location")
    def test_run_analysis_pipeline_full_workflow_success(
        self,
        mock_verify_loc,
        mock_verify_cat,
        mock_calc_fin,
        mock_mkt_loc,
        mock_comp_loc,
        mock_scheme_matches,
        mock_schemes,
        mock_feasibility,
        mock_ai_advisor,
    ):
        loc_id = uuid4()
        cat_id = uuid4()
        user_id = uuid4()

        mock_verify_loc.return_value = loc_id
        mock_verify_cat.return_value = cat_id

        # Mock DB entities
        mock_db = MagicMock()
        mock_profile = Profile(id=user_id, email="user@test.com")
        mock_district = District(id=uuid4(), name="Pune")
        mock_taluka = Taluka(id=uuid4(), name="Khed Taluka", district_id=mock_district.id)
        mock_village = Village(
            id=loc_id,
            name="Khed",
            latitude=18.52,
            longitude=73.85,
            taluka_id=mock_taluka.id,
            district_id=mock_district.id,
        )
        mock_category = BusinessCategory(id=cat_id, name="Dairy Farming")

        def db_get_side_effect(model_cls, entity_id):
            if model_cls == Profile:
                return mock_profile
            elif model_cls == Village:
                return mock_village
            elif model_cls == Taluka:
                return mock_taluka
            elif model_cls == District:
                return mock_district
            elif model_cls == BusinessCategory:
                return mock_category
            return None

        mock_db.get.side_effect = db_get_side_effect
        mock_db.exec.return_value.first.return_value = mock_category

        # Mock Finance
        mock_fin_resp = FinanceCalculateResponse(
            status="success",
            available_capital=50000.0,
            required_contribution=50000.0,
            shortfall=0.0,
            desired_project_cost=200000.0,
            feasible_project_cost=200000.0,
            potential_loan=150000.0,
        )
        mock_calc_fin.return_value = mock_fin_resp

        # Mock Market
        mock_mkt_res = MagicMock()
        mock_mkt_res.market_size.total_population_reach = 10000
        mock_mkt_res.market_size.household_reach = 2000
        mock_mkt_res.market_size.estimated_target_customers = 500
        mock_mkt_res.demand_score = 0.8
        mock_mkt_res.demand_level = "High"
        mock_mkt_res.demand_growth_rate = 0.05
        mock_mkt_res.purchasing_power.estimated_monthly_expenditure = 15000.0
        mock_mkt_res.purchasing_power.average_household_income = 25000.0
        mock_mkt_res.purchasing_power.purchasing_power_index = 0.75
        mock_mkt_res.pricing.average_market_price = 60.0
        mock_mkt_res.pricing.price_range_min = 50.0
        mock_mkt_res.pricing.price_range_max = 70.0
        mock_mkt_res.infrastructure.infrastructure_score = 0.85
        mock_mkt_res.risks.overall_market_risk_score = 0.3
        mock_mkt_res.risks.risk_level = "low"
        mock_mkt_res.overall_market_score = 0.82

        mock_location_market_res = MagicMock()
        mock_location_market_res.radius_results = [mock_mkt_res]
        mock_mkt_loc.return_value = mock_location_market_res

        # Mock Competition
        mock_comp_res = MagicMock()
        mock_comp_res.total_competitors_count = 5
        mock_comp_res.direct_competitors_count = 2
        mock_comp_res.indirect_competitors_count = 3
        mock_comp_res.competition_density = 0.5
        mock_comp_res.market_saturation_level = "medium"
        mock_comp_res.threat_level = "low"
        mock_comp_res.nearest_competitor_distance_km = 1.2
        mock_comp_loc.return_value = mock_comp_res

        # Mock Scheme matches
        mock_scheme_matches.return_value = []
        mock_schemes.return_value = []

        # Mock Feasibility score result
        mock_feas_res = MagicMock()
        mock_feas_res.overall_score = 0.84
        mock_feas_res.market_score = 0.82
        mock_feas_res.financial_score = 0.88
        mock_feas_res.competition_score = 0.78
        mock_feas_res.infrastructure_score = 0.85
        mock_feas_res.risk_score = 0.3
        mock_feas_res.swot.strengths = ["Strong demand"]
        mock_feas_res.swot.weaknesses = ["Limited capital"]
        mock_feas_res.swot.opportunities = ["State subsidy"]
        mock_feas_res.swot.threats = ["Local competition"]
        mock_feasibility.return_value = mock_feas_res

        # Mock AI Advisor
        mock_advice = MagicMock()
        mock_advice.recommendation = "Highly Feasible"
        mock_advice.confidence = "high"
        mock_advice.summary = "Solid micro-dairy viability"
        mock_advice.reasoning = ["Good demand"]
        mock_advice.market_advice = ["Target local retail"]
        mock_advice.financial_advice = ["Apply for PMEGP"]
        mock_advice.risks = ["Feed price variance"]
        mock_advice.next_steps = ["Submit application"]
        mock_advice.model_name = "gemini-3.6-flash"
        mock_advice.prompt_version = "v1"
        mock_ai_advisor.return_value = mock_advice

        # Execute
        payload = AnalysisRunCreate(
            user_id=user_id,
            location_id=loc_id,
            business_category_id=cat_id,
            available_capital=50000.0,
            desired_project_cost=200000.0,
        )
        db_run = AnalysisOrchestrator.run_analysis_pipeline(mock_db, payload)

        assert db_run is not None
        assert db_run.status == "completed"
        assert db_run.completed_at is not None
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

        # Assert FinanceService.calculate_finance call signature shape
        mock_calc_fin.assert_called_once()
        fin_call_args, fin_call_kwargs = mock_calc_fin.call_args
        assert fin_call_kwargs.get("session") == mock_db

    @patch("app.services.analysis_orchestrator.AnalysisService.verify_business_category")
    @patch("app.services.analysis_orchestrator.AnalysisService.verify_location")
    def test_run_analysis_pipeline_rollback_on_failure(self, mock_verify_loc, mock_verify_cat):
        loc_id = uuid4()
        user_id = uuid4()
        mock_verify_loc.return_value = loc_id
        mock_verify_cat.return_value = None

        mock_db = MagicMock()
        mock_profile = Profile(id=user_id, email="user@test.com")

        # Village get returns None to trigger 404 inside pipeline loop
        def db_get_side_effect(model_cls, entity_id):
            if model_cls == Profile:
                return mock_profile
            return None

        mock_db.get.side_effect = db_get_side_effect

        payload = AnalysisRunCreate(
            user_id=user_id,
            location_id=loc_id,
            available_capital=50000.0,
        )

        with pytest.raises(HTTPException) as exc:
            AnalysisOrchestrator.run_analysis_pipeline(mock_db, payload)

        assert exc.value.status_code == 404
        assert mock_db.rollback.called
