"""
RAG Evaluation Package — Dataset and Metrics Evaluator for Recall@K, Precision@K, and Status Accuracy.
"""

from app.rag.evaluation.dataset import EVALUATION_DATASET
from app.rag.evaluation.evaluator import EvaluationReport, evaluate_retrieval

__all__ = ["EVALUATION_DATASET", "EvaluationReport", "evaluate_retrieval"]
