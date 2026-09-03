import os
import tempfile
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pypdf.errors import PdfReadError
from sqlmodel import Session, create_engine, select

from app.config import settings
from app.models.rag import Document, DocumentChunk
from app.models.scheme import Scheme
from app.rag.chunker import chunk_document
from app.rag.document_parser import (
    CorruptedPDFError,
    EmptyPDFError,
    EncryptedPDFError,
    ScannedPDFError,
    parse_pdf,
)
from app.rag.embeddings import (
    EmbeddingRateLimiter,
    EmbeddingRetryExhaustedError,
    generate_embedding,
    generate_embeddings,
)
from app.rag.knowledge_base import calculate_sha256, ingest_document
from app.rag.token_counter import count_tokens, count_tokens_batch, estimate_embedding_cost

# Prevent ValueError in embeddings generation
settings.OPENAI_API_KEY = "mock-openai-key-for-testing"


# Setup an in-memory SQLite database for testing RAG SQLModels
@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine("sqlite:///:memory:")
    # Create only the required tables to avoid PostGIS Geography table creation errors in SQLite
    Document.__table__.create(engine)
    Scheme.__table__.create(engine)
    DocumentChunk.__table__.create(engine)
    with Session(engine) as session:
        yield session


# Helper to create a temporary file with custom bytes
@pytest.fixture
def temp_file():
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, "wb") as f:
        f.write(b"dummy pdf contents")
    yield path
    os.remove(path)


# --- 1. Testing document_parser.py ---


@patch("app.rag.document_parser.pypdf.PdfReader")
def test_parse_pdf_success(mock_pdf_reader, temp_file):
    # Mocking standard PDF with 2 pages of text
    mock_reader = MagicMock()
    mock_reader.is_encrypted = False

    page1 = MagicMock()
    page1.extract_text.return_value = "Page 1: PMFME contribution is 10 percent."

    page2 = MagicMock()
    page2.extract_text.return_value = "Page 2: Exception list for schemes."

    mock_reader.pages = [page1, page2]
    mock_pdf_reader.return_value = mock_reader

    result = parse_pdf(temp_file)
    assert len(result) == 2
    assert result[0]["page_number"] == 1
    assert "PMFME" in result[0]["text"]
    assert result[1]["page_number"] == 2
    assert "Exception" in result[1]["text"]


def test_parse_pdf_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_pdf("non_existent_file.pdf")


def test_parse_pdf_zero_bytes():
    with tempfile.NamedTemporaryFile() as tmp:
        with pytest.raises(EmptyPDFError):
            parse_pdf(tmp.name)


@patch("app.rag.document_parser.pypdf.PdfReader")
def test_parse_pdf_encrypted(mock_pdf_reader, temp_file):
    mock_reader = MagicMock()
    mock_reader.is_encrypted = True
    mock_pdf_reader.return_value = mock_reader

    with pytest.raises(EncryptedPDFError):
        parse_pdf(temp_file)


@patch("app.rag.document_parser.pypdf.PdfReader")
def test_parse_pdf_corrupted(mock_pdf_reader, temp_file):
    mock_pdf_reader.side_effect = PdfReadError("Corrupt headers")

    with pytest.raises(CorruptedPDFError):
        parse_pdf(temp_file)


@patch("app.rag.document_parser.pypdf.PdfReader")
def test_parse_pdf_empty_pages(mock_pdf_reader, temp_file):
    mock_reader = MagicMock()
    mock_reader.is_encrypted = False
    mock_reader.pages = []
    mock_pdf_reader.return_value = mock_reader

    with pytest.raises(EmptyPDFError):
        parse_pdf(temp_file)


@patch("app.rag.document_parser.pypdf.PdfReader")
def test_parse_pdf_scanned_image_only(mock_pdf_reader, temp_file):
    mock_reader = MagicMock()
    mock_reader.is_encrypted = False

    page1 = MagicMock()
    page1.extract_text.return_value = ""  # Scanned PDF returns empty text

    mock_reader.pages = [page1]
    mock_pdf_reader.return_value = mock_reader

    with pytest.raises(ScannedPDFError):
        parse_pdf(temp_file)


# --- 2. Testing chunker.py ---


def test_sliding_window_chunking():
    pages = [
        {"page_number": 1, "text": "This is a sentence. Page 1 metadata content."},
        {"page_number": 2, "text": "Another page text here. Exception is handled."},
    ]
    doc_id = uuid4()

    # 20 chars size, 5 chars overlap
    chunks = chunk_document(
        pages=pages,
        document_id=doc_id,
        source_title="Test Document",
        source_url="http://test.com",
        document_version="1.0",
        chunk_size=20,
        chunk_overlap=5,
    )

    assert len(chunks) > 0
    assert chunks[0]["document_id"] == doc_id
    assert chunks[0]["source_title"] == "Test Document"
    assert chunks[0]["source_url"] == "http://test.com"
    assert chunks[0]["document_version"] == "1.0"

    # Validate sliding window increment
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


def test_chunker_invalid_parameters():
    pages = [{"page_number": 1, "text": "Text"}]
    with pytest.raises(ValueError):
        chunk_document(pages, uuid4(), "Title", chunk_size=-5)
    with pytest.raises(ValueError):
        chunk_document(pages, uuid4(), "Title", chunk_size=10, chunk_overlap=15)


# --- 3. Testing embeddings.py API Success & Failure ---


@patch("app.rag.embeddings.get_openai_client")
def test_generate_embeddings_success(mock_get_client):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_data = [MagicMock(embedding=[0.1] * 1536), MagicMock(embedding=[0.2] * 1536)]
    mock_response.data = mock_data
    mock_client.embeddings.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    embeddings = generate_embeddings(["Text 1", "Text 2"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1536
    assert embeddings[0][0] == 0.1
    assert embeddings[1][0] == 0.2


@patch("app.rag.embeddings.get_openai_client")
def test_generate_embeddings_failure(mock_get_client):
    mock_client = MagicMock()
    mock_client.embeddings.create.side_effect = Exception("OpenAI API Key Invalid")
    mock_get_client.return_value = mock_client

    with pytest.raises(Exception) as excinfo:
        generate_embeddings(["Text"])
    assert "API Key Invalid" in str(excinfo.value)


# --- 4. Testing knowledge_base.py Ingestion & Deduplication ---


@patch("app.rag.knowledge_base.parse_pdf")
@patch("app.rag.knowledge_base.generate_embeddings")
def test_ingest_document_success(mock_embed, mock_parse, db_session, temp_file):
    # Mock parser output
    mock_parse.return_value = [{"page_number": 1, "text": "PMFME scheme loans eligibility rule."}]
    # Mock embedding output (1536 dimensions)
    mock_embed.return_value = [[0.05] * 1536]

    doc = ingest_document(
        db=db_session,
        file_path=temp_file,
        title="PMFME Guidelines",
        source_name="MoFPI",
        source_url="http://test-url.com",
        document_version="1.0",
    )

    assert doc is not None
    assert doc.title == "PMFME Guidelines"
    assert doc.source_url == "http://test-url.com"

    # Assert DB persistence
    db_doc = db_session.get(Document, doc.id)
    assert db_doc is not None
    assert len(db_doc.chunks) == 1
    assert db_doc.chunks[0].page_number == 1
    assert db_doc.chunks[0].content == "PMFME scheme loans eligibility rule."
    assert db_doc.chunks[0].embedding is not None


@patch("app.rag.knowledge_base.parse_pdf")
@patch("app.rag.knowledge_base.generate_embeddings")
def test_ingest_document_deduplication(mock_embed, mock_parse, db_session, temp_file):
    # Register document once in database
    content_hash = calculate_sha256(temp_file)
    existing_doc = Document(
        title="Already Ingested Document",
        source_name="MoFPI",
        document_type="scheme_guideline",
        content_hash=content_hash,
        file_path=temp_file,
    )
    db_session.add(existing_doc)
    db_session.commit()
    db_session.refresh(existing_doc)

    # Mock parsing to return 1 chunk data
    mock_parse.return_value = [{"page_number": 1, "text": "PMFME scheme loans eligibility rule."}]
    mock_embed.return_value = [[0.05] * 1536]

    # Create the complete chunk in database
    db_chunk = DocumentChunk(
        document_id=existing_doc.id,
        chunk_index=0,
        content="PMFME scheme loans eligibility rule.",
        page_number=1,
        embedding=[0.05] * 1536,
    )
    existing_doc.chunks.append(db_chunk)
    db_session.add(existing_doc)
    db_session.commit()
    db_session.expire_all()

    # Attempting to ingest again
    result = ingest_document(
        db=db_session, file_path=temp_file, title="Duplicate Ingestion Attempt"
    )

    # Check that duplication check skipped the file because it is already complete
    assert result is None
    assert mock_embed.call_count == 0


@patch("app.rag.knowledge_base.parse_pdf")
@patch("app.rag.knowledge_base.generate_embeddings")
def test_ingest_document_incomplete_resumes(mock_embed, mock_parse, db_session, temp_file):
    # 1. Register incomplete document (0 chunks) in database
    content_hash = calculate_sha256(temp_file)
    existing_doc = Document(
        title="Incomplete Document",
        source_name="MoFPI",
        document_type="scheme_guideline",
        content_hash=content_hash,
        file_path=temp_file,
    )
    db_session.add(existing_doc)
    db_session.commit()
    db_session.refresh(existing_doc)

    # Mock parser and embeddings
    mock_parse.return_value = [{"page_number": 1, "text": "PMFME scheme loans eligibility rule."}]
    mock_embed.return_value = [[0.05] * 1536]

    # 2. Run ingestion (it should resume instead of skipping)
    result = ingest_document(
        db=db_session,
        file_path=temp_file,
        title="Incomplete Document",
    )

    assert result is not None
    assert result.id == existing_doc.id

    # Verify that the document now has its chunk and no duplicate document row was created
    db_doc = db_session.get(Document, existing_doc.id)
    assert len(db_doc.chunks) == 1
    assert db_doc.chunks[0].content == "PMFME scheme loans eligibility rule."

    docs_count = len(db_session.exec(select(Document)).all())
    assert docs_count == 1


@patch("app.rag.knowledge_base.parse_pdf")
@patch("app.rag.knowledge_base.generate_embeddings")
def test_ingest_document_rollback_on_embedding_failure(
    mock_embed, mock_parse, db_session, temp_file
):
    # Mock parser to return 1 chunk data
    mock_parse.return_value = [{"page_number": 1, "text": "PMFME scheme loans eligibility rule."}]
    # Mock embedding to fail
    mock_embed.side_effect = Exception("OpenAI API Failure")

    # Ingestion should fail and raise the exception
    with pytest.raises(Exception) as excinfo:
        ingest_document(
            db=db_session,
            file_path=temp_file,
            title="Failed Doc",
        )
    assert "OpenAI API Failure" in str(excinfo.value)

    # Verify that transaction rolled back and NO document was saved in database
    docs = db_session.exec(select(Document)).all()
    assert len(docs) == 0

    # Mock embedding to succeed now
    mock_embed.side_effect = None
    mock_embed.return_value = [[0.05] * 1536]

    # Re-try ingestion
    doc = ingest_document(
        db=db_session,
        file_path=temp_file,
        title="Success Doc",
    )
    assert doc is not None

    # Assert exactly 1 document and its chunks exist
    docs = db_session.exec(select(Document)).all()
    assert len(docs) == 1
    assert len(docs[0].chunks) == 1


@patch("app.rag.knowledge_base.parse_pdf")
@patch("app.rag.knowledge_base.generate_embeddings")
def test_ingest_document_retry_no_duplicate_chunks(mock_embed, mock_parse, db_session, temp_file):
    # Mock parser to return 2 chunks expected
    mock_parse.return_value = [
        {"page_number": 1, "text": "New chunk text 1"},
        {"page_number": 2, "text": "New chunk text 2"},
    ]
    mock_embed.return_value = [[0.05] * 1536, [0.06] * 1536]

    # Create incomplete document in DB
    content_hash = calculate_sha256(temp_file)
    existing_doc = Document(
        title="Duplicate Check Doc",
        source_name="MoFPI",
        document_type="scheme_guideline",
        content_hash=content_hash,
        file_path=temp_file,
    )
    db_session.add(existing_doc)
    db_session.commit()
    db_session.refresh(existing_doc)

    # Insert a dangling chunk (only 1 exists in DB, making it incomplete)
    dangling_chunk = DocumentChunk(
        document_id=existing_doc.id,
        chunk_index=0,
        content="Old incomplete text",
        page_number=1,
        embedding=[0.01] * 1536,
    )
    existing_doc.chunks.append(dangling_chunk)
    db_session.add(existing_doc)
    db_session.commit()
    db_session.expire_all()

    # Ingesting the document again (resuming) should wipe the dangling chunk and insert the 2 new ones
    result = ingest_document(
        db=db_session,
        file_path=temp_file,
        title="Duplicate Check Doc",
    )

    assert result is not None
    assert result.id == existing_doc.id

    # Verify document chunks were replaced and not duplicated
    db_doc = db_session.get(Document, existing_doc.id)
    assert len(db_doc.chunks) == 2
    assert db_doc.chunks[0].content == "New chunk text 1"
    assert db_doc.chunks[1].content == "New chunk text 2"


# --- 5. New Tests for Rate Limiting, Token Counter, Heading Detection, PDF Integration ---


def test_token_counter_basic():
    # Basic token counter verification
    text = "Hello world! This is a test."
    tokens = count_tokens(text)
    assert tokens > 0

    batch = ["First text chunk", "Second chunk here"]
    batch_tokens = count_tokens_batch(batch)
    assert batch_tokens == count_tokens(batch[0]) + count_tokens(batch[1])

    cost = estimate_embedding_cost(1000000)
    assert abs(cost - 0.02) < 1e-9


def test_rate_limiter_budget_check():
    # Enforces monthly budget limits
    limiter = EmbeddingRateLimiter(
        max_tokens_per_minute=1000,
        monthly_budget_cents=10,  # $0.10 i.e. 5 million tokens
        alert_threshold_percent=80,
    )

    # 6 million tokens = 12 cents cost. This should raise budget exceeded ValueError
    with pytest.raises(ValueError) as excinfo:
        limiter.check_token_budget(6000000)
    assert "budget exceeded" in str(excinfo.value)


@patch("app.rag.embeddings.time.sleep")
def test_rate_limiter_minute_window(mock_sleep):
    # Enforces tokens per minute sleep block
    limiter = EmbeddingRateLimiter(
        max_tokens_per_minute=100, monthly_budget_cents=5000, alert_threshold_percent=80
    )

    # First batch uses 60 tokens (fine, no sleep)
    limiter.wait_for_rate_limit(60)
    assert mock_sleep.call_count == 0

    # Second batch tries 50 tokens (total 110, exceeds 100 limit, should sleep)
    limiter.wait_for_rate_limit(50)
    assert mock_sleep.call_count == 1


def test_heading_heuristic_detection():
    # Verify various heading heuristic formats
    doc_id = uuid4()

    # 1. Markdown Heading
    chunks = chunk_document(
        pages=[{"page_number": 1, "text": "# Section Heading 1\nSome details here."}],
        document_id=doc_id,
        source_title="Test Title",
        chunk_size=100,
        chunk_overlap=10,
    )
    assert chunks[0]["section_heading"] == "# Section Heading 1"

    # 2. Numbered Heading
    chunks = chunk_document(
        pages=[{"page_number": 1, "text": "1.2 Introduction\nSome details here."}],
        document_id=doc_id,
        source_title="Test Title",
        chunk_size=100,
        chunk_overlap=10,
    )
    assert chunks[0]["section_heading"] == "1.2 Introduction"

    # 3. Hindi Numbered Heading
    chunks = chunk_document(
        pages=[{"page_number": 1, "text": "१. प्रस्तावना\nSome details here."}],
        document_id=doc_id,
        source_title="Test Title",
        chunk_size=100,
        chunk_overlap=10,
    )
    assert chunks[0]["section_heading"] == "१. प्रस्तावना"

    # 4. Keyword heading (English/Hindi)
    chunks = chunk_document(
        pages=[{"page_number": 1, "text": "Chapter Three: Rules\nSome details here."}],
        document_id=doc_id,
        source_title="Test Title",
        chunk_size=100,
        chunk_overlap=10,
    )
    assert chunks[0]["section_heading"] == "Chapter Three: Rules"

    chunks = chunk_document(
        pages=[{"page_number": 1, "text": "अध्याय २: पात्रता\nSome details here."}],
        document_id=doc_id,
        source_title="Test Title",
        chunk_size=100,
        chunk_overlap=10,
    )
    assert chunks[0]["section_heading"] == "अध्याय २: पात्रता"

    # 5. UPPERCASE English Heading
    chunks = chunk_document(
        pages=[{"page_number": 1, "text": "ELIGIBILITY CRITERIA\nSome details here."}],
        document_id=doc_id,
        source_title="Test Title",
        chunk_size=100,
        chunk_overlap=10,
    )
    assert chunks[0]["section_heading"] == "ELIGIBILITY CRITERIA"

    # 6. Colon endings
    chunks = chunk_document(
        pages=[{"page_number": 1, "text": "Eligibility Guidelines:\nSome details here."}],
        document_id=doc_id,
        source_title="Test Title",
        chunk_size=100,
        chunk_overlap=10,
    )
    assert chunks[0]["section_heading"] == "Eligibility Guidelines:"

    # 7. Non-heading (regular sentence fragment)
    chunks = chunk_document(
        pages=[{"page_number": 1, "text": "the quick brown fox jumped over the lazy dog."}],
        document_id=doc_id,
        source_title="Test Title",
        chunk_size=100,
        chunk_overlap=10,
    )
    assert chunks[0]["section_heading"] is None


def test_parse_pdf_real_scanned_file_integration():
    # Writes minimal valid PDF bytes and tests real integration parsing
    # This should trigger ScannedPDFError since it contains no extractable text
    minimal_pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /Resources <<>> /MediaBox [0 0 612 792] /Contents 4 0 R>> endobj\n"
        b"4 0 obj <</Length 21>> stream\n"
        b"BT /F1 12 Tf ET\n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 5\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000056 00000 n\n"
        b"0000000111 00000 n\n"
        b"0000000212 00000 n\n"
        b"trailer <</Size 5 /Root 1 0 R>>\n"
        b"startxref\n"
        b"282\n"
        b"%%EOF"
    )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(minimal_pdf_bytes)
        tmp_name = tmp.name

    try:
        with pytest.raises(ScannedPDFError):
            parse_pdf(tmp_name)
    finally:
        os.remove(tmp_name)


def test_config_defaults():
    # Validate defaults are loaded correctly
    assert settings.RAG_CHUNK_SIZE == 800
    assert settings.RAG_CHUNK_OVERLAP == 150
    assert settings.RAG_EMBEDDING_MODEL == "text-embedding-3-small"
    assert settings.RAG_EMBEDDING_BATCH_SIZE == 100
    assert settings.RAG_EMBEDDING_MAX_TOKENS_PER_MINUTE == 150000
    assert settings.RAG_EMBEDDING_MONTHLY_BUDGET_CENTS == 5000


@patch("app.rag.knowledge_base.parse_pdf")
@patch("app.rag.knowledge_base.generate_embeddings")
def test_ingest_document_mismatch_exception(mock_embed, mock_parse, db_session, temp_file):
    # Mocking parser to return 2 chunks
    mock_parse.return_value = [
        {"page_number": 1, "text": "Page text chunk 1"},
        {"page_number": 2, "text": "Page text chunk 2"},
    ]
    # Mocking embeddings to fail by returning only 1 embedding instead of 2
    mock_embed.return_value = [[0.0] * 1536]

    with pytest.raises(ValueError) as excinfo:
        ingest_document(db=db_session, file_path=temp_file, title="Mismatch Test Doc")
    assert "Embedding count mismatch" in str(excinfo.value)


# --- 6. Refined Phase 3 Integration & Validation Tests ---


def test_generate_embedding_invalid_dimension(db_session):
    # Mock embeddings to return invalid dimension (e.g. 100 instead of 1536)
    with patch("app.rag.embeddings.get_openai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Return a vector of 100 dimensions instead of 1536
        mock_response.data = [MagicMock(embedding=[0.1] * 100)]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(ValueError) as excinfo:
            generate_embedding("Test text")
        assert "Generated embedding dimension is 100, expected 1536" in str(excinfo.value)


def test_secrets_production_validation():
    from app.config import Settings

    # Verify that ENV="production" raises ValueError when SECRET_KEY is missing
    with pytest.raises(ValueError) as excinfo:
        Settings(ENV="production", SECRET_KEY=None)
    assert "SECRET_KEY must be provided" in str(excinfo.value)


def test_secrets_development_fallback():
    from app.config import Settings

    # Verify fallback is applied in development
    s = Settings(ENV="development", SECRET_KEY=None)
    assert s.SECRET_KEY == "dev_secret_key_fallback"


def test_rate_limiter_forwarded_ip_helper():
    from fastapi import Request

    from app.utils.rate_limiter import get_client_ip

    # 1. Single IP
    req1 = MagicMock(spec=Request)
    req1.headers = {"x-forwarded-for": "1.1.1.1"}
    assert get_client_ip(req1) == "1.1.1.1"

    # 2. Leftmost IP from list
    req2 = MagicMock(spec=Request)
    req2.headers = {"x-forwarded-for": "2.2.2.2, 3.3.3.3, 4.4.4.4"}
    assert get_client_ip(req2) == "2.2.2.2"

    # 3. Fallback to client host
    req3 = MagicMock(spec=Request)
    req3.headers = {}
    req3.client = MagicMock()
    req3.client.host = "5.5.5.5"
    assert get_client_ip(req3) == "5.5.5.5"

    # 4. Safe fallback for missing client
    req4 = MagicMock(spec=Request)
    req4.headers = {}
    req4.client = None
    assert get_client_ip(req4) == "unknown"


# --- 7. Review Refinements (Lock Release, Retry Backoff, Transaction Decoupling) ---


def test_rate_limiter_below_limit_proceeds_immediately():
    limiter = EmbeddingRateLimiter(max_tokens_per_minute=100)
    # Starts at 0, consuming 50 tokens proceeds without sleeping
    with patch("time.sleep") as mock_sleep:
        limiter.wait_for_rate_limit(50)
        assert mock_sleep.call_count == 0
    assert limiter.tokens_this_minute == 50


def test_rate_limiter_exceeding_limit_sleeps():
    limiter = EmbeddingRateLimiter(max_tokens_per_minute=100)
    limiter.wait_for_rate_limit(80)

    # Consuming another 30 tokens triggers sleep since 80 + 30 > 100
    # Mock time.sleep to simulate time passage
    current_time = 100.0
    sleeps = []

    def mock_sleep(seconds):
        nonlocal current_time
        current_time += seconds
        sleeps.append(seconds)

    def mock_monotonic():
        return current_time

    with (
        patch("time.sleep", side_effect=mock_sleep),
        patch("time.monotonic", side_effect=mock_monotonic),
    ):
        limiter.minute_window_start = current_time
        limiter.wait_for_rate_limit(30)

    assert len(sleeps) == 1
    # Expect sleep time close to 60 seconds
    assert 59.0 <= sleeps[0] <= 60.0
    assert limiter.tokens_this_minute == 30  # Reset happened, now at 30


def test_rate_limiter_multithreading_no_sleep_blocking():
    limiter = EmbeddingRateLimiter(max_tokens_per_minute=100)
    limiter.wait_for_rate_limit(80)

    import threading

    # Thread 1 tries to consume 30 tokens -> exceeds limit, will wait/sleep
    # Thread 2 tries to consume 10 tokens -> fits within limit! It should proceed immediately
    # without being blocked by Thread 1's sleep!

    t1_started = threading.Event()
    t1_done = threading.Event()
    t2_done = threading.Event()
    t2_proceeded_immediately = False

    t2_sleep_event = threading.Event()
    t1_sleep_event = threading.Event()

    def thread1_run():
        t1_started.set()
        limiter.wait_for_rate_limit(30)
        t1_done.set()

    def thread2_run():
        nonlocal t2_proceeded_immediately
        t1_started.wait()
        # Give thread 1 a tiny fraction of a second to acquire the lock and sleep
        t2_sleep_event.wait(0.05)
        # Thread 2 should proceed immediately because Thread 1 released the lock while sleeping
        limiter.wait_for_rate_limit(10)
        t2_proceeded_immediately = True
        t2_done.set()

    # Mock sleep for thread 1 so it doesn't hang the test suite
    current_time = 100.0

    def mock_sleep(seconds):
        nonlocal current_time
        current_time += seconds
        t1_sleep_event.wait(0.01)  # Small real sleep to let other thread run

    def mock_monotonic():
        return current_time

    with (
        patch("time.sleep", side_effect=mock_sleep),
        patch("time.monotonic", side_effect=mock_monotonic),
    ):
        limiter.minute_window_start = current_time
        th1 = threading.Thread(target=thread1_run)
        th2 = threading.Thread(target=thread2_run)

        th1.start()
        th2.start()

        t2_done.wait(timeout=2.0)
        th2.join()
        th1.join()

    assert t2_proceeded_immediately, "Thread 2 must proceed immediately while Thread 1 is sleeping!"


@patch("app.rag.embeddings.get_openai_client")
@patch("time.sleep")
def test_retry_successful_first_attempt(mock_sleep, mock_get_client):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
    mock_client.embeddings.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    embedding = generate_embedding("Test text")
    assert len(embedding) == 1536
    assert mock_sleep.call_count == 0


@patch("app.rag.embeddings.get_openai_client")
@patch("time.sleep")
def test_retry_429_followed_by_success(mock_sleep, mock_get_client):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

    from openai import RateLimitError

    mock_client.embeddings.create.side_effect = [
        RateLimitError(
            message="Rate Limit Exceeded", response=MagicMock(status_code=429), body=None
        ),
        mock_response,
    ]
    mock_get_client.return_value = mock_client

    embedding = generate_embedding("Test text", max_retries=3, base_delay=0.01)
    assert len(embedding) == 1536
    assert mock_sleep.call_count == 1


@patch("app.rag.embeddings.get_openai_client")
@patch("time.sleep")
def test_retry_transient_failure_followed_by_success(mock_sleep, mock_get_client):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

    from openai import InternalServerError

    mock_client.embeddings.create.side_effect = [
        InternalServerError(
            message="Internal Server Error", response=MagicMock(status_code=500), body=None
        ),
        mock_response,
    ]
    mock_get_client.return_value = mock_client

    embedding = generate_embedding("Test text", max_retries=3, base_delay=0.01)
    assert len(embedding) == 1536
    assert mock_sleep.call_count == 1


@patch("app.rag.embeddings.get_openai_client")
@patch("time.sleep")
def test_retry_exhaustion_raises_custom_error(mock_sleep, mock_get_client):
    mock_client = MagicMock()
    from openai import APITimeoutError

    mock_client.embeddings.create.side_effect = APITimeoutError(request=MagicMock())
    mock_get_client.return_value = mock_client

    with pytest.raises(EmbeddingRetryExhaustedError) as excinfo:
        generate_embedding("Test text", max_retries=3, base_delay=0.01)
    assert "OpenAI API call failed after 3 attempts" in str(excinfo.value)
    assert mock_sleep.call_count == 3


@patch("app.rag.embeddings.get_openai_client")
@patch("time.sleep")
def test_retry_permanent_failure_raises_immediately(mock_sleep, mock_get_client):
    mock_client = MagicMock()
    from openai import AuthenticationError

    mock_client.embeddings.create.side_effect = AuthenticationError(
        message="Invalid API Key", response=MagicMock(status_code=401), body=None
    )
    mock_get_client.return_value = mock_client

    with pytest.raises(AuthenticationError) as excinfo:
        generate_embedding("Test text", max_retries=3, base_delay=0.01)
    assert "Invalid API Key" in str(excinfo.value)
    assert mock_sleep.call_count == 0


@patch("app.rag.knowledge_base.parse_pdf")
@patch("app.rag.knowledge_base.generate_embeddings")
def test_ingest_document_transaction_decoupling(mock_embed, mock_parse, db_session, temp_file):
    mock_parse.return_value = [
        {"page_number": 1, "text": "Page text chunk 1"},
    ]

    # Spy on DB commit and generate_embeddings calls
    call_order = []

    original_commit = db_session.commit

    def spy_commit():
        call_order.append("commit")
        return original_commit()

    db_session.commit = spy_commit

    def spy_embed(texts):
        call_order.append("embed")
        return [[0.1] * 1536]

    mock_embed.side_effect = spy_embed

    # Execute ingestion
    ingest_document(db=db_session, file_path=temp_file, title="Transaction Decoupling Test")

    # Verify call order: embed happens first (outside transaction), then commit happens once at the end.
    assert call_order == ["embed", "commit"]
