from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.api.deps import get_current_profile
from app.database import get_session
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

router = APIRouter()


@router.post("", response_model=AnalysisRunResponse, status_code=201)
@router.post("/", response_model=AnalysisRunResponse, status_code=201, include_in_schema=False)
def create_analysis(
    run_data: AnalysisRunCreate,
    profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_session),
):
    # Analyses always belong to the authenticated user. The profile is
    # resolved from the Supabase session so a client cannot create runs
    # under someone else's (or a random guest) profile.
    owned_run = run_data.model_copy(update={"user_id": profile.id})
    return AnalysisOrchestrator.run_analysis_pipeline(db, owned_run)


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
