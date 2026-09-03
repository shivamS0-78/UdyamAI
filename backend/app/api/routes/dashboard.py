"""Personalised Dashboard overview routes."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_profile
from app.database import get_session
from app.models.user import Profile
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_session),
) -> DashboardOverview:
    """Everything the signed-in user has opted into / produced:
    financial tool summaries, feasibility analyses, matched schemes, and
    generated reports."""
    return DashboardService.build_overview(session, profile)
