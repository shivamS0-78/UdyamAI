import logging

from app.models.rag import Document, DocumentChunk
from app.schemas.rag import EvidenceItem, SourceMetadata

logger = logging.getLogger(__name__)


def build_source_metadata(document: Document, chunk: DocumentChunk) -> SourceMetadata:
    """
    Constructs a traceable SourceMetadata object from a Document and DocumentChunk.

    Args:
        document: The parent Document database model.
        chunk: The DocumentChunk database model.

    Returns:
        SourceMetadata object matching rag-contract.md.
    """
    return SourceMetadata(
        document_id=document.id,
        title=document.title,
        page_number=chunk.page_number,
        section_title=chunk.section_title,
        source_name=document.source_name,
        source_url=document.source_url,
        language=document.language,
        version=getattr(document, "document_version", None),
        effective_from=document.effective_from,
        effective_until=document.effective_until,
    )


def format_evidence_item(chunk: DocumentChunk, document: Document, score: float) -> EvidenceItem:
    """
    Formats a chunk, parent document, and similarity score into a structured EvidenceItem.

    Args:
        chunk: The DocumentChunk database model.
        document: The parent Document database model.
        score: Computed similarity score (0.0 to 1.0).

    Returns:
        Structured EvidenceItem matching rag-contract.md.
    """
    source_meta = build_source_metadata(document, chunk)
    return EvidenceItem(
        chunk_id=chunk.id,
        text=chunk.content,
        score=round(float(score), 6),
        source=source_meta,
    )
