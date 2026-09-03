from __future__ import annotations

import re
from typing import Any

_REQUIRED_CORE_FIELDS = {"summary", "recommendation"}
_ALLOWED_LANGUAGES = {"en", "hi", "mr"}
_ALLOWED_CONFIDENCE = {"high", "medium", "low", "unverified"}
_ALLOWED_SOURCE_TYPES = {"document", "scheme_rule", "data_source"}

_LIST_FIELDS = [
    "reasoning",
    "financial_advice",
    "market_advice",
    "competition_advice",
    "scheme_advice",
    "risks",
    "next_steps",
    "disclaimers",
]


def _contains_invented_financial_claim(
    text: str, context: dict[str, Any], has_verified_sources: bool = False
) -> bool:
    if not isinstance(text, str):
        return False

    lower_text = text.lower()

    if "guaranteed" in lower_text or "definitely" in lower_text:
        return True

    if has_verified_sources:
        return False

    if "subsidy" in lower_text and re.search(r"\b\d+\s*%", lower_text):
        if "backend" not in lower_text and "verified" not in lower_text:
            return True
    if "loan" in lower_text and re.search(r"\b\d+\s*%", lower_text):
        if "backend" not in lower_text and "verified" not in lower_text:
            return True
    if "interest" in lower_text and re.search(r"\b\d+\s*%", lower_text):
        if "backend" not in lower_text and "verified" not in lower_text:
            return True

    if (
        "approved" in lower_text
        and "not" not in lower_text
        and "requires verification" not in lower_text
        and "subject to" not in lower_text
    ):
        return True

    return False


def _validate_source_entry(source: Any) -> dict[str, Any] | None:
    if not isinstance(source, dict):
        return None

    claim = str(source.get("claim", "")).strip()
    if not claim:
        return None

    source_type = str(source.get("source_type", "")).lower()
    if source_type not in _ALLOWED_SOURCE_TYPES:
        source_type = "data_source"

    reference_id = source.get("reference_id")
    if reference_id is None:
        reference_id = "backend"
    elif isinstance(reference_id, (str, int, float)):
        ref_str = str(reference_id).strip()
        reference_id = ref_str if ref_str else "backend"
    else:
        try:
            ref_str = str(reference_id).strip()
            reference_id = ref_str if ref_str else "backend"
        except Exception:
            reference_id = "backend"

    return {
        "claim": claim,
        "source_type": source_type,
        "reference_id": reference_id,
    }


def validate(raw_output: dict, context: dict) -> dict:
    """Validate and normalize AI output before returning it to the backend."""
    if not isinstance(raw_output, dict):
        raise ValueError("AI output must be a JSON object.")

    missing_core = sorted(_REQUIRED_CORE_FIELDS - set(raw_output.keys()))
    if missing_core:
        raise ValueError(f"AI output is missing required fields: {', '.join(missing_core)}")

    for field in ["summary", "recommendation"]:
        value = raw_output.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI field '{field}' must be a non-empty string.")

    normalized: dict[str, Any] = {}
    normalized["summary"] = str(raw_output["summary"]).strip()
    normalized["recommendation"] = str(raw_output["recommendation"]).strip()

    # Coerce list fields (string -> 1-item list, None -> [], list -> list of strings)
    for field in _LIST_FIELDS:
        val = raw_output.get(field, [])
        if isinstance(val, str):
            normalized[field] = [val.strip()] if val.strip() else []
        elif isinstance(val, list):
            normalized[field] = [
                str(item).strip() for item in val if item is not None and str(item).strip()
            ]
        else:
            normalized[field] = []

    # Defensive source parsing
    raw_sources = raw_output.get("sources", [])
    normalized_sources: list[dict[str, Any]] = []
    if isinstance(raw_sources, list):
        for item in raw_sources:
            try:
                valid_entry = _validate_source_entry(item)
                if valid_entry:
                    normalized_sources.append(valid_entry)
            except Exception:
                pass

    # Map RAG evidence sources to SourceReferences if context contains verified RAG evidence
    rag_evidence = context.get("rag_evidence", []) or []
    for ev in rag_evidence:
        if not isinstance(ev, dict):
            continue
        score = ev.get("score", 0.0)
        # Filter evidence items that meet a baseline similarity score threshold (>= 0.60)
        if isinstance(score, (int, float)) and score >= 0.60:
            src = ev.get("source", {}) if isinstance(ev.get("source"), dict) else {}
            raw_doc_id = src.get("document_id")
            raw_chunk_id = ev.get("chunk_id")

            # Safe scalar validation for ref_id before string coercion
            if raw_doc_id is not None and isinstance(raw_doc_id, (str, int, float)):
                ref_id = str(raw_doc_id).strip()
            elif raw_chunk_id is not None and isinstance(raw_chunk_id, (str, int, float)):
                ref_id = str(raw_chunk_id).strip()
            else:
                try:
                    ref_id = str(raw_doc_id or raw_chunk_id).strip()
                except Exception:
                    ref_id = "rag_doc"
            if not ref_id:
                ref_id = "rag_doc"

            doc_title = src.get("title") or "RAG Document"
            claim_text = f"Retrieved Document Evidence: {doc_title}"
            if not any(s.get("reference_id") == ref_id for s in normalized_sources):
                normalized_sources.append(
                    {
                        "claim": claim_text,
                        "source_type": "document",
                        "reference_id": ref_id,
                    }
                )

    normalized["sources"] = normalized_sources

    # Preserve rag_status and evidence
    normalized["rag_status"] = context.get("rag_status") or raw_output.get("rag_status")
    normalized["evidence"] = context.get("rag_evidence", []) or raw_output.get("evidence", [])

    # Metadata defaults
    lang = str(raw_output.get("language", "en")).lower()
    normalized["language"] = lang if lang in _ALLOWED_LANGUAGES else "en"

    conf = str(raw_output.get("confidence", "unverified")).lower()
    normalized["confidence"] = conf if conf in _ALLOWED_CONFIDENCE else "unverified"

    normalized["model_name"] = str(raw_output.get("model_name") or "unknown-model")
    normalized["prompt_version"] = str(raw_output.get("prompt_version") or "v1")

    # Financial claim validation
    has_verified = len(normalized_sources) > 0 or context.get("rag_status") == "success"
    text_items = [
        normalized["summary"],
        normalized["recommendation"],
        *[
            item
            for field in _LIST_FIELDS
            for item in normalized.get(field, [])
            if isinstance(item, str)
        ],
    ]
    for text in text_items:
        if _contains_invented_financial_claim(text, context, has_verified_sources=has_verified):
            raise ValueError(
                "AI output contains invented financial or subsidy claims not supported by backend context."
            )

    return normalized
