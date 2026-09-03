import logging
import re
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.models.scheme import Scheme
from app.rag.retriever import retrieve_evidence
from app.schemas.rag import RAGQueryResponse

logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def _compile_metric_pattern(metric: str) -> re.Pattern:
    """Compiles metric regex pattern with smart word boundaries for alphanumeric boundary ends."""
    m = metric.strip()
    escaped = re.escape(m)

    has_word_start = bool(re.match(r"^[a-zA-Z0-9]", m))
    has_word_end = bool(re.search(r"[a-zA-Z0-9]$", m))

    prefix = r"\b" if has_word_start else ""
    suffix = r"\b" if has_word_end else ""

    return re.compile(prefix + escaped + suffix, re.IGNORECASE)


def _is_metric_in_text(metric: str, text: str) -> bool:
    """Checks if metric string is present in text using cached boundary patterns or currency string match."""
    if not metric or not isinstance(metric, str) or not metric.strip() or not text:
        return False
    m = metric.strip()
    if any(c in m for c in "₹$€"):
        return m.lower() in text.lower()
    pattern = _compile_metric_pattern(m)
    return bool(pattern.search(text))


def _detect_conflicting_values(retrieved_items: list[Any], ground_truth_metrics: list[str]) -> bool:
    """Returns True if multiple distinct document sources present conflicting metric values."""
    if not retrieved_items or not ground_truth_metrics:
        return False

    source_values: dict[str, set[str]] = {}
    for ev in retrieved_items:
        source_id = str(getattr(ev.source, "document_id", ev.source.source_name))
        for m in ground_truth_metrics:
            if _is_metric_in_text(m, ev.text):
                if source_id not in source_values:
                    source_values[source_id] = set()
                source_values[source_id].add(m)

    return len(source_values) >= 2


class QueryEvaluationDetail(BaseModel):
    """Detailed evaluation result for a single query."""

    query_id: str
    query: str
    expected_status: str
    actual_status: str
    status_match: bool
    recall: float
    precision: float
    retrieved_count: int
    error_message: str | None = None


class EvaluationReport(BaseModel):
    """Aggregate benchmark report containing Recall@K, Precision@K, and Status Accuracy."""

    total_queries: int
    top_k: int
    recall_at_k: float = Field(
        description="Average Recall@K score across evaluated queries (0.0 to 1.0)."
    )
    precision_at_k: float = Field(
        description="Average Precision@K score across evaluated queries (0.0 to 1.0)."
    )
    status_accuracy: float = Field(
        description="Proportion of queries matching expected response status (0.0 to 1.0)."
    )
    successful_matches: int
    missing_evidence_matches: int
    conflicting_source_matches: int
    query_details: list[QueryEvaluationDetail] = Field(default_factory=list)


def evaluate_retrieval(
    db: Session,
    eval_dataset: list[dict[str, Any]],
    top_k: int = 5,
    score_threshold: float = 0.50,
) -> EvaluationReport:
    """
    Evaluates RAG retrieval performance using Recall@K, Precision@K, and Status Accuracy.

    Features:
    - Metric-grounded recall: counts matched ground-truth metrics / total metrics
    - Multi-source conflict detection: identifies contradictory values across documents
    - Scheme resolution: exact match first, then case-insensitive fallback
    - Graceful error handling: catches retrieval exceptions and logs them

    Args:
        db: Active SQLModel database session containing indexed documents and chunks.
        eval_dataset: List of test case dictionaries from dataset.py.
        top_k: Max chunks retrieved per query.
        score_threshold: Minimum cosine similarity score (0.50 corresponds to ~60° angular similarity cutoff).

    Returns:
        Structured EvaluationReport.

    Raises:
        None - exceptions are caught and reported in results.
    """
    if not eval_dataset:
        return EvaluationReport(
            total_queries=0,
            top_k=top_k,
            recall_at_k=0.0,
            precision_at_k=0.0,
            status_accuracy=0.0,
            successful_matches=0,
            missing_evidence_matches=0,
            conflicting_source_matches=0,
            query_details=[],
        )

    logger.info(f"Starting RAG retrieval evaluation over {len(eval_dataset)} test queries...")

    total_queries = len(eval_dataset)
    recalls: list[float] = []
    precisions: list[float] = []
    status_matches = 0
    successful_matches = 0
    missing_matches = 0
    conflicting_matches = 0
    details: list[QueryEvaluationDetail] = []

    for item in eval_dataset:
        q_id = item.get("id", "unknown")
        query_str = item["query"]
        expected_status = item.get("expected_status", "success")
        expected_doc = item.get("expected_document_title")
        expected_sec = item.get("expected_section")
        gt_metrics = [
            str(m).strip()
            for m in item.get("ground_truth_metrics", [])
            if m is not None and str(m).strip()
        ]
        is_missing = item.get("is_missing", False)
        is_conflicting = item.get("is_conflicting", False)

        # Precise scheme resolution
        scheme_id = item.get("scheme_id")
        if not scheme_id and item.get("scheme_name") and item["scheme_name"] != "Unknown":
            scheme_name = item["scheme_name"]
            statement = select(Scheme).where(Scheme.name == scheme_name)
            scheme_obj = db.exec(statement).first()
            if not scheme_obj:
                statement_like = select(Scheme).where(Scheme.name.ilike(f"%{scheme_name}%"))
                scheme_obj = db.exec(statement_like).first()

            if scheme_obj:
                scheme_id = scheme_obj.id
            else:
                logger.warning(
                    f"Scheme '{scheme_name}' not found in database for query '{q_id}'. Executing retrieval without scheme filter."
                )

        # Query retrieval execution
        try:
            response: RAGQueryResponse = retrieve_evidence(
                db=db,
                query=query_str,
                scheme_id=scheme_id,
                limit=top_k,
                score_threshold=score_threshold,
            )
            actual_status = response.status
            retrieved_items = response.evidence
            error_msg = None
        except Exception as err:
            logger.error(f"Error executing retrieval for query '{q_id}': {str(err)}", exc_info=True)
            actual_status = "retrieval_failed"
            retrieved_items = []
            error_msg = str(err)

        is_status_correct = actual_status == expected_status
        if is_status_correct:
            status_matches += 1
            if expected_status == "success":
                successful_matches += 1
            elif expected_status == "no_relevant_evidence":
                missing_matches += 1
            elif expected_status == "conflicting_sources":
                conflicting_matches += 1

        # Multi-source validation for conflict test cases
        if is_conflicting and actual_status == "conflicting_sources":
            has_multi_source_conflict = _detect_conflicting_values(retrieved_items, gt_metrics)
            if not has_multi_source_conflict and len(retrieved_items) > 1:
                logger.debug(
                    f"Query '{q_id}': Expected conflicting_sources but found compatible values across sources."
                )

        # Metric-grounded Recall@K & Precision@K calculations
        if is_missing or expected_status == "no_relevant_evidence":
            if actual_status == "no_relevant_evidence" and len(retrieved_items) == 0:
                q_recall = 1.0
                q_precision = 1.0
            else:
                q_recall = 0.0
                q_precision = 0.0
        elif actual_status == "retrieval_failed":
            q_recall = 0.0
            q_precision = 0.0
        else:
            if not retrieved_items:
                q_recall = 0.0
                q_precision = 0.0
            else:
                # Check ground-truth metric ratio for Recall
                if gt_metrics:
                    matched_gt_count = 0
                    for m in gt_metrics:
                        if any(_is_metric_in_text(m, ev.text) for ev in retrieved_items):
                            matched_gt_count += 1
                    q_recall = matched_gt_count / len(gt_metrics)
                else:
                    doc_sec_match = any(
                        (
                            expected_doc
                            and ev.source
                            and getattr(ev.source, "title", None)
                            and expected_doc.lower() in str(ev.source.title).lower()
                        )
                        or (
                            expected_sec
                            and ev.source
                            and getattr(ev.source, "section_title", None)
                            and expected_sec.lower() in str(ev.source.section_title).lower()
                        )
                        for ev in retrieved_items
                    )
                    q_recall = 1.0 if doc_sec_match else 0.0

                # Precision calculation over retrieved items
                relevant_retrieved = 0
                for ev in retrieved_items:
                    doc_title_match = (
                        expected_doc
                        and ev.source
                        and getattr(ev.source, "title", None)
                        and (expected_doc.lower() in str(ev.source.title).lower())
                    )
                    sec_title_match = (
                        expected_sec
                        and ev.source
                        and getattr(ev.source, "section_title", None)
                        and (expected_sec.lower() in str(ev.source.section_title).lower())
                    )
                    metric_match = (
                        any(_is_metric_in_text(m, ev.text) for m in gt_metrics)
                        if gt_metrics
                        else False
                    )

                    if doc_title_match or sec_title_match or metric_match:
                        relevant_retrieved += 1

                q_precision = relevant_retrieved / len(retrieved_items)

        recalls.append(q_recall)
        precisions.append(q_precision)

        details.append(
            QueryEvaluationDetail(
                query_id=q_id,
                query=query_str,
                expected_status=expected_status,
                actual_status=actual_status,
                status_match=is_status_correct,
                recall=round(q_recall, 4),
                precision=round(q_precision, 4),
                retrieved_count=len(retrieved_items),
                error_message=error_msg,
            )
        )

    avg_recall = sum(recalls) / total_queries if total_queries > 0 else 0.0
    avg_precision = sum(precisions) / total_queries if total_queries > 0 else 0.0
    accuracy = status_matches / total_queries if total_queries > 0 else 0.0

    report = EvaluationReport(
        total_queries=total_queries,
        top_k=top_k,
        recall_at_k=round(avg_recall, 4),
        precision_at_k=round(avg_precision, 4),
        status_accuracy=round(accuracy, 4),
        successful_matches=successful_matches,
        missing_evidence_matches=missing_matches,
        conflicting_source_matches=conflicting_matches,
        query_details=details,
    )

    logger.info(
        f"RAG Evaluation complete. Recall@{top_k}={report.recall_at_k}, "
        f"Precision@{top_k}={report.precision_at_k}, StatusAccuracy={report.status_accuracy}"
    )

    return report
