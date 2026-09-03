# 📄 UdyamAI - Phase 2 API Contracts Specification

**Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Status:** Frozen for Frontend Integration  

---

> [!IMPORTANT]
> **Contract Immutability Warning**  
> Do not change contracts casually after frontend integration begins. Any required changes to endpoints, request payloads, response schemas, or field names must undergo an architectural review and version bump.

---

## 📌 Overview

This document specifies the RESTful API contracts for the UdyamAI platform. The backend is built with **FastAPI**, **SQLModel / Pydantic v2**, and **PostgreSQL / PostGIS**, serving a **Next.js 14** frontend.

### 📚 Specialized Architecture & Engine Documents
For deep-dive technical logic, refer to:
- **Analysis Workflow & Pipeline**: [analysis-flow.md](file:///d:/UdyamAI/docs/analysis-flow.md)
- **Finance Engine & Formulas**: [finance-engine.md](file:///d:/UdyamAI/docs/finance-engine.md)
- **AI Advisor & RAG Integration**: [ai-integration.md](file:///d:/UdyamAI/docs/ai-integration.md)

---

## 🏛️ Service Ownership Matrix

| Domain Area | Service Owner / Module | Route File | Primary DB Models |
|---|---|---|---|
| **Analysis Pipeline** | `AnalysisOrchestrator` / `AnalysisService` | `app/api/routes/analysis.py` | `AnalysisRun`, `FeasibilityAnalysis`, `AIAnalysis` |
| **Location & GIS** | `LocationService` | `app/api/routes/locations.py` | `District`, `Taluka`, `GramPanchayat`, `Village` |
| **Business Categories** | `BusinessService` | `app/api/routes/businesses.py` | `BusinessCategory`, `BusinessModel`, `Business` |
| **Finance Engine** | `FinanceService` (`app/finance/`) | `app/api/routes/finance.py` | `SchemeRule`, `Scheme` |
| **Schemes & Matcher** | `SchemeService` (`app/schemes/`) | `app/api/routes/schemes.py` | `Scheme`, `SchemeRule`, `SchemeMatch` |
| **Market & Competition** | `MarketService` (`app/market/`, `app/geo/`) | `app/api/routes/markets.py` | `Market`, `MarketPrice`, `MarketAnalysis`, `CompetitorAnalysis` |
| **Infrastructure & Data** | `InfrastructureService` etc. | `app/api/routes/infrastructure.py` | `InfrastructureFacility`, `Agriculture`, `Livestock`, `Population` |
| **Reports** | `ReportService` | `app/api/routes/reports.py` | `Report` |
| **AI Advisor Layer** | `advisor` (`app/ai/`, `app/rag/`) | Orchestrated internally | `AIAnalysis`, `RAGChunk`, `Document` |

---

## 🔒 Non-Negotiable AI Boundary

1. **AI Never Computes Numbers**: Financial calculations, EMIs, loan sizing, feasibility sub-scores, and spatial densities are calculated **strictly by deterministic Python services** before AI invocation.
2. **Immutable Input**: The AI receives an immutable `AnalysisContext` and cannot mutate any numerical figures or eligibility flags.
3. **No Financial Guarantees**: Phrases promising "guaranteed loans" or unverified subsidy percentages are blocked by guardrails.

---

## 📐 Calculation Rules Summary

- **Project Cost Raw**: $\text{Available Capital} / (\text{Contribution \%} / 100)$
- **Feasible Cost**: $\min(\max(\text{Target Cost}, \text{Min Project Cost}), \text{Max Project Cost})$
- **Loan Potential**: $\min(\text{Feasible Cost} \times \text{Loan \%}, \text{Max Loan Amount})$
- **Amortization EMI**: $P \times \frac{r(1+r)^n}{(1+r)^n - 1}$ (Supports monthly, quarterly, semi-annual, annual cycles)
- **Feasibility Score**: $(S_{\text{market}} \times 0.25) + (S_{\text{finance}} \times 0.25) + (S_{\text{competition}} \times 0.20) + (S_{\text{infra}} \times 0.15) + (S_{\text{risk}} \times 0.15)$
- **Scenarios & DSCR**: $\text{DSCR} = \text{Operating Surplus} / \text{Monthly EMI}$. Zero revenue invented when data is missing.

---

## ⚠️ Standard Error Response Schema & Error Codes

All non-`2xx` HTTP response bodies follow the standard error structure:

```json
{
  "error": {
    "code": "LOCATION_NOT_FOUND",
    "message": "The selected village could not be found.",
    "details": [
      {
        "field": "location_id",
        "issue": "Village with ID c7a85f64-... not found"
      }
    ]
  },
  "detail": "The selected village could not be found.",
  "error_code": "LOCATION_NOT_FOUND",
  "status_code": 404
}
```

### Standard Error Codes

| Error Code | HTTP Status | Description |
|---|---|---|
| `MISSING_REQUIRED_FIELD` | `400` | Mandatory payload parameter is missing |
| `LOCATION_NOT_FOUND` | `404` | Specified village or district was not found |
| `BUSINESS_CATEGORY_NOT_FOUND` | `404` | Specified business category was not found |
| `USER_NOT_FOUND` | `404` | User profile ID does not exist |
| `INSUFFICIENT_MARGIN` | `422` | Available capital is lower than required scheme margin |
| `BELOW_MINIMUM_COST` | `422` | Project cost is below minimum scheme threshold |
| `INVALID_SCHEME_RULE` | `400` / `422` | Scheme rule contains invalid interest rate or tenure parameters |
| `CALCULATION_ERROR` | `500` | Financial or feasibility calculation failure |
| `AI_UNAVAILABLE` | `500` | AI advice layer unavailable (handled via graceful degraded fallback) |
| `VALIDATION_ERROR` | `422` | Request body failed Pydantic / JSON schema validation |
| `DATABASE_ERROR` | `500` | PostgreSQL / PostGIS transaction or query execution error |
| `INTERNAL_SERVER_ERROR` | `500` | Unhandled server exception |

---

## ⚙️ General Architectural Assumptions

1. **Spatial Buffer Default**: Spatial market and competitor queries default to **10.0 km** if radius is not explicitly specified.
2. **Precision & Rounding**: Currency values are rounded to 2 decimal places (`0.01` precision); scores are rounded to 1 decimal place (`0.1` precision).
3. **Idempotency**: `POST /api/v1/finance/calculate` is purely stateless and idempotent. `POST /api/v1/analysis` generates a new trackable `AnalysisRun` record.
4. **Multilingual Fallback**: Supported languages are `"en"` (English), `"hi"` (Hindi), and `"mr"` (Marathi). Any unsupported language code defaults to `"en"`.

---

## 🗺️ Summary of Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/analysis` | `POST` | Trigger a new multi-criteria feasibility analysis run |
| `/api/v1/analysis/{analysis_id}` | `GET` | Retrieve complete details and results of an analysis run |
| `/api/v1/analysis/{analysis_id}/status` | `GET` | Poll status and progress of an analysis run |
| `/api/v1/locations/districts` | `GET` | List administrative districts filtered by state/search |
| `/api/v1/locations/talukas` | `GET` | List administrative talukas filtered by district |
| `/api/v1/locations/villages` | `GET` | List administrative villages filtered by taluka/district |
| `/api/v1/business-categories` | `GET` | List available business categories and sectors |
| `/api/v1/business-categories/models` | `GET` | List business model reference data (startup costs, assumptions) |
| `/api/v1/businesses` | `GET` | List business establishments with optional filters |
| `/api/v1/businesses/{business_id}` | `GET` | Get a single business establishment by ID |
| `/api/v1/finance/calculate` | `POST` | Calculate project funding, loan EMI, and repayment schedule |
| `/api/v1/schemes` | `GET` | List government schemes filtered by state/agency |
| `/api/v1/schemes/states` | `GET` | Get distinct states with schemes |
| `/api/v1/schemes/agencies` | `GET` | Get distinct agency names |
| `/api/v1/schemes/{scheme_id}` | `GET` | Get scheme by ID |
| `/api/v1/schemes/{scheme_id}/rules` | `GET` | Get scheme rules |
| `/api/v1/schemes/{scheme_id}/rules/latest` | `GET` | Get latest active rule |
| `/api/v1/schemes/{scheme_id}/eligibility-rules` | `GET` | Get eligibility rules |
| `/api/v1/schemes/{scheme_id}/eligibility-rules/types` | `GET` | Get eligibility rule types |
| `/api/v1/schemes/matches/{run_id}` | `GET` | Get scheme matches for analysis run |
| `/api/v1/schemes/match` | `POST` | Evaluate beneficiary profile against eligible government schemes |
| `/api/v1/reports/{report_id}` | `GET` | Fetch details and PDF download link for a generated report |
| `/api/v1/locations/nearby/villages` | `GET` | Find villages within radius of coordinates |
| `/api/v1/locations/nearby/businesses` | `GET` | Find businesses within radius of coordinates |
| `/api/v1/locations/nearby/markets` | `GET` | Find markets within radius of coordinates |
| `/api/v1/locations/nearby/facilities` | `GET` | Find infrastructure facilities within radius |
| `/api/v1/locations/normalize` | `POST` | Normalize a raw location name (no DB write) |
| `/api/v1/locations/dedup/detect` | `GET` | Detect groups of potential duplicate locations |
| `/api/v1/locations/dedup/merge` | `POST` | Merge duplicate locations into canonical record |
| `/api/v1/markets` | `GET` | List markets with optional filters |
| `/api/v1/markets/types` | `GET` | Get distinct market types |
| `/api/v1/markets/commodities` | `GET` | Get distinct commodity names |
| `/api/v1/markets/{market_id}` | `GET` | Get market by ID |
| `/api/v1/markets/prices` | `GET` | List market prices with filters |
| `/api/v1/markets/prices/history` | `GET` | Price history for a commodity over time |
| `/api/v1/markets/prices/latest` | `GET` | Latest price per commodity |
| `/api/v1/markets/analyses/{run_id}` | `GET` | Market analyses for an analysis run |
| `/api/v1/markets/competitors/{run_id}` | `GET` | Competitor analyses for an analysis run |
| `/api/v1/infrastructure` | `GET` | List infrastructure records |
| `/api/v1/infrastructure/types` | `GET` | Get distinct facility types |
| `/api/v1/infrastructure/{id}` | `GET` | Get infrastructure record by ID |
| `/api/v1/agriculture` | `GET` | List agriculture records |
| `/api/v1/agriculture/crops` | `GET` | Get distinct crop names |
| `/api/v1/agriculture/seasons` | `GET` | Get distinct seasons |
| `/api/v1/agriculture/{id}` | `GET` | Get agriculture record by ID |
| `/api/v1/livestock` | `GET` | List livestock records |
| `/api/v1/livestock/types` | `GET` | Get distinct animal types |
| `/api/v1/livestock/{id}` | `GET` | Get livestock record by ID |
| `/api/v1/population` | `GET` | List population records |
| `/api/v1/population/years` | `GET` | Get distinct years with data |
| `/api/v1/population/{id}` | `GET` | Get population record by ID |
| `/api/v1/weather` | `GET` | List weather records |
| `/api/v1/weather/{id}` | `GET` | Get weather record by ID |
| `/api/v1/economic` | `GET` | List economic indicator records |
| `/api/v1/economic/indicators` | `GET` | Get distinct indicator names |
| `/api/v1/economic/{id}` | `GET` | Get economic indicator record by ID |

---

## 🔍 API Endpoint Specifications

---

### 1. `POST /api/v1/analysis`

Initiate a new feasibility, financial, market, and scheme analysis task for a micro-entrepreneur.

- **HTTP Method**: `POST`
- **Path**: `/api/v1/analysis`
- **Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <jwt_token>` *(optional depending on auth configuration)*

#### Request Body
```json
{
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "location_id": "c7a85f64-5717-4562-b3fc-2c963f66afa6",
  "business_category_id": "e2a85f64-5717-4562-b3fc-2c963f66afa7",
  "available_capital": 50000.00
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | `UUID` | Yes | Unique ID of the entrepreneur profile |
| `location_id` | `UUID` | No | ID of the target village (`villages.id`) |
| `business_category_id` | `UUID` | No | ID of the chosen business category (`business_categories.id`) |
| `available_capital` | `float` | No | Available capital / equity investment (`>= 0`) |

#### Responses

- **`202 Accepted`** - Analysis task queued successfully.
```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "location_id": "c7a85f64-5717-4562-b3fc-2c963f66afa6",
  "business_category_id": "e2a85f64-5717-4562-b3fc-2c963f66afa7",
  "available_capital": 50000.00,
  "status": "pending",
  "created_at": "2026-08-30T17:15:00Z",
  "completed_at": null
}
```

- **`422 Unprocessable Entity`** - Validation error in request body.

---

### 2. `GET /api/v1/analysis/{analysis_id}`

Retrieve full results for a completed analysis run, including feasibility breakdown, financial calculations, scheme matches, and report references.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/analysis/{analysis_id}`
- **Path Parameters**:
  - `analysis_id` (`UUID`, required): Unique identifier of the analysis run.

#### Responses

- **`200 OK`** - Analysis details retrieved successfully.
```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "location_id": "c7a85f64-5717-4562-b3fc-2c963f66afa6",
  "business_category_id": "e2a85f64-5717-4562-b3fc-2c963f66afa7",
  "available_capital": 50000.00,
  "status": "completed",
  "created_at": "2026-08-30T17:15:00Z",
  "completed_at": "2026-08-30T17:15:12Z",
  "feasibility_analysis": {
    "id": "f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "market_score": 82.5,
    "financial_score": 75.0,
    "competition_score": 68.0,
    "infrastructure_score": 90.0,
    "risk_score": 25.0,
    "overall_score": 78.5,
    "recommendation": "Highly Viable - Recommend proceeding with PM-EGPE subsidy application.",
    "strengths": ["High local demand for dairy products", "Proximity to milk collection hub"],
    "weaknesses": ["Requires continuous cold storage power supply"],
    "opportunities": ["State cattle distribution scheme subsidy available"],
    "threats": ["Seasonal fluctuations in fodder pricing"],
    "risks": ["Power outage impact on refrigeration"],
    "warnings": ["Ensure back-up diesel generator arrangement"],
    "confidence": "high"
  },
  "financial_summary": {
    "estimated_project_cost": 200000.00,
    "recommended_loan": 140000.00,
    "estimated_subsidy": 50000.00,
    "estimated_monthly_emi": 1750.50
  },
  "matched_schemes": [
    {
      "scheme_id": "s1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
      "scheme_name": "PMEGP (Prime Minister's Employment Generation Programme)",
      "match_status": "potential_match",
      "match_score": 0.92,
      "estimated_subsidy_amount": 50000.00
    }
  ],
  "reports": [
    {
      "id": "r1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
      "title": "Dairy Enterprise Feasibility Study - Pune",
      "report_file_path": "/api/v1/reports/r1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c"
    }
  ]
}
```

- **`404 Not Found`** - Analysis ID not found.

---

### 3. `GET /api/v1/analysis/{analysis_id}/status`

Check the processing status and execution state of an ongoing or completed analysis run.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/analysis/{analysis_id}/status`
- **Path Parameters**:
  - `analysis_id` (`UUID`, required): Unique identifier of the analysis run.

#### Responses

- **`200 OK`** - Status retrieved successfully.
```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "status": "running",
  "progress_percentage": 65,
  "current_step": "evaluating_scheme_rules",
  "created_at": "2026-08-30T17:15:00Z",
  "completed_at": null,
  "error_message": null
}
```

*Status Enum Values:* `pending`, `running`, `completed`, `failed`

- **`404 Not Found`** - Analysis ID not found.

---

### 4. `GET /api/v1/locations/districts`

Fetch a list of administrative districts, filtered optional by state name or search query.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/locations/districts`
- **Query Parameters**:
  - `state` (`string`, optional): State filter (e.g., `Maharashtra`).
  - `search` (`string`, optional): Text query to search district name.

#### Responses

- **`200 OK`** - List of districts returned.
```json
[
  {
    "id": "d1a85f64-5717-4562-b3fc-2c963f66afa1",
    "name": "Pune",
    "state": "Maharashtra",
    "lgd_code": "521"
  },
  {
    "id": "d2a85f64-5717-4562-b3fc-2c963f66afa2",
    "name": "Nashik",
    "state": "Maharashtra",
    "lgd_code": "522"
  }
]
```

---

### 5. `GET /api/v1/locations/talukas`

Fetch administrative talukas/sub-districts filtered by district ID.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/locations/talukas`
- **Query Parameters**:
  - `district_id` (`UUID`, optional): District identifier.
  - `search` (`string`, optional): Text search for taluka name.

#### Responses

- **`200 OK`** - List of talukas returned.
```json
[
  {
    "id": "t1a85f64-5717-4562-b3fc-2c963f66afa1",
    "name": "Haveli",
    "district_id": "d1a85f64-5717-4562-b3fc-2c963f66afa1",
    "lgd_code": "4185"
  },
  {
    "id": "t2a85f64-5717-4562-b3fc-2c963f66afa2",
    "name": "Baramati",
    "district_id": "d1a85f64-5717-4562-b3fc-2c963f66afa1",
    "lgd_code": "4186"
  }
]
```

---

### 6. `GET /api/v1/locations/villages`

Fetch administrative villages filtered by taluka/district with geo-coordinates and pin codes.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/locations/villages`
- **Query Parameters**:
  - `taluka_id` (`UUID`, optional): Taluka identifier.
  - `district_id` (`UUID`, optional): District identifier.
  - `search` (`string`, optional): Search village name or pin code.
  - `limit` (`int`, optional, default `50`): Maximum records to return.
  - `offset` (`int`, optional, default `0`): Pagination offset.

#### Responses

- **`200 OK`** - List of villages returned.
```json
[
  {
    "id": "c7a85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Khed Shivapur",
    "district_id": "d1a85f64-5717-4562-b3fc-2c963f66afa1",
    "taluka_id": "t1a85f64-5717-4562-b3fc-2c963f66afa1",
    "gram_panchayat_id": "g1a85f64-5717-4562-b3fc-2c963f66afa1",
    "lgd_code": "556123",
    "pin_code": "412205",
    "latitude": 18.3492,
    "longitude": 73.8504
  }
]
```

---

### 7. `GET /api/v1/business-categories`

List predefined business categories (e.g., Agriculture, Manufacturing, Services, Animal Husbandry).

- **HTTP Method**: `GET`
- **Path**: `/api/v1/business-categories`
- **Query Parameters**:
  - `sector` (`string`, optional): Sector filter (e.g. `Agriculture`, `Services`).
  - `active_only` (`boolean`, optional, default `true`): Filter active categories only.

#### Responses

- **`200 OK`** - List of business categories returned.
```json
[
  {
    "id": "e2a85f64-5717-4562-b3fc-2c963f66afa7",
    "name": "Dairy Farming & Milk Processing",
    "sector": "Agriculture & Livestock",
    "description": "Small-scale cattle rearing, milk collection, and dairy product processing.",
    "active": true,
    "created_at": "2026-01-15T10:00:00Z"
  },
  {
    "id": "e3a85f64-5717-4562-b3fc-2c963f66afa8",
    "name": "Poultry Rearing",
    "sector": "Livestock",
    "description": "Broiler and layer poultry farming operations.",
    "active": true,
    "created_at": "2026-01-15T10:00:00Z"
  }
]
```

---

### 8. `POST /api/v1/finance/calculate`

Perform interactive loan EMI, capital requirement, moratorium, and repayment schedule calculations.

- **HTTP Method**: `POST`
- **Path**: `/api/v1/finance/calculate`
- **Headers**:
  - `Content-Type: application/json`

#### Request Body
```json
{
  "desired_project_cost": 200000.00,
  "available_capital": 50000.00,
  "loan_percent": 75.0,
  "interest_rate": 8.5,
  "tenure_months": 60,
  "moratorium_months": 6
}
```

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| `desired_project_cost` | `float` | Yes | `gt: 0` | Total estimated startup/project cost |
| `available_capital` | `float` | Yes | `ge: 0` | Entrepreneur's equity capital |
| `loan_percent` | `float` | No | `ge: 0, le: 100` | Percentage of cost to fund via loan |
| `interest_rate` | `float` | Yes | `ge: 0, le: 100` | Annual interest rate percentage |
| `tenure_months` | `int` | Yes | `gt: 0` | Loan tenure in months |
| `moratorium_months` | `int` | No | `ge: 0` | Moratorium period in months (default `0`) |

#### Responses

- **`200 OK`** - Calculation successfully rendered.
```json
{
  "desired_project_cost": 200000.00,
  "available_capital": 50000.00,
  "required_contribution": 50000.00,
  "margin_gap": 0.00,
  "calculated_loan": 150000.00,
  "monthly_emi": 3077.20,
  "total_interest": 34632.00,
  "total_repayment": 184632.00,
  "repayment_schedule": [
    {
      "period_number": 1,
      "principal_amount": 0.00,
      "interest_amount": 1062.50,
      "payment_amount": 1062.50,
      "remaining_principal": 150000.00,
      "is_moratorium": true
    },
    {
      "period_number": 7,
      "principal_amount": 2014.70,
      "interest_amount": 1062.50,
      "payment_amount": 3077.20,
      "remaining_principal": 147985.30,
      "is_moratorium": false
    }
  ]
}
```

- **`422 Unprocessable Entity`** - Out-of-bounds inputs or missing parameters.

---

### 9. `GET /api/v1/schemes`

Query available government credit, subsidy, and micro-finance schemes.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/schemes`
- **Query Parameters**:
  - `state` (`string`, optional): Target state (e.g. `Maharashtra`, `Central`).
  - `agency_name` (`string`, optional): Scheme sponsoring agency (e.g., `KVIC`, `NABARD`, `NSFDC`).
  - `active_only` (`boolean`, optional, default `true`): Return active schemes only.
  - `limit` (`int`, optional, default `20`): Pagination limit.
  - `offset` (`int`, optional, default `0`): Pagination offset.

#### Responses

- **`200 OK`** - List of matching schemes.
```json
[
  {
    "id": "s1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "name": "Prime Minister's Employment Generation Programme (PMEGP)",
    "description": "Credit-linked subsidy program for setup of micro-enterprises.",
    "agency_name": "KVIC / Ministry of MSME",
    "state": "Central",
    "active": true,
    "official_url": "https://www.kviconline.gov.in/pmegpeportal/",
    "source": "official_gazette",
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

### 10. `POST /api/v1/schemes/match`

Run eligibility engine rules against beneficiary profile metrics and return scored scheme matches.

- **HTTP Method**: `POST`
- **Path**: `/api/v1/schemes/match`
- **Headers**:
  - `Content-Type: application/json`

#### Request Body
```json
{
  "analysis_run_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "applicant_age": 28,
  "category": "OBC",
  "annual_income": 120000.00,
  "location_id": "c7a85f64-5717-4562-b3fc-2c963f66afa6",
  "business_category_id": "e2a85f64-5717-4562-b3fc-2c963f66afa7",
  "desired_project_cost": 200000.00,
  "available_capital": 50000.00
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `analysis_run_id` | `UUID` | No | Associated analysis run ID |
| `applicant_age` | `int` | No | Age of beneficiary in years |
| `category` | `string` | No | Social category (`SC`, `ST`, `OBC`, `General`, `Women`) |
| `annual_income` | `float` | No | Total annual household income |
| `location_id` | `UUID` | No | Village ID |
| `business_category_id` | `UUID` | No | Target business category ID |
| `desired_project_cost` | `float` | No | Estimated total project investment |
| `available_capital` | `float` | No | Equity capital available |

#### Responses

- **`200 OK`** - Array of scheme matches with rule breakdown.
```json
[
  {
    "scheme_id": "s1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "scheme_name": "PMEGP",
    "match_status": "potential_match",
    "match_score": 0.95,
    "matched_conditions": {
      "age_limit": "Eligible (28 in 18-45 range)",
      "category": "OBC Special Category Subsidy eligible (25% rural)",
      "project_cost": "Eligible (2.0L <= 25.0L max cost)"
    },
    "failed_conditions": {},
    "missing_information": {
      "educational_qualification": "Requires 8th pass certificate for project cost > 10L"
    },
    "estimated_subsidy_amount": 50000.00,
    "estimated_loan_amount": 140000.00,
    "estimated_project_cost": 200000.00,
    "verification_required": true
  }
]
```

*Match Status Enum Values:* `potential_match`, `not_match`, `missing_information`, `verification_required`
*(Note: Legacy payloads using `not_matched` or `insufficient_information` are backward-compatibly mapped to `not_match` and `missing_information` respectively.)*

---

### 11. `GET /api/v1/reports/{report_id}`

Fetch metadata and PDF download link for a generated feasibility report.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/reports/{report_id}`
- **Path Parameters**:
  - `report_id` (`UUID`, required): Unique report identifier.

#### Responses

- **`200 OK`** - Report record retrieved.
```json
{
  "id": "r1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
  "analysis_run_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "title": "Dairy Enterprise Feasibility & Scheme Report - Khed Shivapur",
  "language": "mr",
  "report_data": {
    "summary": "Feasibility score 78.5%. PMEGP subsidy recommended.",
    "generated_sections": ["Executive Summary", "Financial Viability", "Scheme Eligibility", "SWOT Analysis"]
  },
  "report_file_path": "/static/reports/report_r1a2b3c4.pdf",
  "created_at": "2026-08-30T17:15:15Z"
}
```

- **`404 Not Found`** - Report ID not found.

---

---

### 12. `GET /api/v1/locations/nearby/villages`

Find villages within a radius of given coordinates using PostGIS.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/locations/nearby/villages`
- **Query Parameters**:
  - `lat` (`float`, required): Center latitude (-90 to 90).
  - `lng` (`float`, required): Center longitude (-180 to 180).
  - `radius_km` (`float`, optional, default `10.0`): Search radius in km (max 100).
  - `district_id` (`UUID`, optional): Filter by district.
  - `limit` (`int`, optional, default `50`): Max results (max 200).

#### Response
```json
[
  {
    "id": "c7a85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Khed Shivapur",
    "district_id": "d1a85f64-5717-4562-b3fc-2c963f66afa1",
    "taluka_id": "t1a85f64-5717-4562-b3fc-2c963f66afa1",
    "gram_panchayat_id": "g1a85f64-5717-4562-b3fc-2c963f66afa1",
    "pin_code": "412205",
    "latitude": 18.3492,
    "longitude": 73.8504,
    "distance_meters": 1250.5
  }
]
```

---

### 13. `GET /api/v1/locations/nearby/businesses`

Find businesses within a radius using PostGIS.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/locations/nearby/businesses`
- **Query Parameters**:
  - `lat` (`float`, required): Center latitude.
  - `lng` (`float`, required): Center longitude.
  - `radius_km` (`float`, optional, default `10.0`): Search radius (max 50).
  - `category_id` (`UUID`, optional): Filter by business category.
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
```json
[
  {
    "id": "b1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "name": "Shivapur Dairy Center",
    "business_category_id": "e2a85f64-5717-4562-b3fc-2c963f66afa7",
    "address": "Khed Shivapur, Pune",
    "latitude": 18.35,
    "longitude": 73.85,
    "distance_meters": 1500.0
  }
]
```

---

### 14. `GET /api/v1/locations/nearby/markets`

Find markets within a radius using PostGIS.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/locations/nearby/markets`
- **Query Parameters**:
  - `lat` (`float`, required): Center latitude.
  - `lng` (`float`, required): Center longitude.
  - `radius_km` (`float`, optional, default `25.0`): Search radius (max 100).
  - `market_type` (`string`, optional): Filter by type (e.g., `mandi`, `retail`).
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
```json
[
  {
    "id": "m1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "name": "Pune Agricultural Mandi",
    "market_type": "mandi",
    "latitude": 18.52,
    "longitude": 73.86,
    "distance_meters": 5000.0
  }
]
```

---

### 15. `GET /api/v1/locations/nearby/facilities`

Find infrastructure facilities within a radius using PostGIS.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/locations/nearby/facilities`
- **Query Parameters**:
  - `lat` (`float`, required): Center latitude.
  - `lng` (`float`, required): Center longitude.
  - `radius_km` (`float`, optional, default `10.0`): Search radius (max 50).
  - `facility_type` (`string`, optional): Filter by type (e.g., `hospital`, `bank`).
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
```json
[
  {
    "id": "f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "name": "Rural Health Center",
    "facility_type": "hospital",
    "latitude": 18.36,
    "longitude": 73.84,
    "capacity": 50.0,
    "distance_meters": 2500.0
  }
]
```

---

### 16. `POST /api/v1/locations/normalize`

Normalize a raw location name without writing to the database. Useful for ingestion pipelines and validation.

- **HTTP Method**: `POST`
- **Path**: `/api/v1/locations/normalize`
- **Headers**:
  - `Content-Type: application/json`

#### Request Body
```json
{
  "name": "Pune District",
  "level": "district"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Raw location name to normalize |
| `level` | `string` | No | Location hierarchy level: `district`, `taluka`, `gram_panchayat`, `village` (default `village`) |

#### Response
- **`200 OK`** — Normalized name returned.
```json
{
  "original": "Pune District",
  "normalized": "pune",
  "level": "district"
}
```

---

### 17. `GET /api/v1/locations/dedup/detect`

Detect groups of potential duplicate locations at a given hierarchy level using fuzzy matching.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/locations/dedup/detect`
- **Query Parameters**:
  - `level` (`string`, optional, default `village`): Hierarchy level (`district`, `taluka`, `gram_panchayat`, `village`).
  - `state` (`string`, optional): Filter by state (districts only).
  - `fuzzy_threshold` (`float`, optional, default `0.85`): Fuzzy match threshold (0.5–1.0).

#### Response
- **`200 OK`** — Groups of potential duplicates.
```json
{
  "level": "district",
  "total_groups": 1,
  "groups": [
    {
      "normalized_name": "pune",
      "count": 3,
      "records": [
        {"id": "uuid1", "name": "Pune", "normalized": "pune", "lgd_code": "521"},
        {"id": "uuid2", "name": "PUNE", "normalized": "pune", "lgd_code": null},
        {"id": "uuid3", "name": "Pune District", "normalized": "pune", "lgd_code": null}
      ]
    }
  ]
}
```

---

### 18. `POST /api/v1/locations/dedup/merge`

Merge duplicate locations into a single canonical record. Re-parents all foreign key references from merged records to the kept record, then deletes the merged records.

> ⚠️ **Admin operation** — This modifies data. Use `/dedup/detect` first to preview.

- **HTTP Method**: `POST`
- **Path**: `/api/v1/locations/dedup/merge`
- **Headers**:
  - `Content-Type: application/json`

#### Request Body
```json
{
  "keep_id": "canonical-uuid",
  "merge_ids": ["duplicate-uuid-1", "duplicate-uuid-2"],
  "level": "village"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `keep_id` | `UUID` | Yes | UUID of the record to keep (canonical) |
| `merge_ids` | `array[UUID]` | Yes | UUIDs of duplicate records to merge into `keep_id` (min 1) |
| `level` | `string` | No | Hierarchy level (default `village`) |

#### Response
- **`200 OK`** — Merge completed.
```json
{
  "keep_id": "canonical-uuid",
  "merged_count": 2,
  "summary": {
    "villages.taluka_id": 5,
    "agriculture.location_id": 3,
    "markets.location_id": 2,
    "villages_deleted": 2
  }
}
```

---

### 19. `GET /api/v1/markets`

List markets with optional filters.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/markets`
- **Query Parameters**:
  - `market_type` (`string`, optional): Filter by market type.
  - `location_id` (`UUID`, optional): Filter by village location.
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
```json
[
  {
    "id": "m1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "name": "Pune Mandi",
    "market_type": "mandi",
    "location_id": "c7a85f64-5717-4562-b3fc-2c963f66afa6",
    "latitude": 18.52,
    "longitude": 73.86,
    "source": "government_data",
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

### 17. `GET /api/v1/markets/{market_id}`

Get a single market by ID.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/markets/{market_id}`
- **Path Parameters**:
  - `market_id` (`UUID`, required): Market identifier.

#### Response
- **`200 OK`** — Market record.
- **`404 Not Found`** — Market not found.

---

### 18. `GET /api/v1/markets/prices`

List market prices with optional filters.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/markets/prices`
- **Query Parameters**:
  - `market_id` (`UUID`, optional): Filter by market.
  - `location_id` (`UUID`, optional): Filter by location.
  - `commodity` (`string`, optional): Filter by commodity name.
  - `recorded_date` (`date`, optional): Filter by exact date.
  - `limit` (`int`, optional, default `100`): Max results.

#### Response
```json
[
  {
    "id": "p1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "market_id": "m1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "commodity": "Wheat",
    "commodity_variety": "Sharbati",
    "unit": "quintal",
    "min_price": 2200.0,
    "max_price": 2500.0,
    "modal_price": 2350.0,
    "arrival_quantity": 150.0,
    "recorded_date": "2026-03-15",
    "source": "mandi_portal"
  }
]
```

---

### 19. `GET /api/v1/markets/prices/history`

Get price history for a commodity over time (for trend analysis).

- **HTTP Method**: `GET`
- **Path**: `/api/v1/markets/prices/history`
- **Query Parameters**:
  - `commodity` (`string`, required): Commodity name.
  - `market_id` (`UUID`, optional): Filter by market.
  - `location_id` (`UUID`, optional): Filter by location.
  - `start_date` (`date`, optional): Start of date range.
  - `end_date` (`date`, optional): End of date range.
  - `limit` (`int`, optional, default `365`): Max results.

#### Response
```json
[
  {
    "id": "p1a2b3c4-...",
    "commodity": "Wheat",
    "modal_price": 2200.0,
    "recorded_date": "2026-01-15"
  },
  {
    "id": "p2a2b3c4-...",
    "commodity": "Wheat",
    "modal_price": 2350.0,
    "recorded_date": "2026-03-15"
  }
]
```

---

### 20. `GET /api/v1/markets/prices/latest`

Get the most recent price for each commodity.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/markets/prices/latest`
- **Query Parameters**:
  - `market_id` (`UUID`, optional): Filter by market.
  - `location_id` (`UUID`, optional): Filter by location.
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
- Returns one `MarketPrice` per commodity, ordered by `recorded_date` descending.

---

### 21. `GET /api/v1/markets/commodities`

Get distinct commodity names available.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/markets/commodities`
- **Query Parameters**:
  - `market_id` (`UUID`, optional): Filter by market.
  - `location_id` (`UUID`, optional): Filter by location.

#### Response
```json
["Rice", "Wheat", "Maize", "Soybean"]
```

---

### 22. `GET /api/v1/markets/types`

Get distinct market types.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/markets/types`

#### Response
```json
["mandi", "retail", "wholesale"]
```

---

### 23. `GET /api/v1/infrastructure`

List infrastructure records (hospitals, schools, banks, etc.).

- **HTTP Method**: `GET`
- **Path**: `/api/v1/infrastructure`
- **Query Parameters**:
  - `location_id` (`UUID`, optional): Filter by village location.
  - `facility_type` (`string`, optional): Filter by type (e.g., `hospital`, `school`).
  - `limit` (`int`, optional, default `50`): Max results (max 200).

#### Response
```json
[
  {
    "id": "f1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
    "location_id": "c7a85f64-5717-4562-b3fc-2c963f66afa6",
    "facility_type": "hospital",
    "name": "Rural Health Center",
    "latitude": 18.36,
    "longitude": 73.84,
    "distance_from_village": 2.5,
    "capacity": 50.0,
    "source": "government_data",
    "data_year": 2025,
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

### 24. `GET /api/v1/infrastructure/types`

Get distinct facility types.

#### Response
```json
["hospital", "school", "bank", "pharmacy"]
```

---

### 25. `GET /api/v1/infrastructure/{id}`

Get a single infrastructure record by ID.

- **`200 OK`** — Infrastructure record.
- **`404 Not Found`** — Record not found.

---

### 26. `GET /api/v1/agriculture`

List agriculture records with optional filters.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/agriculture`
- **Query Parameters**:
  - `location_id` (`UUID`, optional): Filter by village location.
  - `crop_name` (`string`, optional): Filter by crop name.
  - `crop_category` (`string`, optional): Filter by category (e.g., `cereals`, `pulses`).
  - `season` (`string`, optional): Filter by season (`kharif`, `rabi`).
  - `year` (`int`, optional): Filter by year.
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
```json
[
  {
    "id": "a1b2c3d4-...",
    "location_id": "c7a85f64-...",
    "crop_name": "Soybean",
    "crop_category": "oilseeds",
    "cultivated_area": 250.0,
    "production": 450.0,
    "production_unit": "quintal",
    "irrigated_area": 100.0,
    "year": 2025,
    "season": "kharif",
    "source": "census_data",
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

### 27. `GET /api/v1/agriculture/crops`

Get distinct crop names, optionally filtered by location.

- **Query Parameters**: `location_id` (UUID, optional)
- **Response**: `array[string]` — e.g., `["Rice", "Wheat", "Soybean"]`

---

### 28. `GET /api/v1/agriculture/seasons`

Get distinct seasons.

- **Response**: `array[string]` — e.g., `["kharif", "rabi", "zaid"]`

---

### 29. `GET /api/v1/agriculture/{id}`

Get a single agriculture record by ID.

- **`200 OK`** — Agriculture record.
- **`404 Not Found`** — Record not found.

---

### 30. `GET /api/v1/livestock`

List livestock records with optional filters.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/livestock`
- **Query Parameters**:
  - `location_id` (`UUID`, optional): Filter by village location.
  - `animal_type` (`string`, optional): Filter by type (e.g., `cattle`, `buffalo`).
  - `year` (`int`, optional): Filter by year.
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
```json
[
  {
    "id": "l1a2b3c4-...",
    "location_id": "c7a85f64-...",
    "animal_type": "cattle",
    "animal_count": 1200,
    "milk_production": 3500.0,
    "milk_production_unit": "liters/day",
    "year": 2025,
    "source": "census_data",
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

### 31. `GET /api/v1/livestock/types`

Get distinct animal types, optionally filtered by location.

- **Query Parameters**: `location_id` (UUID, optional)
- **Response**: `array[string]` — e.g., `["cattle", "buffalo", "goat"]`

---

### 32. `GET /api/v1/livestock/{id}`

Get a single livestock record by ID.

- **`200 OK`** — Livestock record.
- **`404 Not Found`** — Record not found.

---

### 33. `GET /api/v1/population`

List population records with optional filters.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/population`
- **Query Parameters**:
  - `location_id` (`UUID`, optional): Filter by village location.
  - `year` (`int`, optional): Filter by census/survey year.
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
```json
[
  {
    "id": "p1a2b3c4-...",
    "location_id": "c7a85f64-...",
    "year": 2021,
    "population_total": 5420,
    "male_population": 2780,
    "female_population": 2640,
    "households": 1150,
    "working_population": 3200,
    "literacy_rate": 82.5,
    "source": "census_2021",
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

### 34. `GET /api/v1/population/years`

Get distinct years with population data, optionally filtered by location.

- **Query Parameters**: `location_id` (UUID, optional)
- **Response**: `array[int]` — e.g., `[2021, 2011, 2001]`

---

### 35. `GET /api/v1/population/{id}`

Get a single population record by ID.

- **`200 OK`** — Population record.
- **`404 Not Found`** — Record not found.

---

### 36. `GET /api/v1/weather`

List weather records with optional filters.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/weather`
- **Query Parameters**:
  - `location_id` (`UUID`, optional): Filter by village location.
  - `start_date` (`date`, optional): Start of date range.
  - `end_date` (`date`, optional): End of date range.
  - `drought_only` (`boolean`, optional, default `false`): Only drought-flagged records.
  - `limit` (`int`, optional, default `50`): Max results (max 500).

#### Response
```json
[
  {
    "id": "w1a2b3c4-...",
    "location_id": "c7a85f64-...",
    "date": "2026-03-15",
    "rainfall_mm": 12.5,
    "temperature_min": 18.2,
    "temperature_max": 34.5,
    "drought_indicator": false,
    "source": "imd_data",
    "created_at": "2026-03-16T06:00:00Z"
  }
]
```

---

### 37. `GET /api/v1/weather/{id}`

Get a single weather record by ID.

- **`200 OK`** — Weather record.
- **`404 Not Found`** — Record not found.

---

### 38. `GET /api/v1/economic`

List economic indicator records with optional filters.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/economic`
- **Query Parameters**:
  - `location_id` (`UUID`, optional): Filter by village location.
  - `indicator_name` (`string`, optional): Filter by indicator (e.g., `GDP_per_capita`).
  - `year` (`int`, optional): Filter by year.
  - `limit` (`int`, optional, default `50`): Max results.

#### Response
```json
[
  {
    "id": "e1a2b3c4-...",
    "location_id": "c7a85f64-...",
    "indicator_name": "GDP_per_capita",
    "indicator_value": 125000.0,
    "unit": "INR",
    "year": 2025,
    "source": "economic_survey",
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

### 39. `GET /api/v1/economic/indicators`

Get distinct indicator names, optionally filtered by location.

- **Query Parameters**: `location_id` (UUID, optional)
- **Response**: `array[string]` — e.g., `["GDP_per_capita", "literacy_rate", "poverty_rate"]`

---

### 40. `GET /api/v1/economic/{id}`

Get a single economic indicator record by ID.

- **`200 OK`** — Economic indicator record.
- **`404 Not Found`** — Record not found.

---

### 41. `GET /api/v1/businesses`

List business establishment records with optional filters.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/businesses`
- **Query Parameters**:
  - `business_category_id` (`UUID`, optional): Filter by business category (`business_categories.id`).
  - `location_id` (`UUID`, optional): Filter by village location (`villages.id`).
  - `limit` (`int`, optional, default `50`, max `200`): Max results.

#### Response
```json
[
  {
    "id": "b1a2b3c4-...",
    "name": "Sharma Kirana Store",
    "business_category_id": "e2a85f64-...",
    "location_id": "c7a85f64-...",
    "district": "Pune",
    "taluka": "Haveli",
    "village": "Wagholi",
    "address": "Main Road, Wagholi",
    "latitude": 18.5792,
    "longitude": 73.9502,
    "source": "udyam_survey_2026",
    "source_url": "https://...",
    "data_year": 2026,
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

### 42. `GET /api/v1/businesses/{business_id}`

Get a single business establishment by ID.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/businesses/{business_id}`
- **Path Parameters**:
  - `business_id` (`UUID`, required): Business record ID.

#### Responses

- **`200 OK`** — Business establishment record (same shape as item in section 41).
- **`404 Not Found`** — Business not found.

---

### 43. `GET /api/v1/business-categories/models`

List business model reference data (startup cost ranges, working capital, revenue/operating-cost assumptions) used by the analysis engine.

- **HTTP Method**: `GET`
- **Path**: `/api/v1/business-categories/models`
- **Query Parameters**:
  - `business_category_id` (`UUID`, optional): Filter by business category.
  - `limit` (`int`, optional, default `100`, max `200`): Max results.

#### Response
```json
[
  {
    "id": "d1a2b3c4-...",
    "business_category_id": "e2a85f64-...",
    "name": "Small Dairy Farm (5 cattle)",
    "description": "Milk collection and local sale.",
    "startup_cost_min": 150000.0,
    "startup_cost_max": 300000.0,
    "working_capital": 50000.0,
    "active": true,
    "created_at": "2026-01-10T12:00:00Z"
  }
]
```

---

## 🔒 Contract Change Management & Freeze Policy

1. **Strict Versioning**: Any breaking change to response structure or removal of fields will require a endpoint prefix update (e.g. `/api/v2/...`).
2. **Backward Compatibility**: Non-breaking updates (such as adding new optional fields to response objects) are permitted subject to notice.
3. **Frontend Integration Freeze**: Once frontend components bind to these contracts, any modification requires consent from both backend and frontend module owners.
