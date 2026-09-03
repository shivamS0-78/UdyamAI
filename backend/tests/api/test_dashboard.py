"""Tests for the personalised dashboard overview route."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dashboard import DashboardOverview


def _sample_overview() -> DashboardOverview:
    return DashboardOverview()


def test_dashboard_overview_requires_auth(client: TestClient):
    app.dependency_overrides.clear()
    response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 401


def test_dashboard_overview_returns_overview(client: TestClient):
    with patch(
        "app.api.routes.dashboard.DashboardService.build_overview",
        return_value=_sample_overview(),
    ):
        response = client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["analyses"] == []
    assert data["schemes"] == []
    assert data["reports"] == []
    assert data["finance"]["expenses"]["count"] == 0


def test_dashboard_service_builds_overview_with_finance_rows():
    """Regression: aggregate SUM/COUNT queries must unwrap scalars instead of
    passing Row objects to float() (previously 500 on /dashboard/overview)."""
    from uuid import uuid4

    from sqlalchemy.pool import StaticPool
    from sqlmodel import Session, SQLModel, create_engine

    from app import models as _  # noqa: F401 - register every table
    from app.models.expenses import Expense
    from app.models.user import Profile
    from app.services.dashboard_service import DashboardService

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    profile = Profile(
        id=uuid4(),
        auth_user_id=uuid4(),
        name="Test User",
        phone="+919999999999",
    )
    live = Expense(profile_id=profile.id, category="rent", amount=1200.5)
    deleted = Expense(profile_id=profile.id, category="rent", amount=9999.0, deleted=True)

    with Session(engine) as session:
        session.add(profile)
        session.add(live)
        session.add(deleted)
        session.commit()
        overview = DashboardService.build_overview(session, profile)

    assert overview.finance.expenses.count == 1
    assert overview.finance.expenses.total == 1200.5
    assert overview.finance.cash_flow.count == 0
    assert overview.finance.cash_flow.net == 0.0
    assert overview.finance.savings.goals == 0
    assert overview.finance.budgets.count == 0
    assert overview.finance.debts.count == 0
    assert overview.finance.borrowings.count == 0
    assert overview.finance.credit.records == 0
    assert overview.finance.recycle_bin.count == 0
    assert overview.analyses == []
    assert overview.schemes == []
    assert overview.reports == []
