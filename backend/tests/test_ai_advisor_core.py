import json

import pytest

from app.ai import context_builder, guardrails, prompts, recommendation


def test_context_builder_builds_safe_prompt_payload():
    analysis_context = {
        "location": {"village": {"name": "Khed"}, "district": {"name": "Pune"}},
        "business": {"category": {"name": "Dairy Farming"}},
        "financial": {
            "available_capital": 50000,
            "required_contribution": 60000,
            "shortfall": 10000,
            "desired_project_cost": 200000,
            "potential_loan": 150000,
        },
        "market": {
            "overall_market_score": 82,
            "demand_level": "High",
            "estimated_target_customers": 500,
        },
        "competition": {
            "total_competitors_count": 6,
            "threat_level": "low",
        },
        "schemes": [
            {"scheme": {"name": "PM FME"}, "match_status": "potential_match", "match_score": 0.8}
        ],
        "feasibility": {
            "overall_score": 76,
            "market_score": 80,
            "financial_score": 74,
            "risk_score": 35,
            "recommendation": "Moderately feasible",
        },
        "risks": [{"title": "Feed cost risk"}],
        "language": "en",
    }

    payload = context_builder.build(analysis_context)

    assert payload["business"]["category_name"] == "Dairy Farming"
    assert payload["financial"]["shortfall"] == 10000
    assert payload["feasibility"]["overall_score"] == 76
    assert "verified" in payload["summary"]["source_note"].lower()


def test_advisor_prompt_mentions_verified_data_and_json_output():
    payload = {
        "business": {"category_name": "Dairy Farming"},
        "financial": {"shortfall": 0},
        "feasibility": {"overall_score": 82},
    }

    prompt = prompts.build_advisor_prompt(payload, language="en")

    assert "verified backend data" in prompt.lower()
    assert "json" in prompt.lower()
    assert "dairy farming" in prompt.lower()


def test_guardrails_validate_keeps_valid_output_and_rejects_invented_numbers():
    good_output = {
        "summary": "Based on verified backend data, the business is feasible.",
        "recommendation": "Proceed with the plan using current risk controls.",
        "reasoning": ["Scores and funding values are based on backend analysis."],
        "financial_advice": ["Use the verified contribution requirement."],
        "market_advice": ["Use the verified market conditions."],
        "competition_advice": ["Account for local competition."],
        "scheme_advice": ["Review the matched schemes."],
        "risks": ["Cost volatility remains a key risk."],
        "next_steps": ["Validate demand before launch."],
        "disclaimers": ["This advice is based on available backend data."],
        "sources": [],
        "confidence": "medium",
        "model_name": "demo-model",
        "prompt_version": "v1",
        "language": "en",
    }

    cleaned = guardrails.validate(good_output, {"financial": {"shortfall": 0}})
    assert cleaned["summary"] == good_output["summary"]

    bad_output = dict(good_output)
    bad_output["summary"] = "The subsidy will cover 90% of the project cost."

    try:
        guardrails.validate(bad_output, {"financial": {"shortfall": 0}})
        raise AssertionError("Expected guardrail validation to reject invented subsidy claims")
    except ValueError:
        pass


def test_recommendation_explain_uses_verified_feasibility_scores():
    feasibility = {
        "overall_score": 76,
        "market_score": 80,
        "financial_score": 74,
        "risk_score": 35,
        "recommendation": "Moderately feasible",
    }

    explanation = recommendation.explain(feasibility)

    assert "76" in explanation or "Moderately feasible" in explanation
    assert "market" in explanation.lower()
    assert "financial" in explanation.lower()


def test_guardrails_string_coercion_and_metadata_defaults():
    raw_output = {
        "summary": "Feasible project.",
        "recommendation": "Proceed with caution.",
        "reasoning": "Single reasoning string provided by LLM.",
        "financial_advice": "Maintain minimum capital.",
    }

    cleaned = guardrails.validate(raw_output, {})

    assert isinstance(cleaned["reasoning"], list)
    assert cleaned["reasoning"] == ["Single reasoning string provided by LLM."]
    assert isinstance(cleaned["financial_advice"], list)
    assert cleaned["financial_advice"] == ["Maintain minimum capital."]
    assert cleaned["language"] == "en"
    assert cleaned["confidence"] == "unverified"
    assert cleaned["model_name"] == "unknown-model"
    assert cleaned["prompt_version"] == "v1"


def test_guardrails_defensive_sources_parsing():
    raw_output = {
        "summary": "Valid summary.",
        "recommendation": "Valid recommendation.",
        "sources": [
            {"claim": "PMFME subsidy", "source_type": "scheme_rule", "reference_id": "pmfme_doc"},
            "invalid_string_source",
            {"claim": "Another claim"},
        ],
    }

    cleaned = guardrails.validate(raw_output, {})

    assert len(cleaned["sources"]) >= 1
    assert cleaned["sources"][0]["claim"] == "PMFME subsidy"
    assert cleaned["sources"][0]["reference_id"] == "pmfme_doc"


def test_context_builder_raw_context_options():
    analysis_context = {"business": {"category": {"name": "Bakery"}}}

    default_payload = context_builder.build(analysis_context)
    assert default_payload["raw_context"] is None

    payload_with_raw = context_builder.build(
        analysis_context, include_raw_context=True, max_raw_context_length=20
    )
    assert payload_with_raw["raw_context"] is not None
    assert len(payload_with_raw["raw_context"]) <= 35


def test_guardrails_source_backed_claim_allowed():
    raw_output = {
        "summary": "The scheme offers 35% credit-linked capital subsidy.",
        "recommendation": "Apply for PMFME.",
        "sources": [
            {
                "claim": "35% credit-linked capital subsidy under PMFME",
                "source_type": "scheme_rule",
                "reference_id": "pmfme_v1",
            }
        ],
    }

    cleaned = guardrails.validate(raw_output, {})
    assert cleaned["summary"] == raw_output["summary"]


def test_recommendation_explain_handles_normalized_scale():
    fractional_feasibility = {
        "overall_score": 0.85,
        "market_score": 0.90,
        "financial_score": 0.80,
        "recommendation": "Highly feasible",
    }

    explanation = recommendation.explain(fractional_feasibility)
    assert "85" in explanation
    assert "reasonably feasible" in explanation.lower()


def test_generate_advice_calls_retrieve_evidence_when_db_provided(monkeypatch):
    from uuid import uuid4

    from app.ai import advisor
    from app.schemas.rag import EvidenceItem, RAGQueryResponse, SourceMetadata

    called = {}

    def mock_retrieve_evidence(db, query, scheme_id=None, language=None, **kwargs):
        called["query"] = query
        called["scheme_id"] = scheme_id
        called["language"] = language
        return RAGQueryResponse(
            status="success",
            evidence=[
                EvidenceItem(
                    chunk_id=uuid4(),
                    text="PMFME provides 35% capital subsidy up to 10 lakhs.",
                    score=0.92,
                    source=SourceMetadata(
                        document_id=uuid4(),
                        title="PMFME Guidelines",
                        page_number=4,
                        section_title="Subsidy Rules",
                        source_name="Ministry of Food Processing",
                    ),
                )
            ],
        )

    def mock_llm_generate(prompt):
        assert "35% capital subsidy" in prompt or "PMFME Guidelines" in prompt
        return '{"summary": "Feasible under PMFME.", "recommendation": "Apply online.", "reasoning": ["Verified by guidelines."]}'

    monkeypatch.setattr("app.rag.retriever.retrieve_evidence", mock_retrieve_evidence)
    monkeypatch.setattr("app.ai.llm.generate", mock_llm_generate)

    mock_db = object()
    analysis_context = {
        "location": {"district": {"name": "Pune"}},
        "business": {"category": {"name": "Food Processing"}},
        "schemes": [{"scheme": {"id": uuid4(), "name": "PMFME"}}],
        "feasibility": {"overall_score": 80},
    }

    advice = advisor.generate_advice(analysis_context, language="en", db=mock_db)

    assert called["language"] == "en"
    assert "Food Processing" in called["query"]
    assert advice.rag_status == "success"
    assert len(advice.evidence) == 1
    assert advice.evidence[0].source.title == "PMFME Guidelines"


def test_generate_advice_conflicting_sources_warning(monkeypatch):
    from uuid import uuid4

    from app.ai import advisor
    from app.schemas.rag import EvidenceItem, RAGQueryResponse, SourceMetadata

    def mock_retrieve_evidence(db, query, **kwargs):
        return RAGQueryResponse(
            status="conflicting_sources",
            evidence=[
                EvidenceItem(
                    chunk_id=uuid4(),
                    text="Subsidy limit is 35%.",
                    score=0.88,
                    source=SourceMetadata(
                        document_id=uuid4(),
                        title="Doc A",
                        source_name="Ministry A",
                    ),
                ),
                EvidenceItem(
                    chunk_id=uuid4(),
                    text="Subsidy limit is 50%.",
                    score=0.85,
                    source=SourceMetadata(
                        document_id=uuid4(),
                        title="Doc B",
                        source_name="Ministry B",
                    ),
                ),
            ],
        )

    def mock_llm_generate(prompt):
        assert "CONFLICTING SOURCES DETECTED" in prompt
        return '{"summary": "Conflicting guidance.", "recommendation": "Verify with department.", "reasoning": ["Docs disagree."]}'

    monkeypatch.setattr("app.rag.retriever.retrieve_evidence", mock_retrieve_evidence)
    monkeypatch.setattr("app.ai.llm.generate", mock_llm_generate)

    mock_db = object()
    advice = advisor.generate_advice({"feasibility": {"overall_score": 75}}, db=mock_db)

    assert advice.rag_status == "conflicting_sources"
    assert "WARNING" in advice.recommendation.upper()
    assert "conflicting" in advice.recommendation.lower()


def test_generate_advice_rag_failure_resilience(monkeypatch):
    from app.ai import advisor

    def mock_retrieve_evidence(db, query, **kwargs):
        raise RuntimeError("Vector database connection timed out")

    def mock_llm_generate(prompt):
        assert "NO RELEVANT EVIDENCE FOUND" in prompt
        return '{"summary": "Backend fallback advice.", "recommendation": "Proceed using backend data."}'

    monkeypatch.setattr("app.rag.retriever.retrieve_evidence", mock_retrieve_evidence)
    monkeypatch.setattr("app.ai.llm.generate", mock_llm_generate)

    mock_db = object()
    advice = advisor.generate_advice({"feasibility": {"overall_score": 70}}, db=mock_db)

    assert advice.rag_status == "no_relevant_evidence"
    assert advice.summary == "Backend fallback advice."


def test_generate_advice_backward_compatibility_without_db(monkeypatch):
    from app.ai import advisor

    def mock_llm_generate(prompt):
        return '{"summary": "Standard advice.", "recommendation": "Standard recommendation."}'

    monkeypatch.setattr("app.ai.llm.generate", mock_llm_generate)

    advice = advisor.generate_advice({"feasibility": {"overall_score": 70}})

    assert advice.rag_status == "no_relevant_evidence"
    assert advice.summary == "Standard advice."
    assert advice.evidence == []


def test_rag_status_enum_values():
    from app.schemas.rag import RAGStatus

    assert RAGStatus.SUCCESS == "success"
    assert RAGStatus.NO_RELEVANT_EVIDENCE == "no_relevant_evidence"
    assert RAGStatus.CONFLICTING_SOURCES == "conflicting_sources"
    assert RAGStatus.EMBEDDING_GENERATION_FAILED == "embedding_generation_failed"
    assert issubclass(RAGStatus, str)


def test_generate_advice_malformed_json_fallback(monkeypatch):
    from app.ai import advisor

    def mock_llm_generate(prompt):
        return "This is malformed non-JSON text from the model."

    monkeypatch.setattr("app.ai.llm.generate", mock_llm_generate)

    advice = advisor.generate_advice({"feasibility": {"overall_score": 75}})
    assert advice is not None
    assert (
        "malformed" in advice.summary
        or "unavailable" in advice.summary.lower()
        or "verified" in advice.recommendation.lower()
    )


def test_generate_advice_specific_exception_handling(monkeypatch):
    from app.ai import advisor

    def mock_llm_generate_json_error(prompt):
        raise json.JSONDecodeError("Expecting value", "doc", 0)

    monkeypatch.setattr("app.ai.llm.generate", mock_llm_generate_json_error)

    advice = advisor.generate_advice({"feasibility": {"overall_score": 75}})
    assert advice is not None
    assert "verified backend analysis" in advice.summary.lower()
    assert advice.model_name == "backend-grounded-v1"


def test_generate_advice_reraises_import_error(monkeypatch):
    from app.ai import advisor

    def mock_llm_generate_import_error(prompt):
        raise ImportError("Missing required package")

    monkeypatch.setattr("app.ai.llm.generate", mock_llm_generate_import_error)

    with pytest.raises(ImportError, match="Missing required package"):
        advisor.generate_advice({"feasibility": {"overall_score": 75}})
