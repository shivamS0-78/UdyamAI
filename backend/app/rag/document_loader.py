import logging
import os
from uuid import UUID

from sqlmodel import Session

from app.models.rag import Document
from app.rag.document_parser import (
    CorruptedPDFError,
    EmptyPDFError,
    EncryptedPDFError,
    PDFParserError,
    ScannedPDFError,
)
from app.rag.knowledge_base import ingest_document
from app.rag.retriever import retrieve_evidence
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse

logger = logging.getLogger(__name__)

# Supported ISO 639-1 language codes for document ingestion
VALID_LANGUAGES = {"en", "hi", "te", "ta", "ka", "mr", "gu", "bn", "pa", "ml", "kn", "or"}

# Re-export exceptions for convenience
__all__ = [
    "load_document",
    "query_rag_pipeline",
    "PDFParserError",
    "CorruptedPDFError",
    "EncryptedPDFError",
    "EmptyPDFError",
    "ScannedPDFError",
    "VALID_LANGUAGES",
]


def load_document(
    db: Session,
    file_path: str,
    title: str,
    scheme_id: UUID | None = None,
    source_name: str = "Official Department",
    source_url: str | None = None,
    document_type: str = "scheme_guideline",
    language: str = "en",
    document_version: str | None = None,
) -> Document | None:
    """
    Validates PDF file existence, ISO language, and readability, then ingests document into RAG knowledge base.
    Remote OpenAI embedding calls execute outside DB transactions to prevent lock contention.

    Args:
        db: Active SQLModel database session.
        file_path: Absolute or relative local path to PDF file.
        title: Document title.
        scheme_id: Optional scheme UUID.
        source_name: Official publisher or department name.
        source_url: Reference URL for source document.
        document_type: Category of document (e.g. scheme_guideline).
        language: ISO language code (default 'en').
        document_version: Version identifier string.

    Returns:
        Ingested Document model, or None if skipped (e.g., duplicate content hash).

    Raises:
        FileNotFoundError: If file path does not exist.
        PermissionError: If file path is not readable.
        ValueError: If parameters, language, or file are invalid.
        CorruptedPDFError: If PDF structure is corrupted.
        EncryptedPDFError: If PDF is password protected.
        EmptyPDFError: If PDF is empty or 0 bytes.
        ScannedPDFError: If PDF contains no extractable text.
    """
    if file_path is None or not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("File path must be a non-empty string.")

    if language not in VALID_LANGUAGES:
        raise ValueError(
            f"Unsupported language code: '{language}'. Supported: {sorted(VALID_LANGUAGES)}"
        )

    file_path_str = file_path.strip()

    if not os.path.exists(file_path_str):
        raise FileNotFoundError(f"File not found: {file_path_str}")

    if not os.path.isfile(file_path_str):
        raise ValueError(f"Path is not a regular file: {file_path_str}")

    if not os.access(file_path_str, os.R_OK):
        raise PermissionError(f"File is not readable: {file_path_str}")

    logger.info(f"Initiating document_loader pipeline for '{title}' from path: {file_path_str}")

    # Calls existing ingestion pipeline (executes remote API call outside DB transaction)
    return ingest_document(
        db=db,
        file_path=file_path_str,
        title=title,
        scheme_id=scheme_id,
        source_name=source_name,
        source_url=source_url,
        document_type=document_type,
        language=language,
        document_version=document_version,
    )


def query_rag_pipeline(
    db: Session,
    query: str | RAGQueryRequest,
    scheme_id: UUID | None = None,
    language: str | None = None,
    limit: int | None = None,
    score_threshold: float | None = None,
) -> RAGQueryResponse:
    """
    Convenience pipeline function executing end-to-end RAG evidence retrieval and citation formatting.

    Args:
        db: Active SQLModel database session.
        query: Search query or RAGQueryRequest model.
        scheme_id: Optional scheme filter.
        language: Optional language filter.
        limit: Max top_k evidence items to retrieve.
        score_threshold: Minimum similarity threshold.

    Returns:
        RAGQueryResponse containing status and verified citations.
    """
    logger.info("Executing end-to-end RAG query pipeline...")
    return retrieve_evidence(
        db=db,
        query=query,
        scheme_id=scheme_id,
        language=language,
        limit=limit,
        score_threshold=score_threshold,
    )
