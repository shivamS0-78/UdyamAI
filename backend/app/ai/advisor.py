"""AI Advisor orchestrator.

Pipeline: AnalysisContext -> context_builder -> prompts + llm -> guardrails
          -> recommendation -> AIAdvice

The advisor is intentionally resilient: if the provider, prompt-building, or
validation step fails, it returns a degraded AI response instead of crashing
the rest of the backend analysis flow.
"""

import json
import logging
from typing import Any

from app.ai import context_builder, guardrails, llm, prompts, recommendation
from app.schemas.ai import AIAdvice, AnalysisContext
from app.schemas.rag import RAGQueryResponse, RAGStatus

logger = logging.getLogger(__name__)


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if item is not None and str(item).strip()]


def _backend_grounded_advice(prepared_context: dict[str, Any], language: str = "en") -> AIAdvice:
    """Build advisory guidance from verified backend analysis when the LLM is unavailable."""
    normalized_language = language if language in {"en", "hi", "mr"} else "en"
    location = prepared_context.get("location", {}) or {}
    business = prepared_context.get("business", {}) or {}
    feasibility = prepared_context.get("feasibility", {}) or {}
    schemes = prepared_context.get("schemes", []) or []
    rag_status = prepared_context.get("rag_status") or RAGStatus.NO_RELEVANT_EVIDENCE.value

    village = location.get("village_name") or "the target village"
    district = location.get("district_name") or ""
    category = business.get("category_name") or "the proposed enterprise"
    location_label = f"{village}, {district}" if district and district != "N/A" else village

    overall = feasibility.get("overall_score")
    market = feasibility.get("market_score")
    financial = feasibility.get("financial_score")

    summary_parts = [f"Based on verified backend analysis for a {category} in {location_label}."]
    if overall is not None:
        summary_parts.append(f"The overall feasibility index is {float(overall):.0f}/100.")
    if market is not None:
        summary_parts.append(f"Market demand scores {float(market):.0f}/100.")
    if financial is not None:
        summary_parts.append(f"Financial viability scores {float(financial):.0f}/100.")
    if rag_status == RAGStatus.SUCCESS.value:
        summary_parts.append(
            "Relevant government scheme documents were retrieved for cross-reference."
        )
    else:
        summary_parts.append(
            "Recommendations below are derived from verified market, financial, competition, and scheme-matching outputs."
        )

    strengths = _as_string_list(feasibility.get("strengths"))
    weaknesses = _as_string_list(feasibility.get("weaknesses"))
    opportunities = _as_string_list(feasibility.get("opportunities"))
    threats = _as_string_list(feasibility.get("threats"))

    scheme_advice = [
        f"{scheme.get('name', 'Matched scheme')}: status {scheme.get('match_status', 'review')} "
        f"(match score {scheme.get('match_score', 'N/A')})."
        for scheme in schemes
        if isinstance(scheme, dict)
    ]
    if not scheme_advice:
        scheme_advice = [
            "Review matched government subsidy and credit schemes in the dashboard before finalizing capital structure."
        ]

    financial_ctx = prepared_context.get("financial", {}) or {}
    financial_advice = []
    if financial_ctx.get("desired_project_cost") is not None:
        financial_advice.append(
            f"Target project cost: INR {float(financial_ctx['desired_project_cost']):,.0f}."
        )
    if financial_ctx.get("available_capital") is not None:
        financial_advice.append(
            f"Available capital: INR {float(financial_ctx['available_capital']):,.0f}."
        )
    if financial_ctx.get("potential_loan") is not None:
        financial_advice.append(
            f"Estimated loan requirement: INR {float(financial_ctx['potential_loan']):,.0f}."
        )
    if not financial_advice:
        financial_advice = [
            "Use the backend financial summary and EMI projections as the primary decision signal."
        ]

    competition_ctx = prepared_context.get("competition", {}) or {}
    competition_advice = []
    if competition_ctx.get("competition_density") is not None:
        competition_advice.append(
            f"Competition density in the local radius is {float(competition_ctx['competition_density']):.2f}."
        )
    if competition_ctx.get("threat_level"):
        competition_advice.append(
            f"Competitive threat level is assessed as {competition_ctx['threat_level']}."
        )
    if not competition_advice:
        competition_advice = [
            "Monitor nearby competitors and differentiate on service quality and local reach."
        ]

    market_ctx = prepared_context.get("market", {}) or {}
    market_advice = []
    if market_ctx.get("demand_level"):
        market_advice.append(f"Local demand level: {market_ctx['demand_level']}.")
    if market_ctx.get("estimated_target_customers") is not None:
        market_advice.append(
            f"Estimated target customers in radius: {int(market_ctx['estimated_target_customers']):,}."
        )
    if opportunities:
        market_advice.extend(opportunities[:2])
    if not market_advice:
        market_advice = [
            "Leverage local demand indicators and mandi connectivity shown in the market analysis."
        ]

    risk_items = (
        threats
        or weaknesses
        or [
            "Review seasonal supply volatility and maintain working-capital buffers.",
            "Validate subsidy eligibility directly with the implementing agency before commitment.",
        ]
    )

    next_steps = [
        "Validate scheme eligibility documents with the local DIC or bank branch.",
        "Prepare a detailed project report using the dashboard financial model.",
        "Register on the MSME Udyam portal before applying for credit-linked subsidies.",
    ]
    if overall is not None and float(overall) >= 75:
        next_steps.insert(
            0, "Proceed with formal loan application using the matched subsidy schemes."
        )

    rec_text = recommendation.explain(feasibility)
    evidence = prepared_context.get("rag_evidence", []) or []

    return AIAdvice(
        summary=" ".join(summary_parts),
        recommendation=rec_text,
        reasoning=strengths
        or ["Verified backend indicators support the proposed enterprise model."],
        financial_advice=financial_advice,
        market_advice=market_advice,
        competition_advice=competition_advice,
        scheme_advice=scheme_advice,
        risks=risk_items,
        next_steps=next_steps,
        disclaimers=[
            "This guidance is generated from verified backend analysis data.",
            "Final subsidy approval remains subject to official government verification.",
        ],
        sources=[],
        confidence="high" if overall is not None and float(overall) >= 60 else "medium",
        model_name="backend-grounded-v1",
        prompt_version="backend-grounded-v1",
        language=normalized_language,
        rag_status=rag_status,
        evidence=evidence,
    )


def _fallback_ai_advice(language: str = "en") -> AIAdvice:
    normalized_language = language if language in {"en", "hi", "mr"} else "en"
    return AIAdvice(
        summary="AI advisory guidance is temporarily unavailable. The backend analysis remains the authoritative source of truth.",
        recommendation="Review the verified backend analysis before making a final decision. Retry the AI advisory layer once the provider is available.",
        reasoning=[
            "The AI provider or validation pipeline is unavailable.",
            "The system is falling back to verified analysis data only.",
        ],
        financial_advice=[
            "Use the backend-calculated financial summary as the authoritative financial signal.",
        ],
        market_advice=[
            "Use the verified market analysis output as the authoritative market signal.",
        ],
        competition_advice=[
            "Use the verified competition analysis output as the authoritative competition signal.",
        ],
        scheme_advice=[
            "Use the verified scheme matching output as the authoritative scheme signal.",
        ],
        risks=[
            "AI-generated recommendations are currently unavailable.",
            "Decisions should rely on the verified backend analysis until the AI layer recovers.",
        ],
        next_steps=[
            "Retry the AI advisor when the provider is available.",
            "Continue using the structured analysis output as the source of truth.",
        ],
        disclaimers=[
            "AI guidance is unavailable; backend analysis remains authoritative.",
        ],
        sources=[],
        confidence="unverified",
        model_name="unavailable",
        prompt_version="fallback-v1",
        language=normalized_language,
        rag_status=RAGStatus.NO_RELEVANT_EVIDENCE.value,
        evidence=[],
    )


def generate_advice(
    analysis_context: AnalysisContext | dict,
    language: str = "en",
    db: Any | None = None,
) -> AIAdvice:
    """Turn a verified AnalysisContext into structured AIAdvice grounded in RAG evidence.

    The method is intentionally defensive: any provider, prompt, or validation
    issue degrades to a safe fallback rather than crashing the analysis flow.
    """
    logger.info("Generating advice", extra={"language": language})

    prepared_context: dict[str, Any] | None = None
    try:
        # 1. Construct natural RAG query from AnalysisContext
        ctx_dict = context_builder._as_dict(analysis_context)
        category_name = (
            context_builder._safe_get(ctx_dict, "business", "category", "name")
            or context_builder._safe_get(ctx_dict, "business", "category_name")
            or ""
        )
        district_name = (
            context_builder._safe_get(ctx_dict, "location", "district", "name")
            or context_builder._safe_get(ctx_dict, "location", "district_name")
            or ""
        )
        schemes_list = ctx_dict.get("schemes", []) or []
        scheme_names: list[str] = []
        primary_scheme_id = None
        for s in schemes_list:
            s_dict = context_builder._as_dict(s)
            s_meta = context_builder._as_dict(s_dict.get("scheme"))
            s_id = s_meta.get("id") or s_dict.get("scheme_id")
            if s_id and not primary_scheme_id:
                primary_scheme_id = s_id
            s_name = s_meta.get("name")
            if s_name:
                scheme_names.append(str(s_name))

        query_parts = [
            p
            for p in [
                category_name,
                district_name,
                " ".join(scheme_names),
                "eligibility loan subsidy rules",
            ]
            if p
        ]
        query_str = " ".join(query_parts) or "business scheme rules eligibility subsidy"

        # 2. Perform RAG Retrieval if DB session provided
        rag_response = None
        if db is not None:
            try:
                from app.rag.retriever import retrieve_evidence

                rag_response = retrieve_evidence(
                    db=db,
                    query=query_str,
                    scheme_id=primary_scheme_id,
                    language=language,
                )
            except (ConnectionError, TimeoutError) as exc:
                logger.warning("RAG vector store network/timeout issue: %s", exc)
                rag_response = RAGQueryResponse(
                    status=RAGStatus.NO_RELEVANT_EVIDENCE.value, evidence=[]
                )
            except Exception as exc:
                logger.warning(
                    "RAG evidence retrieval failed; using empty fallback: %s", exc, exc_info=True
                )
                rag_response = RAGQueryResponse(
                    status=RAGStatus.NO_RELEVANT_EVIDENCE.value, evidence=[]
                )
        else:
            rag_response = RAGQueryResponse(
                status=RAGStatus.NO_RELEVANT_EVIDENCE.value, evidence=[]
            )

        # 3. Shape AnalysisContext and RAG evidence into prompt payload.
        prepared_context = context_builder.build(analysis_context, rag_response=rag_response)

        # 4. Build layered prompt containing evidence & status instructions.
        prompt = prompts.build_advisor_prompt(prepared_context, language=language)

        # 5. Call LLM provider abstraction.
        raw_output_str = llm.generate(prompt)

        # Parse JSON output if LLM returns a string
        if isinstance(raw_output_str, str):
            try:
                cleaned_str = raw_output_str.strip()
                if cleaned_str.startswith("```json"):
                    cleaned_str = cleaned_str[7:]
                if cleaned_str.startswith("```"):
                    cleaned_str = cleaned_str[3:]
                if cleaned_str.endswith("```"):
                    cleaned_str = cleaned_str[:-3]
                raw_output = json.loads(cleaned_str.strip())
            except json.JSONDecodeError as exc:
                logger.warning(
                    "LLM response failed JSON parsing; constructing fallback dict: %s", exc
                )
                raw_output = {
                    "summary": str(raw_output_str)[:500],
                    "recommendation": "Review verified backend analysis data.",
                }
            except Exception as exc:
                logger.warning("Unexpected error during LLM response parsing: %s", exc)
                raw_output = {
                    "summary": str(raw_output_str)[:500],
                    "recommendation": "Review verified backend analysis data.",
                }
        else:
            raw_output = context_builder._as_dict(raw_output_str)

        # 6. Validate output against guardrails & attach RAG evidence/status
        validated_output = guardrails.validate(raw_output, prepared_context)

        # 7. Attach deterministic recommendation explanation & conflict warnings
        rec_text = recommendation.explain(prepared_context.get("feasibility", {}))
        if (
            prepared_context.get("rag_status") == RAGStatus.CONFLICTING_SOURCES.value
            or prepared_context.get("rag_status") == RAGStatus.CONFLICTING_SOURCES
        ):
            rec_text += " WARNING: Official government documents contain conflicting rule metrics. Please verify details directly with the relevant official department."
        validated_output["recommendation"] = rec_text

        return AIAdvice.model_validate(validated_output)
    except (ImportError, ModuleNotFoundError):
        raise
    except (llm.LLMError, json.JSONDecodeError, ConnectionError, TimeoutError, ValueError) as exc:
        logger.warning(
            "AI advisor pipeline recoverable issue; returning degraded fallback: %s", exc
        )
        if prepared_context:
            return _backend_grounded_advice(prepared_context, language)
        return _fallback_ai_advice(language)
    except Exception as exc:
        logger.exception("AI advice generation failed with unexpected error: %s", exc)
        if prepared_context:
            return _backend_grounded_advice(prepared_context, language)
        return _fallback_ai_advice(language)
