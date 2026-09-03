from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class RAGStatus(str, Enum):  # noqa: UP042
    """Enumeration of standard RAG evidence retrieval status codes."""

    SUCCESS = "success"
    NO_RELEVANT_EVIDENCE = "no_relevant_evidence"
    CONFLICTING_SOURCES = "conflicting_sources"
    EMBEDDING_GENERATION_FAILED = "embedding_generation_failed"


class DocumentCreate(BaseModel):
    """Schema for creating a new RAG document."""

    title: str = Field(..., min_length=1, max_length=255)
    source_name: str = Field(..., min_length=1, max_length=255)
    source_url: str | None = Field(default=None, max_length=500)
    document_type: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="hi", max_length=10)
    file_path: str | None = Field(default=None, max_length=500)
    published_date: date | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    last_verified_at: datetime | None = None
    content_hash: str = Field(..., min_length=1, max_length=64)
    active: bool = True


class DocumentRead(BaseModel):
    """Schema for reading a RAG document."""

    id: UUID
    title: str
    source_name: str
    source_url: str | None = None
    document_type: str
    language: str
    file_path: str | None = None
    published_date: date | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    last_verified_at: datetime | None = None
    content_hash: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChunkCreate(BaseModel):
    """Schema for creating a document chunk."""

    document_id: UUID
    scheme_id: UUID | None = None
    chunk_index: int = Field(..., ge=0)
    content: str = Field(..., min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    section_title: str | None = Field(default=None, max_length=255)
    embedding: list[float] | None = Field(
        default=None, description="Vector embedding (1536 dimensions for OpenAI ada-002)"
    )


class ChunkRead(BaseModel):
    """Schema for reading a document chunk."""

    id: UUID
    document_id: UUID
    scheme_id: UUID | None = None
    chunk_index: int
    content: str
    page_number: int | None = None
    section_title: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RAGQueryRequest(BaseModel):
    """Input contract schema for RAG evidence retrieval."""

    query: str = Field(
        ..., min_length=1, description="Search query derived from user business context."
    )
    scheme_id: UUID | None = Field(default=None, description="Optional filter by scheme ID.")
    language: str | None = Field(
        default=None, description="Optional language filter (e.g., 'en', 'hi', 'mr')."
    )
    limit: int = Field(
        default=5, ge=1, le=50, description="Maximum number of evidence chunks to retrieve."
    )
    score_threshold: float = Field(
        default=0.70, ge=0.0, le=1.0, description="Minimum similarity score threshold."
    )
    effective_date: date | None = Field(
        default=None, description="Optional effective date filter for document versioning."
    )


class SourceMetadata(BaseModel):
    """Source metadata structure embedded in each evidence chunk response."""

    document_id: UUID
    title: str
    page_number: int | None = None
    section_title: str | None = None
    source_name: str
    source_url: str | None = None
    language: str = "hi"
    version: str | None = None
    effective_from: date | None = None
    effective_until: date | None = None

    model_config = {"from_attributes": True}


class EvidenceItem(BaseModel):
    """Individual retrieved evidence chunk item."""

    chunk_id: UUID
    text: str
    score: float
    source: SourceMetadata


class RAGQueryResponse(BaseModel):
    """Output contract schema for RAG evidence retrieval."""

    status: RAGStatus | str = Field(
        ...,
        description=(
            "Retrieval status: 'success', 'no_relevant_evidence', 'conflicting_sources', "
            "or 'embedding_generation_failed'."
        ),
    )
    evidence: list[EvidenceItem] = Field(
        default_factory=list, description="List of verified evidence items."
    )
