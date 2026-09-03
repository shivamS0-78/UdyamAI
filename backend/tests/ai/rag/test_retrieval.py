from datetime import date
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine

from app.config import settings
from app.models.rag import Document, DocumentChunk
from app.models.scheme import Scheme
from app.rag.citations import build_source_metadata, format_evidence_item
from app.rag.document_loader import load_document, query_rag_pipeline
from app.rag.retriever import retrieve_evidence
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse

settings.OPENAI_API_KEY = "mock-openai-key-for-testing"


@pytest.fixture(name="db_session")
def db_session_fixture():
    """In-memory SQLite database session fixture for testing RAG retrieval."""
    engine = create_engine("sqlite:///:memory:")
    Document.__table__.create(engine)
    Scheme.__table__.create(engine)
    DocumentChunk.__table__.create(engine)
    with Session(engine) as session:
        yield session


def _create_vector(val: float) -> list[float]:
    """Helper to generate a 1536-dim vector filled with val."""
    return [val] * 1536


@pytest.fixture
def sample_documents(db_session: Session):
    """Creates sample documents and chunks in the test database."""
    scheme_a_id = uuid4()
    scheme_b_id = uuid4()

    scheme_a = Scheme(id=scheme_a_id, name="PMFME Scheme", code="PMFME", active=True)
    scheme_b = Scheme(id=scheme_b_id, name="PMEGP Scheme", code="PMEGP", active=True)
    db_session.add(scheme_a)
    db_session.add(scheme_b)

    doc_1 = Document(
        id=uuid4(),
        title="PMFME Official Guidelines 2024",
        source_name="Ministry of Food Processing",
        source_url="https://mofpi.gov.in/pmfme",
        document_type="guideline",
        language="en",
        content_hash="hash_doc_1",
        active=True,
        effective_from=date(2024, 1, 1),
        effective_until=None,
    )

    doc_2 = Document(
        id=uuid4(),
        title="PMEGP Guidelines 2023",
        source_name="KVIC",
        source_url="https://kvic.gov.in/pmegp",
        document_type="guideline",
        language="hi",
        content_hash="hash_doc_2",
        active=True,
        effective_from=date(2023, 1, 1),
        effective_until=date(2023, 12, 31),
    )

    db_session.add(doc_1)
    db_session.add(doc_2)
    db_session.flush()

    chunk_1 = DocumentChunk(
        id=uuid4(),
        document_id=doc_1.id,
        scheme_id=scheme_a_id,
        chunk_index=0,
        content="Beneficiary contribution under PMFME is 10% of project cost up to ₹10 lakh.",
        page_number=14,
        section_title="Funding Pattern",
        embedding=_create_vector(0.1),
    )

    chunk_2 = DocumentChunk(
        id=uuid4(),
        document_id=doc_1.id,
        scheme_id=scheme_a_id,
        chunk_index=1,
        content="Eligible applicants include micro food processing units and SHGs.",
        page_number=15,
        section_title="Eligibility",
        embedding=_create_vector(0.1),
    )

    chunk_3 = DocumentChunk(
        id=uuid4(),
        document_id=doc_2.id,
        scheme_id=scheme_b_id,
        chunk_index=0,
        content="Margin money subsidy under PMEGP is 25% for general category.",
        page_number=5,
        section_title="Financial Assistance",
        embedding=_create_vector(0.05),
    )

    db_session.add(chunk_1)
    db_session.add(chunk_2)
    db_session.add(chunk_3)
    db_session.commit()

    return {
        "scheme_a_id": scheme_a_id,
        "scheme_b_id": scheme_b_id,
        "doc_1": doc_1,
        "doc_2": doc_2,
        "chunk_1": chunk_1,
        "chunk_2": chunk_2,
        "chunk_3": chunk_3,
    }


# --- 1. Success & Top_K Tests ---


@patch("app.rag.retriever.generate_embedding")
def test_retrieve_evidence_success_and_top_k(
    mock_gen_embedding, db_session: Session, sample_documents
):
    mock_gen_embedding.return_value = _create_vector(0.1)

    response = retrieve_evidence(
        db=db_session,
        query="What is the contribution requirement?",
        limit=2,
        score_threshold=0.50,
    )

    assert isinstance(response, RAGQueryResponse)
    assert response.status == "success"
    assert len(response.evidence) <= 2
    assert response.evidence[0].score >= response.evidence[-1].score


# --- 2. Score Threshold Filtering ---


@patch("app.rag.retriever.generate_embedding")
def test_retrieve_evidence_score_threshold(
    mock_gen_embedding, db_session: Session, sample_documents
):
    # Vector with different values yielding lower similarity (e.g., ~0.5)
    diff_vector = [0.1 if i % 2 == 0 else -0.1 for i in range(1536)]
    mock_gen_embedding.return_value = diff_vector

    # High threshold (0.95) should exclude lower matching vectors
    response = retrieve_evidence(
        db=db_session,
        query="PMFME contribution query",
        score_threshold=0.95,
    )

    assert response.status == "no_relevant_evidence"
    assert len(response.evidence) == 0


# --- 3. Scheme ID Filtering ---


@patch("app.rag.retriever.generate_embedding")
def test_retrieve_evidence_scheme_id_filter(
    mock_gen_embedding, db_session: Session, sample_documents
):
    mock_gen_embedding.return_value = _create_vector(0.1)

    scheme_a_id = sample_documents["scheme_a_id"]
    response = retrieve_evidence(
        db=db_session,
        query="eligibility terms",
        scheme_id=scheme_a_id,
        score_threshold=0.50,
    )

    assert response.status == "success"
    assert len(response.evidence) > 0
    for item in response.evidence:
        assert item.source.document_id == sample_documents["doc_1"].id


# --- 4. Language Filtering ---


@patch("app.rag.retriever.generate_embedding")
def test_retrieve_evidence_language_filter(
    mock_gen_embedding, db_session: Session, sample_documents
):
    mock_gen_embedding.return_value = _create_vector(0.05)

    response = retrieve_evidence(
        db=db_session,
        query="PMEGP subsidy query",
        language="hi",
        score_threshold=0.50,
    )

    assert response.status == "success"
    assert len(response.evidence) == 1
    assert response.evidence[0].source.language == "hi"


# --- 5. Effective Date Filtering ---


@patch("app.rag.retriever.generate_embedding")
def test_retrieve_evidence_effective_date_filter(
    mock_gen_embedding, db_session: Session, sample_documents
):
    mock_gen_embedding.return_value = _create_vector(0.05)

    # Date 2024-06-01: doc_2 (effective until 2023-12-31) is expired!
    response = retrieve_evidence(
        db=db_session,
        query="subsidy details",
        language="hi",
        effective_date=date(2024, 6, 1),
        score_threshold=0.50,
    )

    assert response.status == "no_relevant_evidence"
    assert len(response.evidence) == 0


# --- 6. Conflicting Sources Detection ---


@patch("app.rag.retriever.generate_embedding")
def test_conflicting_sources_status(mock_gen_embedding, db_session: Session):
    mock_gen_embedding.return_value = _create_vector(0.1)

    doc_a = Document(
        id=uuid4(),
        title="Doc Version A",
        source_name="Dept A",
        document_type="guideline",
        content_hash="hash_a",
        active=True,
    )
    doc_b = Document(
        id=uuid4(),
        title="Doc Version B",
        source_name="Dept B",
        document_type="guideline",
        content_hash="hash_b",
        active=True,
    )
    db_session.add(doc_a)
    db_session.add(doc_b)
    db_session.flush()

    # Document A states 10%, Document B states 25% for the same scheme query
    chunk_a = DocumentChunk(
        id=uuid4(),
        document_id=doc_a.id,
        chunk_index=0,
        content="Beneficiary contribution requirement is 10% of total project cost.",
        embedding=_create_vector(0.1),
    )
    chunk_b = DocumentChunk(
        id=uuid4(),
        document_id=doc_b.id,
        chunk_index=0,
        content="Beneficiary contribution requirement is 25% of total project cost.",
        embedding=_create_vector(0.1),
    )
    db_session.add(chunk_a)
    db_session.add(chunk_b)
    db_session.commit()

    response = retrieve_evidence(
        db=db_session,
        query="What is the contribution requirement?",
        score_threshold=0.50,
    )

    assert response.status == "conflicting_sources"
    assert len(response.evidence) == 2


# --- 7. Citation Metadata Verification ---


def test_citation_formatting(db_session: Session, sample_documents):
    doc_1 = sample_documents["doc_1"]
    chunk_1 = sample_documents["chunk_1"]

    meta = build_source_metadata(doc_1, chunk_1)
    assert meta.document_id == doc_1.id
    assert meta.title == "PMFME Official Guidelines 2024"
    assert meta.page_number == 14
    assert meta.section_title == "Funding Pattern"
    assert meta.source_name == "Ministry of Food Processing"

    item = format_evidence_item(chunk_1, doc_1, 0.8954321)
    assert item.chunk_id == chunk_1.id
    assert item.text == chunk_1.content
    assert item.score == 0.895432
    assert item.source.document_id == doc_1.id


# --- 8. Invalid Query & Max Length Validation ---


def test_invalid_query_raises_value_error(db_session: Session):
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        retrieve_evidence(db=db_session, query="   ")

    with pytest.raises(ValueError, match="Query exceeds max length of 2000 characters"):
        retrieve_evidence(db=db_session, query="a" * 2001)


# --- 9. Cosine Similarity Edge Case Unit Tests ---


def test_cosine_similarity_edge_cases():
    from app.rag.retriever import _cosine_similarity

    # Identical vectors
    assert abs(_cosine_similarity([1.0, 2.0], [1.0, 2.0]) - 1.0) < 1e-6

    # Orthogonal vectors
    assert abs(_cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-6

    # Zero vectors
    assert _cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
    assert _cosine_similarity([], [1.0, 2.0]) == 0.0

    # Dimension mismatch
    assert _cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0

    # NaN / Inf vectors
    assert _cosine_similarity([float("nan"), 1.0], [1.0, 2.0]) == 0.0
    assert _cosine_similarity([float("inf"), 1.0], [1.0, 2.0]) == 0.0


# --- 10. RAGQueryRequest Input Handling ---


@patch("app.rag.retriever.generate_embedding")
def test_retrieve_evidence_request_schema(
    mock_gen_embedding, db_session: Session, sample_documents
):
    mock_gen_embedding.return_value = _create_vector(0.1)

    req = RAGQueryRequest(
        query="PMFME applicant rules",
        scheme_id=sample_documents["scheme_a_id"],
        limit=1,
        score_threshold=0.50,
    )

    response = retrieve_evidence(db=db_session, query=req)
    assert response.status == "success"
    assert len(response.evidence) == 1


# --- 11. Document Loader Integration ---


@patch("os.access", return_value=True)
@patch("os.path.isfile", return_value=True)
@patch("os.path.exists", return_value=True)
@patch("app.rag.document_loader.retrieve_evidence")
@patch("app.rag.document_loader.ingest_document")
def test_document_loader_integration(
    mock_ingest, mock_retrieve, mock_exists, mock_isfile, mock_access, db_session: Session
):
    mock_doc = Document(
        title="Test Doc",
        source_name="Source A",
        document_type="guideline",
        content_hash="hash_test",
    )
    mock_ingest.return_value = mock_doc

    doc = load_document(db=db_session, file_path="dummy.pdf", title="Test Doc")
    assert doc == mock_doc
    mock_ingest.assert_called_once()

    mock_response = RAGQueryResponse(status="success", evidence=[])
    mock_retrieve.return_value = mock_response

    res = query_rag_pipeline(db=db_session, query="test query")
    assert res == mock_response


@pytest.mark.parametrize(
    "mock_exists,mock_isfile,mock_access,expected_error",
    [
        (False, True, True, FileNotFoundError),
        (True, False, True, ValueError),
        (True, True, False, PermissionError),
    ],
)
def test_document_loader_all_error_paths(
    mock_exists: bool,
    mock_isfile: bool,
    mock_access: bool,
    expected_error: type[Exception],
    db_session: Session,
):
    """Parametrized verification of document_loader file OS validation checks."""
    with (
        patch("os.path.exists", return_value=mock_exists),
        patch("os.path.isfile", return_value=mock_isfile),
        patch("os.access", return_value=mock_access),
    ):
        with pytest.raises(expected_error):
            load_document(db=db_session, file_path="test_spec.pdf", title="Test")


def test_load_document_invalid_language(db_session: Session):
    """Verifies ValueError raised for unsupported language code."""
    with pytest.raises(ValueError, match="Unsupported language code"):
        load_document(db=db_session, file_path="dummy.pdf", title="Test", language="invalid_lang")


# --- 12. API Error & Dimension Mismatch Tests ---


@patch("app.rag.retriever.generate_embedding", side_effect=Exception("OpenAI API error"))
def test_retrieve_evidence_embedding_generation_failure(mock_gen_embedding, db_session: Session):
    """Test graceful failure when embedding generation raises an exception."""
    response = retrieve_evidence(db=db_session, query="test query")
    assert response.status == "embedding_generation_failed"
    assert len(response.evidence) == 0


@patch("app.rag.retriever.generate_embedding")
def test_retrieve_evidence_invalid_query_vector_dimension(mock_gen_embedding, db_session: Session):
    """Test failure status when query vector has wrong dimension (e.g. 768)."""
    mock_gen_embedding.return_value = [0.1] * 768
    response = retrieve_evidence(db=db_session, query="test query")
    assert response.status == "embedding_generation_failed"
    assert len(response.evidence) == 0


@patch("app.rag.retriever.generate_embedding")
def test_skip_chunks_with_mismatched_embedding_dimensions(mock_gen_embedding, db_session: Session):
    """Test skipping chunks in DB that have wrong embedding dimensions."""
    mock_gen_embedding.return_value = _create_vector(0.1)

    doc = Document(
        title="Doc Wrong Vector",
        source_name="Dept",
        document_type="guideline",
        content_hash="hash_wrong_vec",
        active=True,
    )
    db_session.add(doc)
    db_session.flush()

    chunk_wrong = DocumentChunk(
        id=uuid4(),
        document_id=doc.id,
        chunk_index=0,
        content="Chunk with 768 vector instead of 1536",
        embedding=[0.1] * 768,  # Mismatched dimension!
    )
    db_session.add(chunk_wrong)
    db_session.commit()

    response = retrieve_evidence(db=db_session, query="test query", score_threshold=0.1)
    assert response.status == "no_relevant_evidence"
    assert len(response.evidence) == 0


@patch("app.rag.retriever.generate_embedding")
def test_exclude_documents_with_inverted_dates(mock_gen_embedding, db_session: Session):
    """Test excluding documents with inverted effective date ranges."""
    mock_gen_embedding.return_value = _create_vector(0.1)

    doc = Document(
        id=uuid4(),
        title="Doc Inverted Dates",
        source_name="Dept Bad Date",
        document_type="guideline",
        content_hash="hash_bad_dates",
        active=True,
        effective_from=date(2024, 12, 31),
        effective_until=date(2024, 1, 1),  # Inverted dates!
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunk(
        id=uuid4(),
        document_id=doc.id,
        chunk_index=0,
        content="Document content with inverted effective dates",
        embedding=_create_vector(0.1),
    )
    db_session.add(chunk)
    db_session.commit()

    response = retrieve_evidence(db=db_session, query="test query", score_threshold=0.1)
    assert response.status == "no_relevant_evidence"
    assert len(response.evidence) == 0
