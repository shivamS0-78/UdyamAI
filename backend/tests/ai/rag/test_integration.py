import os
import tempfile
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine

from app.config import settings
from app.models.rag import Document, DocumentChunk
from app.models.scheme import Scheme
from app.rag.document_loader import (
    EncryptedPDFError,
    ScannedPDFError,
    load_document,
    query_rag_pipeline,
)
from app.schemas.rag import RAGQueryResponse

settings.OPENAI_API_KEY = "mock-openai-key-for-testing"
EMBEDDING_DIM = getattr(settings, "EMBEDDING_DIMENSION", 1536)


@pytest.fixture(name="db_session")
def db_session_fixture():
    """In-memory SQLite database session fixture for RAG integration testing."""
    engine = create_engine("sqlite:///:memory:")
    Document.__table__.create(engine)
    Scheme.__table__.create(engine)
    DocumentChunk.__table__.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def temp_pdf_file():
    """Creates a temporary non-empty dummy file for PDF loader testing."""
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, "wb") as f:
        f.write(b"%PDF-1.4 header dummy contents")
    yield path
    if os.path.exists(path):
        os.remove(path)


def _create_vector(val: float, dim: int = EMBEDDING_DIM) -> list[float]:
    return [val] * dim


# --- 1. End-to-End Integration Flow ---


@patch("app.rag.embeddings.get_openai_client")
@patch("app.rag.document_parser.pypdf.PdfReader")
def test_end_to_end_rag_pipeline_integration(
    mock_pdf_reader, mock_get_client, db_session: Session, temp_pdf_file: str
):
    """
    Tests complete pipeline:
    PDF -> parse_pdf -> chunk_document -> generate_embeddings (mocked) -> DB -> retrieve_evidence -> citations -> RAGQueryResponse
    """
    # 1. Mock PDF Reader page text extraction
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = (
        "PMFME Guidelines 2024\nSection 1: Beneficiary contribution is 10% of total project cost."
    )
    mock_reader_inst = MagicMock()
    mock_reader_inst.is_encrypted = False
    mock_reader_inst.pages = [mock_page_1]
    mock_pdf_reader.return_value = mock_reader_inst

    # 2. Mock OpenAI Embeddings API client
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=_create_vector(0.1))]
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    scheme_id = uuid4()
    scheme = Scheme(id=scheme_id, name="PMFME", code="PMFME", active=True)
    db_session.add(scheme)
    db_session.commit()

    # 3. Step A: Load and ingest document
    doc = load_document(
        db=db_session,
        file_path=temp_pdf_file,
        title="PMFME Guidelines 2024",
        scheme_id=scheme_id,
        source_name="Ministry of Food Processing",
        language="en",
    )

    assert doc is not None
    assert doc.title == "PMFME Guidelines 2024"

    # Verify chunks stored in database
    chunks = db_session.query(DocumentChunk).filter_by(document_id=doc.id).all()
    assert len(chunks) > 0
    assert "10%" in chunks[0].content

    # 4. Step B: Query retrieval pipeline
    rag_response: RAGQueryResponse = query_rag_pipeline(
        db=db_session,
        query="What is the contribution requirement under PMFME?",
        scheme_id=scheme_id,
        score_threshold=0.10,
    )

    assert isinstance(rag_response, RAGQueryResponse)
    assert rag_response.status == "success"
    assert len(rag_response.evidence) > 0

    # 5. Step C: Traceability Verification
    item = rag_response.evidence[0]
    assert item.source.document_id == doc.id
    assert item.source.title == "PMFME Guidelines 2024"
    assert item.source.source_name == "Ministry of Food Processing"
    assert item.source.language == "en"
    assert "10%" in item.text


@patch("app.rag.embeddings.get_openai_client")
@patch("app.rag.document_parser.pypdf.PdfReader")
def test_multipage_pdf_ingestion_integration(
    mock_pdf_reader, mock_get_client, db_session: Session, temp_pdf_file: str
):
    """Verifies parsing and chunking multi-page PDF documents across page boundaries."""
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = "Page 1: PMFME Overview and Subsidy Rules."
    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = (
        "Page 2: Eligible Micro Food Enterprises and Documentation."
    )

    mock_reader = MagicMock()
    mock_reader.is_encrypted = False
    mock_reader.pages = [mock_page_1, mock_page_2]
    mock_pdf_reader.return_value = mock_reader

    mock_resp = MagicMock()
    mock_resp.data = [
        MagicMock(embedding=_create_vector(0.1)),
        MagicMock(embedding=_create_vector(0.1)),
    ]
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = mock_resp
    mock_get_client.return_value = mock_client

    doc = load_document(
        db=db_session,
        file_path=temp_pdf_file,
        title="Multi Page Guidelines",
        source_name="MoFPI",
    )

    assert doc is not None
    chunks = (
        db_session.query(DocumentChunk)
        .filter_by(document_id=doc.id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    assert len(chunks) >= 2
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2


@patch("app.rag.document_loader.ingest_document", return_value=None)
def test_load_document_duplicate_returns_none(mock_ingest, db_session: Session, temp_pdf_file: str):
    """Verifies load_document returns None when ingest_document skips duplicate document hash."""
    result = load_document(db=db_session, file_path=temp_pdf_file, title="Duplicate Doc")
    assert result is None
    mock_ingest.assert_called_once()


# --- 2. Error Propagation Integration Tests ---


def test_load_document_nonexistent_file(db_session: Session):
    with pytest.raises(FileNotFoundError, match="File not found"):
        load_document(db=db_session, file_path="non_existent_file.pdf", title="Test")


def test_load_document_empty_path(db_session: Session):
    with pytest.raises(ValueError, match="File path must be a non-empty string"):
        load_document(db=db_session, file_path="", title="Test")


@patch("app.rag.document_parser.pypdf.PdfReader")
def test_load_document_scanned_pdf(mock_pdf_reader, db_session: Session, temp_pdf_file: str):
    """Verifies ScannedPDFError is propagated when PDF contains no extractable text."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    mock_reader = MagicMock()
    mock_reader.is_encrypted = False
    mock_reader.pages = [mock_page]
    mock_pdf_reader.return_value = mock_reader

    with pytest.raises(ScannedPDFError, match="scanned or image-only"):
        load_document(db=db_session, file_path=temp_pdf_file, title="Scanned PDF Test")


@patch("app.rag.document_parser.pypdf.PdfReader")
def test_load_document_encrypted_pdf(mock_pdf_reader, db_session: Session, temp_pdf_file: str):
    """Verifies EncryptedPDFError is propagated when PDF is password protected."""
    mock_reader = MagicMock()
    mock_reader.is_encrypted = True
    mock_pdf_reader.return_value = mock_reader

    with pytest.raises(EncryptedPDFError, match="encrypted"):
        load_document(db=db_session, file_path=temp_pdf_file, title="Encrypted PDF Test")


# --- 3. PostgreSQL / pgvector Integration Marker Test ---


@pytest.mark.postgresql_integration
def test_pgvector_native_cosine_search():
    """
    Placeholder marker test for native PostgreSQL + pgvector cosine similarity search.
    Requires an active PostgreSQL database instance with pgvector extension enabled.
    """
    pass
