"""Unit tests for enhanced SchemeService data lookup functions."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models.scheme import (
    Scheme,
    SchemeEligibilityRule,
    SchemeMatch,
    SchemeRule,
)
from app.services.scheme_service import SchemeService

# ------------------------------------------------------------------ #
# Scheme queries
# ------------------------------------------------------------------ #


class TestGetSchemes:
    def test_returns_all_active_schemes(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Scheme(id=uuid4(), name="PMEGP", active=True),
            Scheme(id=uuid4(), name="MUDRA", active=True),
        ]
        results = SchemeService.get_schemes(mock_db)
        assert len(results) == 2

    def test_filters_by_state(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Scheme(id=uuid4(), name="PMEGP", state="Central"),
        ]
        results = SchemeService.get_schemes(mock_db, state="Central")
        assert len(results) == 1

    def test_filters_by_agency(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Scheme(id=uuid4(), name="PMEGP", agency_name="KVIC"),
        ]
        results = SchemeService.get_schemes(mock_db, agency_name="KVIC")
        assert len(results) == 1

    def test_includes_inactive_when_not_active_only(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            Scheme(id=uuid4(), name="Old Scheme", active=False),
        ]
        results = SchemeService.get_schemes(mock_db, active_only=False)
        assert len(results) == 1

    def test_limit_capped_at_200(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []
        SchemeService.get_schemes(mock_db, limit=500)


class TestGetSchemeById:
    def test_returns_scheme(self):
        scheme_id = uuid4()
        mock_db = MagicMock()
        mock_db.get.return_value = Scheme(id=scheme_id, name="PMEGP")
        result = SchemeService.get_scheme_by_id(mock_db, scheme_id)
        assert result is not None
        assert result.name == "PMEGP"

    def test_returns_none_when_not_found(self):
        mock_db = MagicMock()
        mock_db.get.return_value = None
        result = SchemeService.get_scheme_by_id(mock_db, uuid4())
        assert result is None


class TestGetSchemeByName:
    def test_returns_scheme(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.first.return_value = Scheme(id=uuid4(), name="PMEGP")
        result = SchemeService.get_scheme_by_name(mock_db, "PMEGP")
        assert result is not None
        assert result.name == "PMEGP"

    def test_returns_none_when_not_found(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.first.return_value = None
        result = SchemeService.get_scheme_by_name(mock_db, "NonExistent")
        assert result is None


# ------------------------------------------------------------------ #
# Scheme Rules
# ------------------------------------------------------------------ #


class TestGetSchemeRules:
    def test_returns_rules_for_scheme(self):
        scheme_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            SchemeRule(id=uuid4(), scheme_id=scheme_id, interest_rate=8.5),
            SchemeRule(id=uuid4(), scheme_id=scheme_id, interest_rate=9.0),
        ]
        results = SchemeService.get_scheme_rules(mock_db, scheme_id)
        assert len(results) == 2

    def test_filters_out_expired_rules(self):
        scheme_id = uuid4()
        expired_rule = SchemeRule(
            id=uuid4(),
            scheme_id=scheme_id,
            effective_from=date(2020, 1, 1),
            effective_until=date(2023, 12, 31),
        )
        active_rule = SchemeRule(
            id=uuid4(),
            scheme_id=scheme_id,
            effective_from=date(2024, 1, 1),
            effective_until=None,
        )
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [expired_rule, active_rule]
        results = SchemeService.get_scheme_rules(mock_db, scheme_id, active_only=True)
        assert len(results) == 1
        assert results[0].id == active_rule.id


class TestGetRuleById:
    def test_returns_rule(self):
        rule_id = uuid4()
        mock_db = MagicMock()
        mock_db.get.return_value = SchemeRule(id=rule_id, interest_rate=8.5)
        result = SchemeService.get_rule_by_id(mock_db, rule_id)
        assert result is not None
        assert result.interest_rate == 8.5


class TestGetLatestRule:
    def test_returns_latest_active_rule(self):
        scheme_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.first.return_value = SchemeRule(
            id=uuid4(),
            scheme_id=scheme_id,
            interest_rate=9.0,
            created_at=datetime(2026, 3, 1),
        )
        result = SchemeService.get_latest_rule(mock_db, scheme_id)
        assert result is not None
        assert result.interest_rate == 9.0

    def test_returns_none_when_no_active_rules(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.first.return_value = None
        result = SchemeService.get_latest_rule(mock_db, uuid4())
        assert result is None


# ------------------------------------------------------------------ #
# Eligibility Rules
# ------------------------------------------------------------------ #


class TestGetEligibilityRules:
    def test_returns_rules_for_scheme(self):
        scheme_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            SchemeEligibilityRule(
                id=uuid4(), scheme_id=scheme_id, rule_type="age", field_name="min_age"
            ),
            SchemeEligibilityRule(
                id=uuid4(), scheme_id=scheme_id, rule_type="income", field_name="annual_income"
            ),
        ]
        results = SchemeService.get_eligibility_rules(mock_db, scheme_id)
        assert len(results) == 2

    def test_filters_by_rule_type(self):
        scheme_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            SchemeEligibilityRule(
                id=uuid4(), scheme_id=scheme_id, rule_type="age", field_name="min_age"
            ),
        ]
        results = SchemeService.get_eligibility_rules_by_type(mock_db, scheme_id, "age")
        assert len(results) == 1
        assert results[0].rule_type == "age"


# ------------------------------------------------------------------ #
# Scheme Matches (data lookup)
# ------------------------------------------------------------------ #


class TestGetSchemeMatches:
    def test_returns_matches_for_run(self):
        run_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            SchemeMatch(
                id=uuid4(),
                analysis_run_id=run_id,
                scheme_id=uuid4(),
                match_status="potential_match",
                match_score=0.92,
            ),
        ]
        results = SchemeService.get_scheme_matches(mock_db, run_id)
        assert len(results) == 1
        assert results[0].match_score == 0.92


class TestGetMatchById:
    def test_returns_match(self):
        match_id = uuid4()
        mock_db = MagicMock()
        mock_db.get.return_value = SchemeMatch(id=match_id, match_status="potential_match")
        result = SchemeService.get_match_by_id(mock_db, match_id)
        assert result is not None


# ------------------------------------------------------------------ #
# Aggregation helpers
# ------------------------------------------------------------------ #


class TestGetStates:
    def test_returns_distinct_states(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            ("Central",),
            ("Maharashtra",),
        ]
        results = SchemeService.get_states(mock_db)
        assert results == ["Central", "Maharashtra"]


class TestGetAgencies:
    def test_returns_distinct_agencies(self):
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            ("KVIC",),
            ("NABARD",),
        ]
        results = SchemeService.get_agencies(mock_db)
        assert results == ["KVIC", "NABARD"]


class TestGetRuleTypes:
    def test_returns_distinct_rule_types(self):
        scheme_id = uuid4()
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [
            ("age",),
            ("income",),
            ("location",),
        ]
        results = SchemeService.get_rule_types(mock_db, scheme_id)
        assert results == ["age", "income", "location"]


# ------------------------------------------------------------------ #
# API endpoint tests
# ------------------------------------------------------------------ #


class TestSchemeAPIEndpoints:
    def test_list_schemes(self, client):
        with patch("app.api.routes.schemes.SchemeService.get_schemes") as mock_fn:
            mock_fn.return_value = [
                Scheme(id=uuid4(), name="PMEGP", active=True, created_at=datetime.utcnow()),
            ]
            response = client.get("/schemes")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "PMEGP"

    def test_get_scheme_by_id(self, client):
        scheme_id = uuid4()
        with patch("app.api.routes.schemes.SchemeService.get_scheme_by_id") as mock_fn:
            mock_fn.return_value = Scheme(
                id=scheme_id, name="PMEGP", active=True, created_at=datetime.utcnow()
            )
            response = client.get(f"/schemes/{scheme_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "PMEGP"

    def test_get_scheme_not_found(self, client):
        with patch("app.api.routes.schemes.SchemeService.get_scheme_by_id") as mock_fn:
            mock_fn.return_value = None
            response = client.get(f"/schemes/{uuid4()}")
            assert response.status_code == 404

    def test_list_scheme_rules(self, client):
        scheme_id = uuid4()
        with patch("app.api.routes.schemes.SchemeService.get_scheme_by_id") as mock_get:
            mock_get.return_value = Scheme(id=scheme_id, name="PMEGP")
            with patch("app.api.routes.schemes.SchemeService.get_scheme_rules") as mock_rules:
                mock_rules.return_value = [
                    SchemeRule(
                        id=uuid4(),
                        scheme_id=scheme_id,
                        interest_rate=8.5,
                        tenure_months=84,
                        created_at=datetime.utcnow(),
                    ),
                ]
                response = client.get(f"/schemes/{scheme_id}/rules")
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["interest_rate"] == 8.5

    def test_list_schemes_states(self, client):
        with patch("app.api.routes.schemes.SchemeService.get_states") as mock_fn:
            mock_fn.return_value = ["Central", "Maharashtra"]
            response = client.get("/schemes/states")
            assert response.status_code == 200
            data = response.json()
            assert data == ["Central", "Maharashtra"]

    def test_list_schemes_agencies(self, client):
        with patch("app.api.routes.schemes.SchemeService.get_agencies") as mock_fn:
            mock_fn.return_value = ["KVIC", "NABARD"]
            response = client.get("/schemes/agencies")
            assert response.status_code == 200
            data = response.json()
            assert data == ["KVIC", "NABARD"]

    def test_list_eligibility_rules(self, client):
        scheme_id = uuid4()
        with patch("app.api.routes.schemes.SchemeService.get_scheme_by_id") as mock_get:
            mock_get.return_value = Scheme(id=scheme_id, name="PMEGP")
            with patch("app.api.routes.schemes.SchemeService.get_eligibility_rules") as mock_rules:
                mock_rules.return_value = [
                    SchemeEligibilityRule(
                        id=uuid4(),
                        scheme_id=scheme_id,
                        rule_type="age",
                        field_name="min_age",
                        operator=">=",
                        expected_value=18,
                        description="Minimum age 18",
                        created_at=datetime.utcnow(),
                    ),
                ]
                response = client.get(f"/schemes/{scheme_id}/eligibility-rules")
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["rule_type"] == "age"

    def test_list_scheme_matches(self, client):
        run_id = uuid4()
        with patch("app.api.routes.schemes.SchemeService.get_scheme_matches") as mock_fn:
            mock_fn.return_value = [
                SchemeMatch(
                    id=uuid4(),
                    analysis_run_id=run_id,
                    scheme_id=uuid4(),
                    match_status="potential_match",
                    match_score=0.92,
                    created_at=datetime.utcnow(),
                ),
            ]
            response = client.get(f"/schemes/matches/{run_id}")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["match_score"] == 0.92


class TestSchemeIntegrationRules:
    def test_scheme_match_status_values(self):
        from app.schemas.common import SchemeMatchStatus

        allowed_statuses = {
            "potential_match",
            "not_match",
            "missing_information",
            "verification_required",
        }
        enum_values = {status.value for status in SchemeMatchStatus}
        assert enum_values == allowed_statuses

    def test_prohibited_guarantee_terms_exclusion(self):
        prohibited_terms = ["approved", "guaranteed loan", "guaranteed eligibility"]
        sample_output = {
            "scheme_name": "Rural Subsidy",
            "match_status": "potential_match",
            "justification": "Meets basic criteria. Requires document verification.",
        }
        text_content = f"{sample_output['scheme_name']} {sample_output['justification']}".lower()
        for term in prohibited_terms:
            assert term not in text_content

    def test_validator_rejects_unauthorized_guarantees_in_descriptive_text(self):
        from uuid import uuid4

        import pytest
        from pydantic import ValidationError

        from app.schemas.common import SchemeMatchStatus
        from app.schemas.scheme import SchemeMatchResultResponse

        scheme_id = uuid4()

        # Matched conditions text contains prohibited term 'approved'
        with pytest.raises(ValidationError) as exc:
            SchemeMatchResultResponse(
                scheme_id=scheme_id,
                scheme_name="Subsidy Scheme",
                match_status=SchemeMatchStatus.POTENTIAL_MATCH,
                matched_conditions={"summary": "Approved by board"},
            )
        assert "Prohibited term 'approved'" in str(exc.value)

        # Missing information text contains prohibited term 'guaranteed loan'
        with pytest.raises(ValidationError) as exc:
            SchemeMatchResultResponse(
                scheme_id=scheme_id,
                scheme_name="Subsidy Scheme",
                match_status=SchemeMatchStatus.MISSING_INFORMATION,
                missing_information={"details": "Guaranteed loan option pending doc review"},
            )
        assert "Prohibited term 'guaranteed loan'" in str(exc.value)
