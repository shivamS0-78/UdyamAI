"""Full Vertical Slice Integration Test for UdyamAI.

Validates the complete end-to-end multi-step analysis lifecycle:
POST /analysis
       ↓
AnalysisRun created (running)
       ↓
Location validated (real Maharashtra hierarchy: District -> Taluka -> Village)
       ↓
Business validated (BusinessCategory)
       ↓
Finance calculated (FinancialAnalysis, RepaymentSchedule)
       ↓
Market calculated (MarketAnalysis, Demographics & Demand)
       ↓
Competition calculated (CompetitorAnalysis, Density & Threats)
       ↓
Scheme result obtained (SchemeMatch, PMEGP / Mudra)
       ↓
Feasibility calculated (FeasibilityAnalysis, SWOT & Score)
       ↓
AnalysisContext created (Validated typed context)
       ↓
AI service called (Structured Advice)
       ↓
Report stored (Report entity, completed status)
       ↓
GET /analysis/{id} & GET /analysis/{id}/consolidated
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.models.analysis import AIAnalysis, AnalysisRun, FeasibilityAnalysis
from app.models.business import BusinessCategory
from app.models.finance import FinancialAnalysis, RepaymentSchedule
from app.models.location import District, GramPanchayat, Population, Taluka, Village
from app.models.market import CompetitorAnalysis, MarketAnalysis
from app.models.report import Report
from app.models.scheme import Scheme, SchemeMatch
from app.models.user import Profile
from app.schemas.ai import AIAdvice, AnalysisContext
from app.schemas.common import SchemeMatchStatus
from app.schemas.feasibility import AnalysisRunCreate
from app.schemas.finance import FinanceCalculateResponse
from app.services.analysis_orchestrator import AnalysisOrchestrator


def test_full_vertical_slice_orchestration_maharashtra():
    """Verify complete vertical slice workflow using realistic Maharashtra location data."""
    # 1. Setup real Maharashtra reference data hierarchy in mock DB
    user_id = uuid4()
    pune_district_id = uuid4()
    haveli_taluka_id = uuid4()
    wagholi_gp_id = uuid4()
    wagholi_village_id = uuid4()
    dairy_category_id = uuid4()
    pmegp_scheme_id = uuid4()

    mock_profile = Profile(id=user_id, email="entrepreneur@udyamai.in")
    mock_district = District(
        id=pune_district_id,
        name="Pune",
        state="Maharashtra",
        lgd_code="500",
    )
    mock_taluka = Taluka(
        id=haveli_taluka_id,
        name="Haveli",
        district_id=pune_district_id,
        lgd_code="5001",
    )
    mock_gp = GramPanchayat(
        id=wagholi_gp_id,
        name="Wagholi Gram Panchayat",
        taluka_id=haveli_taluka_id,
        district_id=pune_district_id,
        lgd_code="500101",
    )
    mock_village = Village(
        id=wagholi_village_id,
        name="Wagholi",
        district_id=pune_district_id,
        taluka_id=haveli_taluka_id,
        gram_panchayat_id=wagholi_gp_id,
        lgd_code="50010101",
        latitude=18.5793,
        longitude=73.9814,
    )
    mock_population = Population(
        id=uuid4(),
        location_id=wagholi_village_id,
        year=2024,
        population_total=25000,
        households=5500,
        working_population=12000,
    )
    mock_category = BusinessCategory(
        id=dairy_category_id,
        name="Dairy Processing & Products",
        slug="dairy-processing",
        description="Micro-dairy, milk collection, chilling, and pasteurization unit",
    )
    mock_scheme = Scheme(
        id=pmegp_scheme_id,
        name="Prime Minister Employment Generation Programme (PMEGP)",
        slug="pmegp",
        nodal_agency="KVIC / MSME",
        active=True,
    )

    # In-memory storage to simulate DB persistence across steps
    db_store: dict[type, dict] = {
        Profile: {user_id: mock_profile},
        District: {pune_district_id: mock_district},
        Taluka: {haveli_taluka_id: mock_taluka},
        GramPanchayat: {wagholi_gp_id: mock_gp},
        Village: {wagholi_village_id: mock_village},
        Population: {mock_population.id: mock_population},
        BusinessCategory: {dairy_category_id: mock_category},
        Scheme: {pmegp_scheme_id: mock_scheme},
        AnalysisRun: {},
        FinancialAnalysis: {},
        RepaymentSchedule: {},
        MarketAnalysis: {},
        CompetitorAnalysis: {},
        SchemeMatch: {},
        FeasibilityAnalysis: {},
        AIAnalysis: {},
        Report: {},
    }

    mock_db = MagicMock()

    def mock_db_get(model_cls, entity_id):
        return db_store.get(model_cls, {}).get(entity_id)

    def mock_db_add(entity):
        cls = type(entity)
        if cls not in db_store:
            db_store[cls] = {}
        e_id = getattr(entity, "id", None) or uuid4()
        entity.id = e_id
        db_store[cls][e_id] = entity

    mock_db.get.side_effect = mock_db_get
    mock_db.add.side_effect = mock_db_add
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    # Configure subservice responses
    mock_fin_resp = FinanceCalculateResponse(
        status="success",
        available_capital=100000.0,
        required_contribution=100000.0,
        shortfall=0.0,
        desired_project_cost=500000.0,
        feasible_project_cost=500000.0,
        potential_loan=375000.0,
        subsidy_amount=125000.0,
    )

    # Mock Market Response
    mock_mkt_res = MagicMock()
    mock_mkt_res.market_size.total_population_reach = 25000
    mock_mkt_res.market_size.household_reach = 5500
    mock_mkt_res.market_size.estimated_target_customers = 1200
    mock_mkt_res.demand_score = 0.85
    mock_mkt_res.demand_level = "High"
    mock_mkt_res.demand_growth_rate = 0.08
    mock_mkt_res.purchasing_power.estimated_monthly_expenditure = 22000.0
    mock_mkt_res.purchasing_power.average_household_income = 38000.0
    mock_mkt_res.purchasing_power.purchasing_power_index = 0.82
    mock_mkt_res.pricing.average_market_price = 65.0
    mock_mkt_res.pricing.price_range_min = 55.0
    mock_mkt_res.pricing.price_range_max = 75.0
    mock_mkt_res.infrastructure.infrastructure_score = 0.88
    mock_mkt_res.risks.overall_market_risk_score = 0.25
    mock_mkt_res.risks.risk_level = "low"
    mock_mkt_res.overall_market_score = 0.86

    mock_mkt_location_resp = MagicMock()
    mock_mkt_location_resp.radius_results = [mock_mkt_res]

    # Mock Competition Response
    mock_comp_resp = MagicMock()
    mock_comp_resp.total_competitors_count = 4
    mock_comp_resp.direct_competitors_count = 2
    mock_comp_resp.indirect_competitors_count = 2
    mock_comp_resp.competition_density = 0.42
    mock_comp_resp.market_saturation_level = "low"
    mock_comp_resp.threat_level = "low"
    mock_comp_resp.nearest_competitor_distance_km = 2.4
    mock_comp_resp.data_confidence = "high"
    mock_comp_resp.data_available = True

    mock_advice_resp = AIAdvice(
        summary="Excellent feasibility for micro-dairy processing unit in Wagholi, Pune district.",
        recommendation="Highly Recommended",
        confidence="high",
        reasoning=[
            "High rural-urban transition demand for fresh pasteurized milk and curd",
            "Available capital of ₹1,00,000 matches 20% margin requirement for ₹5,00,000 unit",
            "Substantial 25,000 population reach within 10km radius with strong purchasing power",
        ],
        market_advice=[
            "Establish direct milk collection centers with local dairy farmers in Haveli taluka",
            "Supply packaged milk and paneer to Wagholi and Nagar Road retail outlets",
        ],
        financial_advice=[
            "Apply for PMEGP rural subsidy (up to 35% margin money for rural micro-enterprises)",
            "Structure loan repayment with a 6-month moratorium period during machinery installation",
        ],
        risks=[
            "Milk price seasonal fluctuations during summer months",
            "Cold chain electricity reliability requirement",
        ],
        next_steps=[
            "Prepare detailed project report (DPR) for ₹5,00,000 dairy unit",
            "Submit PMEGP online application through KVIC portal choosing Haveli DIC office",
            "Obtain FSSAI basic registration for milk processing",
        ],
        model_name="gemini-3.6-flash",
        prompt_version="v1.0",
    )

    captured_analysis_context = None

    def fake_generate_advice(
        analysis_context: AnalysisContext, language: str = "en", db=None, **kwargs
    ):
        nonlocal captured_analysis_context
        captured_analysis_context = analysis_context
        return mock_advice_resp

    mock_scheme_match = SchemeMatch(
        id=uuid4(),
        analysis_run_id=uuid4(),
        scheme_id=pmegp_scheme_id,
        match_status=SchemeMatchStatus.POTENTIAL_MATCH,
        match_score=0.9,
        scheme=mock_scheme,
    )

    def fake_match_schemes(*args, **kwargs):
        mock_db_add(mock_scheme_match)
        return [mock_scheme_match]

    with (
        patch(
            "app.services.analysis_orchestrator.AnalysisService.verify_location",
            return_value=wagholi_village_id,
        ),
        patch(
            "app.services.analysis_orchestrator.AnalysisService.verify_business_category",
            return_value=dairy_category_id,
        ),
        patch(
            "app.services.analysis_orchestrator.match_schemes_for_analysis",
            side_effect=fake_match_schemes,
        ),
        patch(
            "app.services.analysis_orchestrator.FinanceService.calculate_finance",
            return_value=mock_fin_resp,
        ),
        patch(
            "app.services.analysis_orchestrator.MarketService.analyze_village_market",
            return_value=mock_mkt_location_resp,
        ),
        patch(
            "app.services.analysis_orchestrator.MarketService.analyze_competition_for_location",
            return_value=mock_comp_resp,
        ),
        patch(
            "app.services.analysis_orchestrator.SchemeService.get_scheme_matches",
            return_value=[mock_scheme_match],
        ),
        patch(
            "app.services.analysis_orchestrator.SchemeService.get_schemes",
            return_value=[mock_scheme],
        ),
        patch(
            "app.services.analysis_orchestrator.SchemeService.get_scheme_by_id",
            return_value=mock_scheme,
        ),
        patch(
            "app.services.analysis_orchestrator.advisor.generate_advice",
            side_effect=fake_generate_advice,
        ),
    ):
        # -------------------------------------------------------------
        # Step 1 -> Step 12: Execute Orchestration Pipeline
        # -------------------------------------------------------------
        run_request = AnalysisRunCreate(
            user_id=user_id,
            location_id=wagholi_village_id,
            business_category_id=dairy_category_id,
            available_capital=100000.0,
            desired_project_cost=500000.0,
            language="en",
        )

        completed_run = AnalysisOrchestrator.run_analysis_pipeline(mock_db, run_request)

        # -------------------------------------------------------------
        # Verify Pipeline Completion & Artifacts
        # -------------------------------------------------------------
        assert completed_run is not None
        assert completed_run.id is not None
        assert completed_run.status == "completed"
        assert completed_run.completed_at is not None
        assert completed_run.location_id == wagholi_village_id
        assert completed_run.business_category_id == dairy_category_id

        # Verify AnalysisContext was constructed and delivered to AI
        assert captured_analysis_context is not None
        assert captured_analysis_context.location.village.name == "Wagholi"
        assert captured_analysis_context.location.district.name == "Pune"
        assert captured_analysis_context.location.taluka.name == "Haveli"
        assert captured_analysis_context.business.category.name == "Dairy Processing & Products"
        assert captured_analysis_context.financial.available_capital == 100000.0
        assert captured_analysis_context.financial.potential_loan == 375000.0
        assert captured_analysis_context.market.total_population_reach == 25000
        assert captured_analysis_context.competition.total_competitors_count == 4
        assert len(captured_analysis_context.schemes) >= 1
        assert captured_analysis_context.schemes[0].scheme.name == mock_scheme.name
        assert captured_analysis_context.feasibility.overall_score > 0
        assert len(captured_analysis_context.risks) >= 1

        # Verify DB Persistence for each required component entity
        assert len(db_store[AnalysisRun]) >= 1
        assert len(db_store[FeasibilityAnalysis]) >= 1
        assert len(db_store[AIAnalysis]) >= 1
        assert len(db_store[MarketAnalysis]) >= 1
        assert len(db_store[CompetitorAnalysis]) >= 1
        assert len(db_store[SchemeMatch]) >= 1
        assert len(db_store[Report]) >= 1

        persisted_report = list(db_store[Report].values())[0]
        assert "Dairy Processing & Products" in persisted_report.title
        assert "Wagholi" in persisted_report.title
        assert persisted_report.report_data["recommendation"] == "Highly Recommended"


def test_full_vertical_slice_api_routes(client: TestClient):
    """Verify HTTP route integration: POST /api/v1/analysis -> GET /api/v1/analysis/{id} -> GET /api/v1/analysis/{id}/consolidated."""
    user_id = uuid4()
    loc_id = uuid4()
    cat_id = uuid4()
    analysis_id = uuid4()

    mock_completed_run = AnalysisRun(
        id=analysis_id,
        user_id=user_id,
        location_id=loc_id,
        business_category_id=cat_id,
        available_capital=100000.0,
        status="completed",
    )

    from app.schemas.feasibility import ConsolidatedAnalysisResponse

    mock_consolidated = ConsolidatedAnalysisResponse(
        analysis_id=analysis_id,
        status="completed",
        location={
            "village_id": str(loc_id),
            "village_name": "Wagholi",
            "taluka_name": "Haveli",
            "district_name": "Pune",
            "state": "Maharashtra",
        },
        business={
            "category_id": str(cat_id),
            "category_name": "Dairy Processing & Products",
        },
        financial={
            "available_capital": 100000.0,
            "desired_project_cost": 500000.0,
            "potential_loan": 375000.0,
            "subsidy_amount": 125000.0,
        },
        market={
            "radius_km": 10.0,
            "population_estimate": 25000,
            "household_estimate": 5500,
            "demand_level": "High",
        },
        competition={
            "total_competitors": 4,
            "competition_density": 0.42,
            "threat_level": "low",
        },
        schemes=[
            {
                "scheme_name": "PMEGP",
                "match_score": 0.85,
            }
        ],
        feasibility={
            "overall_score": 85.0,
            "market_score": 85.0,
            "financial_score": 90.0,
            "data_confidence": "high",
            "competition_data_available": True,
            "market_data_available": True,
        },
        risks=[
            {
                "risk_type": "market_risk",
                "level": "low",
            }
        ],
        ai_advice={
            "recommendation": "Highly Recommended",
            "summary": "Excellent feasibility for micro-dairy processing unit in Wagholi, Pune.",
            "next_steps": ["Prepare DPR", "Submit PMEGP application"],
        },
    )

    # 1. Test POST /api/v1/analysis
    post_payload = {
        "user_id": str(user_id),
        "location_id": str(loc_id),
        "business_category_id": str(cat_id),
        "available_capital": 100000.0,
        "desired_project_cost": 500000.0,
        "language": "en",
    }

    with (
        patch(
            "app.api.routes.analysis.AnalysisOrchestrator.run_analysis_pipeline",
            return_value=mock_completed_run,
        ),
        patch(
            "app.api.routes.analysis.AnalysisService.get_analysis_run",
            return_value=mock_completed_run,
        ),
        patch(
            "app.api.routes.analysis.AnalysisService.get_consolidated_analysis",
            return_value=mock_consolidated,
        ),
    ):
        post_resp = client.post("/api/v1/analysis", json=post_payload)
        assert post_resp.status_code == 201
        post_data = post_resp.json()
        assert post_data["analysis_id"] == str(analysis_id)
        assert post_data["status"] == "completed"

        # 2. Test GET /api/v1/analysis/{id}
        get_resp = client.get(f"/api/v1/analysis/{analysis_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["analysis_id"] == str(analysis_id)
        assert get_data["available_capital"] == 100000.0

        # 3. Test GET /api/v1/analysis/{id}/consolidated
        cons_resp = client.get(f"/api/v1/analysis/{analysis_id}/consolidated")
        assert cons_resp.status_code == 200
        cons_data = cons_resp.json()
        assert cons_data["analysis_id"] == str(analysis_id)
        assert cons_data["status"] == "completed"
        assert cons_data["location"]["village_name"] == "Wagholi"
        assert cons_data["location"]["district_name"] == "Pune"
        assert cons_data["location"]["state"] == "Maharashtra"
        assert cons_data["business"]["category_name"] == "Dairy Processing & Products"
        assert cons_data["financial"]["potential_loan"] == 375000.0
        assert cons_data["ai_advice"]["recommendation"] == "Highly Recommended"
