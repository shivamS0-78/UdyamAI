import logging
import math
import re
from datetime import date
from uuid import UUID

from sqlmodel import Session, select

from app.config import settings
from app.models.rag import Document, DocumentChunk
from app.rag.citations import format_evidence_item
from app.rag.embeddings import generate_embedding
from app.schemas.rag import EvidenceItem, RAGQueryRequest, RAGQueryResponse

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 2000
EXPECTED_EMBEDDING_DIMENSION = 1536


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Computes cosine similarity between two float vectors.
    Includes strict dimension checks and NaN/Infinity safety guards.
    """
    if not vec_a or not vec_b:
        return 0.0

    if len(vec_a) != len(vec_b):
        logger.warning(
            f"Vector dimension mismatch in similarity calculation: {len(vec_a)} vs {len(vec_b)}."
        )
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    score = dot_product / (norm_a * norm_b)

    if math.isnan(score) or math.isinf(score):
        logger.warning(f"Invalid (NaN/Inf) similarity score computed: {score}. Returning 0.0.")
        return 0.0

    return score


def _is_policy_metric(text: str) -> bool:
    """Checks if an extracted metric text looks policy-relevant (excluding pure years, dates, or version strings)."""
    cleaned = text.strip()
    if not cleaned:
        return False
    # Skip pure 4-digit years (e.g. 2023, 2024)
    if re.match(r"^\d{4}$", cleaned):
        return False
    # Skip dates like 01/01/2024 or 2024-01-01
    if re.match(r"^\d{1,4}[./-]\d{1,2}[./-]\d{1,4}$", cleaned):
        return False
    # Skip version numbers like v1.0 or v2.1
    if re.match(r"^v?\d+\.\d+$", cleaned, re.IGNORECASE):
        return False
    return True


def _detect_metric_conflicts(chunk_doc_tuples: list[tuple[DocumentChunk, Document]]) -> bool:
    """
    Detects whether chunks from multiple distinct active documents for the SAME scheme
    contain conflicting numeric metrics (e.g., mismatched percentages, interest rates, or loan limits).
    """
    if len(chunk_doc_tuples) < 2:
        return False

    # Group chunk-doc tuples by scheme_id
    scheme_groups: dict[UUID | None, list[tuple[DocumentChunk, Document]]] = {}
    for chunk, doc in chunk_doc_tuples:
        s_id = chunk.scheme_id
        if s_id not in scheme_groups:
            scheme_groups[s_id] = []
        scheme_groups[s_id].append((chunk, doc))

    for s_id, group in scheme_groups.items():
        if len(group) < 2:
            continue

        # Group extracted metrics by document_id within this scheme
        doc_metrics: dict[UUID, set[str]] = {}
        for chunk, doc in group:
            raw_matches = re.findall(
                r"\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\s*(?:percent|lakh|crore)s?\b|₹\s*\d+(?:\.\d+)?",
                chunk.content,
                flags=re.IGNORECASE,
            )
            found_metrics = set(m for m in raw_matches if _is_policy_metric(m))
            if found_metrics:
                if doc.id not in doc_metrics:
                    doc_metrics[doc.id] = set()
                doc_metrics[doc.id].update(found_metrics)

        if len(doc_metrics) >= 2:
            all_metric_sets = list(doc_metrics.values())
            first_set = all_metric_sets[0]
            for other_set in all_metric_sets[1:]:
                if first_set and other_set and first_set.isdisjoint(other_set):
                    has_numeric_first = any(re.search(r"\d", m) for m in first_set)
                    has_numeric_other = any(re.search(r"\d", m) for m in other_set)
                    if has_numeric_first and has_numeric_other:
                        logger.info(
                            f"Conflict detected between active documents for scheme '{s_id}': "
                            f"{first_set} vs {other_set}"
                        )
                        return True

    return False


def retrieve_evidence(
    db: Session,
    query: str | RAGQueryRequest,
    scheme_id: UUID | None = None,
    language: str | None = None,
    limit: int | None = None,
    score_threshold: float | None = None,
    effective_date: date | None = None,
) -> RAGQueryResponse:
    """
    Retrieves verified evidence chunks from pgvector/PostgreSQL matching query & metadata filters.

    Args:
        db: Active SQLModel/SQLAlchemy Session.
        query: Search query string or RAGQueryRequest schema.
        scheme_id: Optional scheme filter.
        language: Optional language filter.
        limit: Max number of evidence chunks to return (default: settings.RAG_DEFAULT_TOP_K).
        score_threshold: Min similarity score required (default: settings.RAG_DEFAULT_SCORE_THRESHOLD).
        effective_date: Optional date filter for document version applicability.

    Returns:
        RAGQueryResponse with status ('success', 'no_relevant_evidence', 'conflicting_sources', 'embedding_generation_failed')
        and evidence items.
    """
    if isinstance(query, RAGQueryRequest):
        req = query
        query_str = req.query
        scheme_id = req.scheme_id if scheme_id is None else scheme_id
        language = req.language if language is None else language
        limit = req.limit if limit is None else limit
        score_threshold = req.score_threshold if score_threshold is None else score_threshold
        effective_date = req.effective_date if effective_date is None else effective_date
    else:
        query_str = query

    if not query_str or not query_str.strip():
        raise ValueError("Query string cannot be empty or whitespace-only.")

    query_str = query_str.strip()

    if len(query_str) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query exceeds max length of {MAX_QUERY_LENGTH} characters.")

    top_k = limit if limit is not None else settings.RAG_DEFAULT_TOP_K
    threshold = (
        score_threshold if score_threshold is not None else settings.RAG_DEFAULT_SCORE_THRESHOLD
    )

    logger.info(
        f"Executing RAG retrieval for query='{query_str[:40]}...', scheme_id={scheme_id}, "
        f"language={language}, limit={top_k}, score_threshold={threshold}"
    )

    # 1. Generate query embedding using existing embedding module with robust exception handling
    try:
        query_vector = generate_embedding(query_str)
    except ValueError as e:
        logger.error(f"Embedding validation failed: {str(e)}")
        return RAGQueryResponse(status="embedding_generation_failed", evidence=[])
    except Exception as e:
        logger.error(f"Unexpected error during embedding generation: {str(e)}")
        return RAGQueryResponse(status="embedding_generation_failed", evidence=[])

    if not query_vector or len(query_vector) != EXPECTED_EMBEDDING_DIMENSION:
        logger.error(
            f"Invalid query vector received: dimension={len(query_vector) if query_vector else 0}, "
            f"expected {EXPECTED_EMBEDDING_DIMENSION}."
        )
        return RAGQueryResponse(status="embedding_generation_failed", evidence=[])

    # 2. Build base SQL query joining DocumentChunk and Document
    stmt = (
        select(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.active == True)  # noqa: E712
    )

    # Apply scheme_id filter if provided
    if scheme_id is not None:
        stmt = stmt.where(DocumentChunk.scheme_id == scheme_id)

    # Apply language filter if provided
    if language is not None:
        stmt = stmt.where(Document.language == language)

    # Apply effective date filter if provided
    if effective_date is not None:
        stmt = stmt.where(
            (Document.effective_from.is_(None)) | (Document.effective_from <= effective_date),
            (Document.effective_until.is_(None)) | (Document.effective_until >= effective_date),
        )

    results = db.exec(stmt).all()

    if not results:
        logger.info("No active documents matched the requested metadata filters.")
        return RAGQueryResponse(status="no_relevant_evidence", evidence=[])

    # Exclude documents with invalid/inverted effective dates
    bad_doc_ids: set[UUID] = set()
    for _, doc in results:
        if doc.effective_from and doc.effective_until and doc.effective_from > doc.effective_until:
            logger.error(
                f"Document '{doc.id}' ({doc.title}) has invalid/inverted date range "
                f"({doc.effective_from} > {doc.effective_until}). Excluding from retrieval results."
            )
            bad_doc_ids.add(doc.id)

    if bad_doc_ids:
        results = [(c, d) for c, d in results if d.id not in bad_doc_ids]
        if not results:
            logger.warning("All matching documents excluded due to invalid effective date ranges.")
            return RAGQueryResponse(status="no_relevant_evidence", evidence=[])

    # 3. Calculate similarity score for each candidate chunk and apply score threshold
    scored_candidates: list[tuple[DocumentChunk, Document, float]] = []
    skipped_count = 0
    invalid_dim_count = 0

    for chunk, doc in results:
        if not chunk.embedding:
            skipped_count += 1
            logger.debug(f"Skipping chunk {chunk.id}: missing vector embedding.")
            continue

        if len(chunk.embedding) != EXPECTED_EMBEDDING_DIMENSION:
            invalid_dim_count += 1
            logger.warning(
                f"Skipping chunk {chunk.id}: embedding dimension {len(chunk.embedding)} "
                f"!= expected {EXPECTED_EMBEDDING_DIMENSION}."
            )
            continue

        score = _cosine_similarity(chunk.embedding, query_vector)
        if score >= threshold:
            scored_candidates.append((chunk, doc, score))

    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} chunks due to missing embeddings.")
    if invalid_dim_count > 0:
        logger.warning(f"Skipped {invalid_dim_count} chunks due to vector dimension mismatch.")

    if not scored_candidates:
        logger.info(f"No evidence chunks satisfied similarity threshold ({threshold}).")
        return RAGQueryResponse(status="no_relevant_evidence", evidence=[])

    # 4. Sort by relevance score descending
    scored_candidates.sort(key=lambda item: item[2], reverse=True)

    # 5. Check for genuine conflicts across active documents of the same scheme
    chunk_doc_pairs = [(c, d) for c, d, _ in scored_candidates]
    is_conflicting = _detect_metric_conflicts(chunk_doc_pairs)
    status = "conflicting_sources" if is_conflicting else "success"

    # 6. Take top_k items and build EvidenceItems
    top_candidates = scored_candidates[:top_k]
    evidence_items: list[EvidenceItem] = [
        format_evidence_item(chunk, doc, score) for chunk, doc, score in top_candidates
    ]

    if len(evidence_items) < top_k:
        logger.info(
            f"Retrieved {len(evidence_items)} items, less than requested top_k limit of {top_k}."
        )

    logger.info(
        f"RAG retrieval finished. Status='{status}', retrieved {len(evidence_items)} items."
    )
    return RAGQueryResponse(status=status, evidence=evidence_items)
