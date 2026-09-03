from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import (
    AnalysisRunCreate,
    BeneficiaryCategory,
    FinanceCalculateRequest,
    LocationQuery,
    ReportCreateRequest,
    SchemeMatchRequest,
    SchemeMatchResultResponse,
    SchemeMatchStatus,
    SupportedLanguage,
)


def test_analysis_run_create_valid():
    """Verify valid AnalysisRunCreate payload with village_id, business_category_id, capital."""
    data = {
        "village_id": "LGD_556123",
        "business_category_id": "dairy",
        "available_capital": 100000,
        "language": "hi",
    }
    schema = AnalysisRunCreate(**data)
    assert schema.village_id == "LGD_556123"
    assert schema.business_category_id == "dairy"
    assert schema.available_capital == 100000.0
    assert schema.language == SupportedLanguage.HI


def test_analysis_run_create_negative_capital_fails():
    """Verify available_capital cannot be negative."""
    with pytest.raises(ValidationError) as exc:
        AnalysisRunCreate(available_capital=-500)
    assert "available_capital" in str(exc.value)


def test_analysis_run_create_exceeds_max_limit_fails():
    """Verify available_capital exceeds max sensible limit (10 Cr)."""
    with pytest.raises(ValidationError) as exc:
        AnalysisRunCreate(available_capital=200_000_000.0)
    assert "available_capital" in str(exc.value)


def test_finance_calculate_request_validation():
    """Verify required fields and range validations for finance calculation request."""
    # Valid payload
    valid_data = {
        "desired_project_cost": 200000.0,
        "available_capital": 50000.0,
        "loan_percent": 75.0,
        "interest_rate": 8.5,
        "tenure_months": 60,
        "moratorium_months": 6,
    }
    req = FinanceCalculateRequest(**valid_data)
    assert req.desired_project_cost == 200000.0
    assert req.tenure_months == 60

    # Negative project cost should fail (gt=0 requirement)
    with pytest.raises(ValidationError):
        FinanceCalculateRequest(**{**valid_data, "desired_project_cost": 0})

    # Negative interest rate should fail
    with pytest.raises(ValidationError):
        FinanceCalculateRequest(**{**valid_data, "interest_rate": -1.0})

    # Tenure exceeding 360 months should fail
    with pytest.raises(ValidationError):
        FinanceCalculateRequest(**{**valid_data, "tenure_months": 400})


def test_scheme_match_request_category_and_age_validation():
    """Verify beneficiary category enum and age limits."""
    req = SchemeMatchRequest(
        applicant_age=25,
        category=BeneficiaryCategory.OBC,
        annual_income=150000.0,
    )
    assert req.category == BeneficiaryCategory.OBC
    assert req.applicant_age == 25

    # Invalid age under 18
    with pytest.raises(ValidationError):
        SchemeMatchRequest(applicant_age=15)

    # Invalid category string
    with pytest.raises(ValidationError):
        SchemeMatchRequest(category="INVALID_CATEGORY")


def test_supported_languages_validation():
    """Verify supported language enum values ('en', 'hi', 'mr')."""
    req_en = ReportCreateRequest(
        analysis_run_id=uuid4(),
        user_id=uuid4(),
        language=SupportedLanguage.EN,
    )
    assert req_en.language == "en"

    req_mr = ReportCreateRequest(
        analysis_run_id=uuid4(),
        user_id=uuid4(),
        language="mr",  # String coercion to enum
    )
    assert req_mr.language == SupportedLanguage.MR

    # Unsupported language code raises ValidationError
    with pytest.raises(ValidationError):
        ReportCreateRequest(
            analysis_run_id=uuid4(),
            user_id=uuid4(),
            language="fr",
        )


def test_location_query_bounds():
    """Verify pagination limit and search string constraints."""
    query = LocationQuery(search="Pune", limit=100, offset=0)
    assert query.limit == 100

    # Limit > 500 fails
    with pytest.raises(ValidationError):
        LocationQuery(limit=1000)

    # Negative offset fails
    with pytest.raises(ValidationError):
        LocationQuery(offset=-10)


def test_scheme_match_status_values_and_prohibited_guarantees():
    """Verify SchemeMatchStatus values and prohibit unauthoritative guarantee terms."""
    assert SchemeMatchStatus.POTENTIAL_MATCH == "potential_match"
    assert SchemeMatchStatus.NOT_MATCH == "not_match"
    assert SchemeMatchStatus.MISSING_INFORMATION == "missing_information"
    assert SchemeMatchStatus.VERIFICATION_REQUIRED == "verification_required"

    # Valid response
    resp = SchemeMatchResultResponse(
        scheme_id=uuid4(),
        scheme_name="PMEGP",
        match_status=SchemeMatchStatus.POTENTIAL_MATCH,
        verification_required=True,
    )
    assert resp.match_status == "potential_match"


def test_scheme_match_status_legacy_enum_compatibility():
    """Verify legacy enum values deserialize gracefully to canonical SchemeMatchStatus."""
    # "not_matched" maps to NOT_MATCH ("not_match")
    status_1 = SchemeMatchStatus("not_matched")
    assert status_1 == SchemeMatchStatus.NOT_MATCH
    assert status_1.value == "not_match"

    # "insufficient_information" maps to MISSING_INFORMATION ("missing_information")
    status_2 = SchemeMatchStatus("insufficient_information")
    assert status_2 == SchemeMatchStatus.MISSING_INFORMATION
    assert status_2.value == "missing_information"


def test_scheme_match_result_prohibited_terms_negative_cases():
    """Verify that prohibited terms in text fields fail validation unless authoritative approval exists."""
    scheme_id = uuid4()

    # Prohibited term 'approved' in matched_conditions text fails
    with pytest.raises(ValidationError) as exc_info:
        SchemeMatchResultResponse(
            scheme_id=scheme_id,
            scheme_name="PMEGP",
            match_status=SchemeMatchStatus.POTENTIAL_MATCH,
            matched_conditions={"status": "Approved for grant"},
        )
    assert "Prohibited term 'approved'" in str(exc_info.value)

    # Prohibited term 'guaranteed loan' in scheme_name fails
    with pytest.raises(ValidationError) as exc_info:
        SchemeMatchResultResponse(
            scheme_id=scheme_id,
            scheme_name="Guaranteed Loan Scheme",
            match_status=SchemeMatchStatus.POTENTIAL_MATCH,
        )
    assert "Prohibited term 'guaranteed loan'" in str(exc_info.value)

    # Prohibited term 'guaranteed eligibility' in missing_information text fails
    with pytest.raises(ValidationError) as exc_info:
        SchemeMatchResultResponse(
            scheme_id=scheme_id,
            scheme_name="PMEGP",
            match_status=SchemeMatchStatus.MISSING_INFORMATION,
            missing_information={"notes": "Provides guaranteed eligibility upon submission"},
        )
    assert "Prohibited term 'guaranteed eligibility'" in str(exc_info.value)

    # Authoritative approval allows approved status
    approved_resp = SchemeMatchResultResponse(
        scheme_id=scheme_id,
        scheme_name="PMEGP",
        match_status=SchemeMatchStatus.POTENTIAL_MATCH,
        matched_conditions={"status": "Approved by bank"},
        authoritative_approval_status="SANCTIONED",
    )
    assert approved_resp.authoritative_approval_status == "SANCTIONED"


def test_scheme_match_financial_upper_bounds():
    """Verify that financial amounts exceeding upper limits fail validation."""
    scheme_id = uuid4()

    # Loan amount exceeding 10 Cr (100,000,000) fails
    with pytest.raises(ValidationError) as exc_info:
        SchemeMatchResultResponse(
            scheme_id=scheme_id,
            scheme_name="PMEGP",
            match_status=SchemeMatchStatus.POTENTIAL_MATCH,
            estimated_loan_amount=200_000_000.0,
        )
    assert "estimated_loan_amount" in str(exc_info.value)


def test_schema_field_naming_discrepancies_normalization():
    """Verify bidirectional compatibility between old and new property names across schemas."""
    from datetime import datetime, timezone

    from app.schemas.ai import CompetitionContext, MarketContext
    from app.schemas.feasibility import SWOTIndicators
    from app.schemas.market import MarketAnalysisResponse

    # 1. MarketContext initialized with total_population_reach and household_reach
    mkt = MarketContext(
        total_population_reach=25000,
        household_reach=5500,
        estimated_target_customers=3200,
    )
    assert mkt.population_estimate == 25000
    assert mkt.total_population_reach == 25000
    assert mkt.household_estimate == 5500
    assert mkt.household_reach == 5500
    assert mkt.market_reach_estimate == 3200
    assert mkt.estimated_target_customers == 3200

    # 2. MarketAnalysisResponse initialized with aliases
    mkt_resp = MarketAnalysisResponse(
        id=uuid4(),
        analysis_run_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        total_population_reach=18000,
        estimated_household_reach=4000,
    )
    assert mkt_resp.population_estimate == 18000
    assert mkt_resp.household_estimate == 4000

    # 3. CompetitionContext initialized with total_competitors_count
    comp = CompetitionContext(
        total_competitors_count=12,
        total_businesses_in_radius=30,
        target_category="Dairy Farming",
    )
    assert comp.competitor_count == 12
    assert comp.total_competitors_count == 12
    assert comp.total_businesses_in_radius == 30
    assert comp.target_category == "Dairy Farming"

    # 4. SWOTIndicators initialized with strengths/weaknesses
    swot = SWOTIndicators(
        strengths=["High Demand"],
        weaknesses=["Limited Transport"],
        opportunities=["Govt Subsidies"],
        threats=["Drought"],
    )
    assert swot.strength_indicators == ["High Demand"]
    assert swot.strengths == ["High Demand"]
    assert swot.weakness_indicators == ["Limited Transport"]
    assert swot.weaknesses == ["Limited Transport"]
    assert swot.opportunity_indicators == ["Govt Subsidies"]
    assert swot.opportunities == ["Govt Subsidies"]
    assert swot.threat_indicators == ["Drought"]
    assert swot.threats == ["Drought"]


def test_feasibility_score_bounds():
    """Verify that feasibility scores enforce explicit lower and upper bounds (ge=0, le=100)."""
    from app.schemas.feasibility import FeasibilityAnalysisResponse, FeasibilityScoreResult

    # Valid scores within 0-100
    res = FeasibilityScoreResult(
        market_score=85.0,
        financial_score=70.0,
        competition_score=60.0,
        infrastructure_score=75.0,
        risk_score=80.0,
        overall_score=74.5,
    )
    assert res.overall_score == 74.5

    # Out of bounds: negative score fails
    with pytest.raises(ValidationError):
        FeasibilityScoreResult(
            market_score=-5.0,
            financial_score=70.0,
            competition_score=60.0,
            infrastructure_score=75.0,
            risk_score=80.0,
            overall_score=74.5,
        )

    # Out of bounds: score > 100 fails
    with pytest.raises(ValidationError):
        FeasibilityScoreResult(
            market_score=85.0,
            financial_score=105.0,
            competition_score=60.0,
            infrastructure_score=75.0,
            risk_score=80.0,
            overall_score=74.5,
        )

    with pytest.raises(ValidationError):
        FeasibilityScoreResult(
            market_score=85.0,
            financial_score=70.0,
            competition_score=60.0,
            infrastructure_score=75.0,
            risk_score=80.0,
            overall_score=150.0,
        )

    # FeasibilityAnalysisResponse bounds
    with pytest.raises(ValidationError):
        FeasibilityAnalysisResponse(
            id=uuid4(),
            analysis_run_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            overall_score=101.0,
        )

    with pytest.raises(ValidationError):
        FeasibilityAnalysisResponse(
            id=uuid4(),
            analysis_run_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            market_score=-1.0,
        )
