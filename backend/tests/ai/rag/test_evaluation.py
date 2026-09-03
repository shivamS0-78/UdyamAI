from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine

from app.config import settings
from app.models.rag import Document, DocumentChunk
from app.models.scheme import Scheme
from app.rag.evaluation.dataset import EVALUATION_DATASET
from app.rag.evaluation.evaluator import EvaluationReport, evaluate_retrieval

settings.OPENAI_API_KEY = "mock-openai-key-for-testing"
EMBEDDING_DIM = getattr(settings, "EMBEDDING_DIMENSION", 1536)
assert EMBEDDING_DIM > 0, "Invalid embedding dimension"


def _make_vector(active_idx: int, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generates a vector with elevated signal in specific index range for deterministic similarity."""
    v = [0.05] * dim
    start = active_idx * 100
    for i in range(start, start + 100):
        if i < dim:
            v[i] = 0.95
    return v


@pytest.fixture(name="db_session")
def db_session_fixture():
    """In-memory SQLite database session fixture for evaluation testing."""
    engine = create_engine("sqlite:///:memory:")
    Document.__table__.create(engine)
    Scheme.__table__.create(engine)
    DocumentChunk.__table__.create(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def benchmark_database(db_session: Session):
    """Populates test database with ground-truth scheme documents matching EVALUATION_DATASET."""
    schemes = [
        ("PMFME", "PMFME Scheme", 1),
        ("PMEGP", "PMEGP Scheme", 2),
        ("MUDRA", "MUDRA Scheme", 3),
        ("Stand-Up India", "Stand-Up India Scheme", 4),
        ("Agri Infrastructure Fund", "Agri Infrastructure Fund Scheme", 5),
    ]
    scheme_map = {}
    for code, name, idx in schemes:
        s_id = uuid4()
        db_session.add(Scheme(id=s_id, name=name, active=True))
        scheme_map[code] = (s_id, idx)
    db_session.flush()

    docs = [
        {
            "code": "PMFME",
            "title": "PMFME Official Guidelines 2024",
            "chunks": [
                (
                    "Financial Assistance and Funding Pattern",
                    "Beneficiary contribution under PMFME is 10% of project cost up to ₹10 lakh.",
                ),
                (
                    "Eligibility Criteria for Individual Micro Enterprises",
                    "Eligible entities for credit linked capital subsidy include micro food processing units, SHGs, and FPOs.",
                ),
                (
                    "Financial Assistance and Funding Pattern",
                    "Maximum subsidy amount per unit under PMFME is 35% up to ₹10 lakh for individual micro enterprises.",
                ),
                (
                    "Documentation and Application Procedure",
                    "Required documents include Aadhaar, PAN, bank statement, and project report.",
                ),
                (
                    "Capacity Building and EDP Training",
                    "Beneficiaries must undergo EDP training and food safety certification before loan disbursement.",
                ),
            ],
        },
        {
            "code": "PMEGP",
            "title": "PMEGP Official Scheme Guidelines 2023",
            "chunks": [
                (
                    "Margin Money Subsidy Pattern",
                    "Margin money subsidy percentage for general category in urban areas is 15%.",
                ),
                (
                    "Quantum and Nature of Financial Assistance",
                    "Maximum project cost allowed for manufacturing sector under PMEGP is 50 lakh.",
                ),
                (
                    "Margin Money Subsidy Pattern",
                    "Margin money subsidy rate for special category applicants in rural areas is 35%.",
                ),
                (
                    "Eligibility Conditions of Beneficiaries",
                    "Minimum age is 18 years and 8th pass qualification for projects above 10 lakh.",
                ),
                (
                    "Subsidy Disbursement Mechanism",
                    "Margin money subsidy lock-in period is 3 years in bank TDR.",
                ),
            ],
        },
        {
            "code": "MUDRA",
            "title": "PMMY MUDRA Guidelines 2023",
            "chunks": [
                (
                    "Product Categories and Loan Ceilings",
                    "Loan limits: Shishu 50000, Kishor 5 lakh, Tarun 10 lakh.",
                ),
                (
                    "Security and Guarantee Requirements",
                    "No collateral security is required for MUDRA loans up to 10 lakh covered by CGFMU.",
                ),
                (
                    "Repayment Period and Terms",
                    "Repayment period is 36 to 60 months with MUDRA card for working capital.",
                ),
                (
                    "Target Beneficiaries and Eligibility",
                    "Target beneficiaries include artisans, small shopkeepers, and vendors.",
                ),
                (
                    "Interest Rates and Charges",
                    "Interest rates follow RBI guidelines based on bank base rate.",
                ),
            ],
        },
        {
            "code": "Stand-Up India",
            "title": "Stand-Up India Official Guidelines 2023",
            "chunks": [
                (
                    "Nature and Scale of Financial Support",
                    "Loan amount ranges from 10 lakh to 1 crore for SC/ST and Women entrepreneurs.",
                ),
                (
                    "Eligibility Criteria",
                    "SC/ST or woman entrepreneur must hold at least 51% shareholding in non-individual greenfield enterprise.",
                ),
                (
                    "Repayment Schedule and Moratorium",
                    "Repayment period is up to 7 years with maximum 18 months moratorium.",
                ),
                (
                    "Margin Money and Subsidies",
                    "Margin money requirement is 15% for Stand-Up India.",
                ),
            ],
        },
        {
            "code": "Agri Infrastructure Fund",
            "title": "Agriculture Infrastructure Fund Operational Guidelines 2023",
            "chunks": [
                (
                    "Interest Subvention Benefits",
                    "3% interest subvention per annum up to limit of 2 crore loan.",
                ),
                (
                    "Period of Financial Support",
                    "Interest subvention benefit is available for maximum duration of 7 years.",
                ),
                (
                    "Eligible Project Activities",
                    "Eligible post-harvest infrastructure includes cold chain, silos, and pack houses.",
                ),
                (
                    "Credit Guarantee Coverage",
                    "CGTMSE credit guarantee fee paid by Government of India for loans up to 2 crore.",
                ),
            ],
        },
    ]

    for doc_info in docs:
        doc_id = uuid4()
        s_id, idx = scheme_map[doc_info["code"]]
        db_doc = Document(
            id=doc_id,
            title=doc_info["title"],
            source_name="Government Ministry",
            document_type="guideline",
            language="en",
            content_hash=f"hash_{doc_info['code']}",
            active=True,
        )
        db_session.add(db_doc)
        db_session.flush()

        for chunk_i, (sec_title, content) in enumerate(doc_info["chunks"]):
            chunk = DocumentChunk(
                id=uuid4(),
                document_id=doc_id,
                scheme_id=s_id,
                chunk_index=chunk_i,
                content=content,
                section_title=sec_title,
                embedding=_make_vector(idx),
            )
            db_session.add(chunk)

    db_session.commit()

    # Add conflicting document chunks for conflict test cases (vector idx=9)
    s_conflict_pmfme = uuid4()
    db_session.add(Scheme(id=s_conflict_pmfme, name="PMFME Conflict Scheme", active=True))
    conflict_doc_a = Document(
        id=uuid4(),
        title="PMFME Guidelines 2024",
        source_name="Ministry A",
        document_type="guideline",
        content_hash="hash_conflict_a",
        active=True,
    )
    conflict_doc_b = Document(
        id=uuid4(),
        title="PMFME Notice 2024",
        source_name="Ministry B",
        document_type="guideline",
        content_hash="hash_conflict_b",
        active=True,
    )
    db_session.add(conflict_doc_a)
    db_session.add(conflict_doc_b)
    db_session.flush()

    chunk_ca = DocumentChunk(
        id=uuid4(),
        document_id=conflict_doc_a.id,
        scheme_id=s_conflict_pmfme,
        chunk_index=99,
        content="Beneficiary contribution requirement is 10% of project cost.",
        section_title="Contribution Requirement",
        embedding=_make_vector(9),
    )
    chunk_cb = DocumentChunk(
        id=uuid4(),
        document_id=conflict_doc_b.id,
        scheme_id=s_conflict_pmfme,
        chunk_index=99,
        content="Beneficiary contribution requirement is 25% of project cost.",
        section_title="Contribution Requirement",
        embedding=_make_vector(9),
    )
    db_session.add(chunk_ca)
    db_session.add(chunk_cb)

    # Add conflicting PMEGP chunks for conflict_02 test case
    s_conflict_pmegp = uuid4()
    db_session.add(Scheme(id=s_conflict_pmegp, name="PMEGP Conflict Scheme", active=True))
    conflict_pmegp_a = Document(
        id=uuid4(),
        title="PMEGP Guidelines 2023",
        source_name="KVIC A",
        document_type="guideline",
        content_hash="hash_conflict_pmegp_a",
        active=True,
    )
    conflict_pmegp_b = Document(
        id=uuid4(),
        title="PMEGP Circular 2023",
        source_name="KVIC B",
        document_type="guideline",
        content_hash="hash_conflict_pmegp_b",
        active=True,
    )
    db_session.add(conflict_pmegp_a)
    db_session.add(conflict_pmegp_b)
    db_session.flush()

    chunk_pmegp_a = DocumentChunk(
        id=uuid4(),
        document_id=conflict_pmegp_a.id,
        scheme_id=s_conflict_pmegp,
        chunk_index=98,
        content="Maximum project cost allowed for PMEGP manufacturing unit is 25 lakh.",
        section_title="Project Cost Limits",
        embedding=_make_vector(10),
    )
    chunk_pmegp_b = DocumentChunk(
        id=uuid4(),
        document_id=conflict_pmegp_b.id,
        scheme_id=s_conflict_pmegp,
        chunk_index=98,
        content="Maximum project cost allowed for PMEGP manufacturing unit is 50 lakh.",
        section_title="Project Cost Limits",
        embedding=_make_vector(10),
    )
    db_session.add(chunk_pmegp_a)
    db_session.add(chunk_pmegp_b)

    db_session.commit()
    return db_session


def _mock_query_embedding(query_str: str) -> list[float]:
    """Maps query string deterministically to active index vector for evaluation test."""
    low = query_str.lower()
    if "pmfme" in low and ("10%" in low or "percentage" in low):
        return _make_vector(9)
    elif "pmegp" in low and "maximum loan limit" in low:
        return _make_vector(10)
    elif "pmfme" in low:
        return _make_vector(1)
    elif "pmegp" in low:
        return _make_vector(2)
    elif "mudra" in low:
        return _make_vector(3)
    elif "stand-up" in low:
        return _make_vector(4)
    elif (
        "agri" in low
        or "aif" in low
        or "subvention" in low
        or "cold chain" in low
        or "cgtmse" in low
    ):
        return _make_vector(5)
    elif "mars space" in low or "quantum crypto" in low or "interstellar" in low:
        return [0.0] * EMBEDDING_DIM
    return _make_vector(1)


# --- 1. Evaluation Engine & Benchmark Metrics Tests ---


@patch("app.rag.retriever.generate_embedding", side_effect=_mock_query_embedding)
def test_evaluate_retrieval_benchmark(mock_gen_embedding, db_session: Session, benchmark_database):
    report: EvaluationReport = evaluate_retrieval(
        db=db_session,
        eval_dataset=EVALUATION_DATASET,
        top_k=5,
        score_threshold=0.05,
    )

    assert isinstance(report, EvaluationReport)
    assert report.total_queries == len(EVALUATION_DATASET)
    assert report.top_k == 5
    assert report.recall_at_k >= 0.80
    assert report.precision_at_k >= 0.70
    assert report.status_accuracy >= 0.80
    assert len(report.query_details) == len(EVALUATION_DATASET)


def test_evaluate_retrieval_empty_dataset(db_session: Session):
    report = evaluate_retrieval(db=db_session, eval_dataset=[], top_k=5)
    assert report.total_queries == 0
    assert report.recall_at_k == 0.0
    assert report.precision_at_k == 0.0
    assert report.status_accuracy == 0.0


@patch(
    "app.rag.evaluation.evaluator.retrieve_evidence", side_effect=RuntimeError("Database failure")
)
def test_evaluate_retrieval_handles_exceptions_gracefully(mock_retrieve, db_session: Session):
    """Verifies evaluate_retrieval catches exceptions gracefully without crashing."""
    sample_dataset = [
        {
            "id": "err_test_01",
            "query": "Sample failing query?",
            "expected_status": "success",
        }
    ]
    report = evaluate_retrieval(db=db_session, eval_dataset=sample_dataset, top_k=5)
    assert report.total_queries == 1
    assert report.recall_at_k == 0.0
    assert report.precision_at_k == 0.0
    assert report.query_details[0].actual_status == "retrieval_failed"
    assert "Database failure" in report.query_details[0].error_message
