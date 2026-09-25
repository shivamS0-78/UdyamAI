import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.api.deps import get_current_profile
from app.database import get_engine, get_session
from app.models.user import Profile
from app.reports.feasibility_report import assemble_feasibility_report_data
from app.reports.pdf_generator import create_feasibility_pdf
from app.schemas.feasibility import (
    AnalysisRunCreate,
    AnalysisRunResponse,
    AnalysisStatusResponse,
    ConsolidatedAnalysisResponse,
)
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

router = APIRouter()


def _execute_pipeline(run_id: UUID, run_data: AnalysisRunCreate) -> None:
    """Run the analysis pipeline outside the request/response cycle.

    Opens its own session because the request's session is closed once the response is
    sent. The orchestrator records ``completed``/``failed`` on the run itself, so a
    failure here only needs logging.
    """
    try:
        with Session(get_engine()) as session:
            AnalysisOrchestrator.run_analysis_pipeline(session, run_data, run_id=run_id)
    except Exception:
        logger.exception("Background analysis pipeline failed for run %s", run_id)


@router.post("", response_model=AnalysisRunResponse, status_code=201)
@router.post("/", response_model=AnalysisRunResponse, status_code=201, include_in_schema=False)
def create_analysis(
    run_data: AnalysisRunCreate,
    background_tasks: BackgroundTasks,
    profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_session),
):
    """Queue an analysis run and return it immediately.

    The pipeline makes dozens of sequential database round trips, so running it inline
    would hold the request open for the full duration. Instead the run is persisted as
    ``pending`` (giving the client an id straight away) and executed afterwards; clients
    poll ``GET /analysis/{id}/status`` until it completes.
    """
    # Analyses always belong to the authenticated user. The profile is
    # resolved from the Supabase session so a client cannot create runs
    # under someone else's (or a random guest) profile.
    owned_run = run_data.model_copy(update={"user_id": profile.id})
    db_run = AnalysisOrchestrator.create_run(db, owned_run, status="pending")

    background_tasks.add_task(_execute_pipeline, db_run.id, owned_run)
    return db_run


@router.get("/{id}", response_model=AnalysisRunResponse)
def get_analysis(id: UUID, db: Session = Depends(get_session)):
    run = AnalysisService.get_analysis_run(db, id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run with id {id} not found")
    return run


@router.get("/{id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(id: UUID, db: Session = Depends(get_session)):
    status_response = AnalysisService.get_analysis_run_status(db, id)
    if not status_response:
        raise HTTPException(status_code=404, detail=f"Analysis run with id {id} not found")
    return status_response


@router.get("/{id}/consolidated", response_model=ConsolidatedAnalysisResponse)
def get_consolidated_analysis(id: UUID, db: Session = Depends(get_session)):
    res = AnalysisService.get_consolidated_analysis(db, id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Analysis run with id {id} not found")
    return res


@router.get("/{id}/report/pdf")
def download_analysis_pdf(id: UUID, db: Session = Depends(get_session)):
    run = AnalysisService.get_analysis_run(db, id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run with id {id} not found")
    if run.status in ("pending", "running", "created"):
        raise HTTPException(
            status_code=409,
            detail=f"Analysis run with id {id} is currently {run.status}. PDF report cannot be generated until analysis is completed.",
        )

    try:
        report_data = assemble_feasibility_report_data(db, id)
        pdf_bytes = create_feasibility_pdf(report_data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate PDF report") from exc

    filename = f"udyam-feasibility-{str(id)[:8]}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
