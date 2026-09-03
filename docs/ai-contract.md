# AI Contract — UdyamAI AI Advisor Layer

**Status:** Finalized for Day 1, aligned with the current backend schema contracts in
`backend/app/schemas/`.

This contract is the source of truth for the AI Advisor layer. It reflects the verified
backend types used by the project today, rather than the earlier placeholder assumptions.

---

## 1. AI Input — `AnalysisContext`

`AnalysisContext` is the verified input object supplied to the AI layer. It is composed of
authenticated backend outputs and must never be invented by the model.

### Canonical schema shape

The current project contracts define the AI context as:

- `location`: `LocationContext`
- `business`: `BusinessContext`
- `financial`: `FinanceCalculateResponse`
- `market`: `MarketContext` (derived from `MarketAnalysisResponse`)
- `competition`: `CompetitionContext` (derived from `CompetitorAnalysisResponse`)
- `schemes`: `list[SchemeMatchContext]`
- `feasibility`: `FeasibilityContext` (derived from `FeasibilityAnalysisResponse`)
- `language`: `"en" | "hi" | "mr"`

### Pydantic contract

```python
class AnalysisContext(BaseModel):
    location: LocationContext
    business: BusinessContext
    financial: FinanceCalculateResponse
    market: MarketContext
    competition: CompetitionContext
    schemes: list[SchemeMatchContext] = Field(default_factory=list)
    feasibility: FeasibilityContext
    language: str = "en"
```

### Example payload

```json
{
  "location": {
    "village": {
      "id": "",
      "name": "",
      "district_id": "",
      "taluka_id": "",
      "gram_panchayat_id": "",
      "lgd_code": "",
      "pin_code": "411001",
      "latitude": 18.52,
      "longitude": 73.86
    },
    "district": {
      "id": "",
      "name": "Pune",
      "state": "Maharashtra",
      "lgd_code": ""
    },
    "taluka": {
      "id": "",
      "name": "Haveli",
      "district_id": "",
      "lgd_code": ""
    }
  },
  "business": {
    "category": {
      "id": "",
      "name": "Dairy",
      "sector": "Agriculture",
      "description": "",
      "active": true,
      "created_at": "2026-01-01T00:00:00Z"
    },
    "model": {
      "id": "",
      "business_category_id": "",
      "name": "Commercial Dairy",
      "description": "",
      "startup_cost_min": 0.0,
      "startup_cost_max": 0.0,
      "working_capital": 0.0,
      "active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  },
  "financial": {
    "status": "success",
    "available_capital": 100000.0,
    "required_contribution": 50000.0,
    "shortfall": 0.0,
    "desired_project_cost": 200000.0,
    "feasible_project_cost": 200000.0,
    "potential_loan": 150000.0,
    "beneficiary_contribution_percent": 25.0,
    "loan_percent": 75.0,
    "interest_rate": 8.5,
    "tenure_months": 60,
    "moratorium_months": 0,
    "payment_frequency": "monthly",
    "verification_required": false,
    "monthly_emi": 12000.0,
    "total_interest": 80000.0,
    "total_repayment": 200000.0,
    "working_capital": 50000.0,
    "repayment_schedule": [],
    "financial_scenarios": []
  },
  "market": {
    "radius_km": 5.0,
    "population_estimate": 5000,
    "household_estimate": 1500,
    "market_reach_estimate": 2000,
    "competitor_count": 3,
    "demand_indicators": {},
    "distribution_channels": {},
    "pricing_indicators": {},
    "market_gaps": {},
    "data_confidence": "high"
  },
  "competition": {
    "radius_km": 5.0,
    "competitor_count": 3,
    "competition_density": 0.5,
    "competitor_distribution": {},
    "identified_gaps": {},
    "data_confidence": "medium"
  },
  "schemes": [
    {
      "scheme": {
        "id": "",
        "name": "",
        "agency_name": "",
        "state": "",
        "official_url": ""
      },
      "rule": {
        "min_project_cost": 0.0,
        "max_project_cost": 0.0,
        "beneficiary_contribution_percent": 0.0,
        "loan_percent": 0.0,
        "max_loan_amount": 0.0,
        "interest_rate": 0.0,
        "tenure_months": 0,
        "moratorium_months": 0
      },
      "match_status": "potential_match",
      "match_score": 0.75,
      "matched_conditions": {},
      "failed_conditions": {},
      "missing_information": {},
      "estimated_loan_amount": 0.0,
      "estimated_project_cost": 0.0,
      "verification_required": true
    }
  ],
  "feasibility": {
    "market_score": 74.0,
    "financial_score": 82.0,
    "competition_score": 68.0,
    "infrastructure_score": 71.0,
    "risk_score": 33.0,
    "overall_score": 76.0,
    "recommendation": "Reasonably feasible based on verified inputs.",
    "strengths": {},
    "weaknesses": {},
    "opportunities": {},
    "threats": {},
    "risks": {},
    "warnings": {},
    "confidence": "high",
    "scoring_version": "v1"
  },
  "language": "en"
}
```

Important rules:

- There is no separate top-level `risks` field in the input contract.
- Risk data lives under `feasibility.risks` and `feasibility.warnings`.
- The AI layer must only explain facts already present in backend-verified data.

---

## 2. AI Output — `AIAdvice`

The AI output is the structured advisory response returned to the frontend.

### Contract

```python
class AIAdvice(BaseModel):
    summary: str
    recommendation: str
    reasoning: list[str] = Field(default_factory=list)
    financial_advice: list[str] = Field(default_factory=list)
    market_advice: list[str] = Field(default_factory=list)
    competition_advice: list[str] = Field(default_factory=list)
    scheme_advice: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    confidence: ConfidenceLevel
    model_name: str
    prompt_version: str
    language: str = "en"
```

### Example payload

```json
{
  "summary": "The venture appears feasible with moderate financial risk under the captured assumptions.",
  "recommendation": "Proceed with caution and validate the local market before committing full capital.",
  "reasoning": [
    "The project has a strong operating margin based on the provided financial model.",
    "Market demand is positive but limited to a narrow customer base.",
    "The selected scheme appears potentially relevant, but eligibility should be confirmed."
  ],
  "financial_advice": [
    "The available capital covers the current investment requirement with a moderate buffer.",
    "A shortfall should be avoided before scaling operations."
  ],
  "market_advice": [
    "Focus on the most dense demand clusters in the immediate service radius.",
    "Monitor local price sensitivity before expanding inventory."
  ],
  "competition_advice": [
    "The competitive landscape is moderate and requires differentiation in service quality."
  ],
  "scheme_advice": [
    "A scheme may be relevant, but final eligibility still requires verification."
  ],
  "risks": [
    "Demand may be lower than expected if pricing is too aggressive.",
    "The business may require additional working capital in the first 6 months."
  ],
  "next_steps": [
    "Verify the exact scheme eligibility rules.",
    "Re-run the financial model with conservative demand assumptions.",
    "Validate the supply chain and local area demand before finalizing the investment."
  ],
  "disclaimers": [
    "This advice is based only on the verified backend context and not on fresh field validation.",
    "Government scheme approval is not guaranteed."
  ],
  "sources": [
    {
      "claim": "The project has a 25% contribution requirement.",
      "source_type": "scheme_rule",
      "reference_id": ""
    }
  ],
  "confidence": "medium",
  "model_name": "gpt-4o-mini",
  "prompt_version": "ai-advisor-v1",
  "language": "en"
}
```

### Source reference contract

```python
class SourceReference(BaseModel):
    claim: str
    source_type: Literal["document", "scheme_rule", "data_source"]
    reference_id: UUID | str
```

---

## 3. Error handling contract

All AI failures must use the app-wide JSON error envelope already defined in the backend, not a custom format.

```json
{ "detail": "", "error_code": "AI_PROVIDER_UNAVAILABLE", "status_code": 503 }
```

Allowed error codes:

| Case | `error_code` |
|---|---|
| Provider unreachable | `AI_PROVIDER_UNAVAILABLE` |
| Timeout | `AI_TIMEOUT` |
| Rate limited | `AI_RATE_LIMITED` |
| Invalid/unparseable LLM output | `AI_INVALID_OUTPUT` |
| Context exceeds provider limit | `AI_CONTEXT_TOO_LARGE` |
| Provider content filter triggered | `AI_CONTENT_FILTERED` |

The AI layer must degrade gracefully when these occur. The rest of the business analysis must remain usable even if the AI response fails.

---

## 4. Language contract

The AI output and input context must use a plain language code string, not a nested locale object.

Allowed values:

- `"en"`
- `"hi"`
- `"mr"`

This matches the convention already used in the project for reports and conversation records.

---

## 5. Source metadata / provenance contract

The AI layer should preserve provenance for every factual claim it uses. The source object must reflect one of the project’s existing provenance patterns, not a third custom schema.

### RAG / document-backed claim

Use document provenance as defined in the RAG layer:

- `document_id`
- `title`
- `source_name`
- `source_url`
- `page_number`
- `section_title`

### Structured DB fact

Use data-source or scheme provenance for verified facts such as interest rates, market stats, or location data.

Examples:

- scheme rule record itself
- `Scheme` / `SchemeRule`
- provenance dataset metadata from `DataSource`

The AI contract does not invent a brand-new citation object. It reuses the project’s existing provenance shapes.

---

## 6. Confidence and verification status contract

`confidence` is a string value, not a nested object and not a database enum definition.

Allowed values:

- `"high"`
- `"medium"`
- `"low"`
- `"unverified"`

This is separate from `verification_required`, which remains a boolean field on scheme or claim-level data.

Rules:

- `confidence` describes the model’s confidence in the quality of the evidence.
- `verification_required` describes whether the backend or a human should validate a claim before acting on it.
- The two are distinct and must not be merged.

---

## 7. Guardrail rules for the AI layer

The AI must follow these rules at all times:

1. Use only supplied facts; do not invent financial or market numbers.
2. Distinguish facts from assumptions and uncertain claims.
3. Do not invent scheme eligibility, interest rates, or approval outcomes.
4. Do not guarantee a government subsidy or loan approval unless a verified result is explicitly provided.
5. Preserve source references when a claim depends on a datasource or document.
6. Follow the requested language exactly (`en`, `hi`, or `mr`).
7. Return valid structured output matching the Pydantic contract.
8. If the data is missing, say it is missing instead of guessing.

---

## 8. Open implementation decisions still owned by the team

These items are not schema-level blockers for Day 1, but they should be confirmed before full production use:

1. Whether AI advice is a dedicated `/ai` endpoint or embedded in the `/analysis` response path.
2. Whether the extra output fields in `AIAdvice` are stored as dedicated DB columns or embedded under the existing JSON plan structure.
3. Final alignment with AI Engineer 2 on the exact citation object shape used by RAG-backed claims.

---

## 9. Final Day 1 status

The AI schema layer is now aligned to the project’s real backend contracts. The remaining Day 1 work is implementation and guardrail completion:

- finalize and maintain the contract above
- harden LLM provider error handling
- add graceful fallback behavior when AI is unavailable
- add focused tests for contract validation and failure paths

This closes the Day 1 AI task without drifting back into stale placeholder assumptions.