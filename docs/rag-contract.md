# UdyamAI - RAG Layer Interface Contract

This document defines the interface and data contract between the **RAG Layer (AI Engineer 2)** and the **AI Advisor / Application Layer (AI Engineer 1 & Backend)**. The purpose of this contract is to ensure clean, structured, and traceable evidence retrieval to support AI-generated scheme advisor recommendations.

---

## 1. Input Contract

When requesting evidence, the caller (AI Advisor or Backend service) must query the RAG service using the following parameters:

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `query` | `string` | **Yes** | The search query compiled from the user's business context. |
| `scheme_id` | `UUID` | No | If provided, filters retrieved chunks specifically to this government scheme. |
| `language` | `string` | No | Optional language code filter (e.g., `"en"`, `"mr"`). |
| `limit` | `integer` | No | Maximum number of evidence chunks to retrieve (default: `5`). |
| `score_threshold` | `float` | No | Minimum similarity score required for matching (default: `0.70`). |

### Example Request (Pydantic / JSON)
```json
{
  "query": "What is the contribution requirement and loan limit for PMFME?",
  "scheme_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "language": "en",
  "limit": 3,
  "score_threshold": 0.72
}
```

---

## 2. Output Contract (Retrieved Evidence)

The RAG layer will return a structured response indicating the match status and enclosing the verified evidence list.

### Response Statuses
*   `"success"`: Relevant evidence was found and retrieved.
*   `"no_relevant_evidence"`: No chunks matched above the similarity threshold.
*   `"conflicting_sources"`: Found multiple active documents with conflicting metrics (e.g., mismatched interest rates or loan limits).

### Example Response Schema (JSON)
```json
{
  "status": "success",
  "evidence": [
    {
      "chunk_id": "f83a45c2-df38-4e89-9a72-7634f195d2c4",
      "text": "Beneficiary contribution under PMFME scheme is 10% of the project cost, with the remaining 90% funded by bank loan up to a limit of ₹10 lakh.",
      "score": 0.895,
      "source": {
        "document_id": "b1b01c38-8c10-4bc3-95cf-0e1948bc3da1",
        "title": "PMFME Official Guidelines 2024",
        "page_number": 14,
        "section_title": "Financial Assistance and Funding Pattern",
        "source_name": "Ministry of Food Processing Industries",
        "source_url": "https://mofpi.gov.in/pmfme/guidelines",
        "language": "en",
        "version": "2024.1",
        "effective_from": "2024-01-01",
        "effective_until": null
      }
    }
  ]
}
```

---

## 3. Conflict and Missing Evidence Handling

### A. Missing Evidence
If no chunk meets the similarity threshold, the RAG service returns `"status": "no_relevant_evidence"` with an empty array. The advisor model must use this status to explain to the user that it could not verify the criteria from official source documents, avoiding hallucinations.

### B. Conflicting Sources
If the RAG service detects contradictory rules across different active files, it returns `"status": "conflicting_sources"`. The final advisor response must warn the user of the conflicting rules and recommend verification with official departments.

---

## 4. Key Rules for Evidence Generation
1.  **Strict Traceability**: Chunks must always include their document version, exact page number, and section title to ensure verifiable citations.
2.  **No Fabricated Sources**: In the absence of an official PDF/metadata field, it must be set to `null` rather than using mock URLs or pages.
3.  **No Direct Calculations**: The RAG layer returns text evidence. It does not perform eligibility math or calculate interest; this is the responsibility of Backend Engineer 1.
