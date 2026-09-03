from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import UserDefinedType

    class Vector(UserDefinedType):
        def __init__(self, dim=None):
            self.dim = dim

        def get_col_spec(self, **kw):
            return f"VECTOR({self.dim})" if self.dim else "VECTOR"


if TYPE_CHECKING:
    from app.models.scheme import Scheme, SchemeEligibilityRule, SchemeRule


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=255, nullable=False)
    source_name: str = Field(max_length=255, nullable=False)
    source_url: str | None = Field(default=None)
    document_type: str = Field(max_length=100, nullable=False)

    language: str = Field(default="hi", max_length=10)
    file_path: str | None = Field(default=None)

    published_date: date | None = Field(default=None)
    effective_from: date | None = Field(default=None)
    effective_until: date | None = Field(default=None)

    last_verified_at: datetime | None = Field(default=None)
    content_hash: str = Field(max_length=64, unique=True, index=True, nullable=False)
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    chunks: list["DocumentChunk"] = Relationship(
        back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    scheme_rules: list["SchemeRule"] = Relationship(back_populates="source_document")
    scheme_eligibility_rules: list["SchemeEligibilityRule"] = Relationship(
        back_populates="source_document"
    )


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_index",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(foreign_key="documents.id", nullable=False, index=True)
    scheme_id: UUID | None = Field(default=None, foreign_key="schemes.id", nullable=True)

    chunk_index: int = Field(nullable=False)
    content: str = Field(nullable=False)
    page_number: int | None = Field(default=None)
    section_title: str | None = Field(default=None)

    # pgvector embedding field (1536 dimensions for OpenAI ada-002)
    embedding: list[float] | None = Field(
        default=None, sa_column=Column("embedding", Vector(1536), nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    document: Document = Relationship(back_populates="chunks")
    scheme: Optional["Scheme"] = Relationship(back_populates="document_chunks")
