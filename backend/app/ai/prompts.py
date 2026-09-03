from __future__ import annotations

import json


def build_advisor_prompt(context: dict, language: str = "en") -> str:
    """Build a grounded prompt that asks the LLM to explain verified data and RAG evidence."""
    normalized_language = language if language in {"en", "hi", "mr"} else "en"
    pretty_context = json.dumps(context, ensure_ascii=False, default=str)

    rag_status = context.get("rag_status")
    rag_evidence = context.get("rag_evidence", []) or []

    rag_instruction_block = ""
    if rag_status == "success" and rag_evidence:
        evidence_lines = []
        for idx, item in enumerate(rag_evidence, 1):
            src = item.get("source", {})
            evidence_lines.append(
                f"Evidence [{idx}] (Score: {item.get('score')}, Document: '{src.get('title')}', "
                f"Page: {src.get('page_number')}, Section: '{src.get('section_title')}', "
                f"Source: '{src.get('source_name')}', URL: '{src.get('source_url')}'):\n"
                f'"""{item.get("text")}"""'
            )
        evidence_str = "\n\n".join(evidence_lines)
        rag_instruction_block = f"""
RAG RETRIEVAL STATUS: SUCCESS (VERIFIED OFFICIAL EVIDENCE AVAILABLE)
{evidence_str}

RELEVANT RAG EVIDENCE RULES:
- Treat the supplied RAG evidence as authoritative for all factual scheme claims.
- Scheme facts, eligibility requirements, loan limits, subsidy percentages, interest rates, and tenure must be grounded in the provided evidence.
- Do not invent or assume scheme facts that are not supported by the evidence or backend context.
"""
    elif rag_status == "conflicting_sources":
        evidence_lines = []
        for idx, item in enumerate(rag_evidence, 1):
            src = item.get("source", {})
            evidence_lines.append(
                f"Conflicting Evidence [{idx}] (Document: '{src.get('title')}', "
                f"Page: {src.get('page_number')}, Section: '{src.get('section_title')}'):\n"
                f'"""{item.get("text")}"""'
            )
        evidence_str = "\n\n".join(evidence_lines)
        rag_instruction_block = f"""
RAG RETRIEVAL STATUS: CONFLICTING SOURCES DETECTED
{evidence_str}

CONFLICTING EVIDENCE INSTRUCTIONS:
- Active government documents contain conflicting rule metrics (e.g. mismatched subsidy percentages or loan limits).
- Do NOT silently choose one conflicting value as fact.
- EXPLICITLY WARN the user in the advice that official sources disagree.
- Recommend verification with the appropriate official government department/authority.
"""
    elif rag_status == "no_relevant_evidence" or (rag_status is not None and not rag_evidence):
        rag_instruction_block = """
RAG RETRIEVAL STATUS: NO RELEVANT EVIDENCE FOUND
INSTRUCTIONS:
- Relevant scheme facts could not be verified from available official documents.
- Do NOT fabricate or infer missing scheme facts, subsidy rates, or loan conditions.
- Clearly state in scheme advice that official document verification with the department is required.
"""

    return f"""
You are an AI business advisor for UdyamAI.

Core rules:
- Use only the verified backend data and RAG evidence contained in the context below.
- Do not invent subsidy percentages, loan rates, prices, project costs, market size, or eligibility rules.
- If a value is missing or not verified, say so explicitly.
- If competition_data_available is false or no business records exist in radius, do NOT claim there is zero competition or high first-mover advantage; advise that local competitive data is insufficient.
- Explain the feasibility result using the given backend numbers.
- Return a valid JSON object that matches the schema expected by the backend.
- Keep the answer in {normalized_language}.

OUTPUT REQUIREMENTS:
- summary: string
- recommendation: string
- reasoning: list[str]
- financial_advice: list[str]
- market_advice: list[str]
- competition_advice: list[str]
- scheme_advice: list[str]
- risks: list[str]
- next_steps: list[str]
- disclaimers: list[str]
- sources: list[{{"claim": str, "source_type": str, "reference_id": str}}]
- confidence: one of ["high", "medium", "low", "unverified"]
- model_name: string
- prompt_version: string
- language: {normalized_language}

JSON FORMAT EXAMPLE:
```json
{{
  "summary": "The dairy business is moderately feasible with required capital contribution.",
  "recommendation": "Proceed conditionally while maintaining financial controls.",
  "reasoning": ["Market demand is strong.", "Financial contribution is adequate."],
  "financial_advice": ["Maintain reserve capital for feed costs."],
  "market_advice": ["Target local households in the taluka."],
  "competition_advice": ["Compete on quality and direct delivery."],
  "scheme_advice": ["Explore PMFME scheme for credit-linked subsidy."],
  "risks": ["Price fluctuations in animal feed."],
  "next_steps": ["Register business and arrange initial contribution."],
  "disclaimers": ["Advice is based on verified backend input data."],
  "sources": [{{"claim": "PMFME eligibility", "source_type": "scheme_rule", "reference_id": "pmfme_v1"}}],
  "confidence": "high",
  "model_name": "gemini-1.5-pro",
  "prompt_version": "v1",
  "language": "{normalized_language}"
}}
```

{rag_instruction_block}

Use the backend data to explain:
1. whether the business appears feasible
2. what the key financial and risk constraints are
3. what the user should do next
4. which scheme(s) are relevant and why

Context:
{pretty_context}
""".strip()
