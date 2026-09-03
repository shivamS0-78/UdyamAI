import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_profile, get_current_user
from app.main import app
from app.models.analysis import AnalysisRun
from app.models.location import District, Taluka, Village
from app.models.user import Profile
from app.schemas.feasibility import AnalysisStatusResponse
from app.services.auth_service import AuthUser

# Register sqlite3 adapter for list serialization in SQLite in-memory test databases
sqlite3.register_adapter(list, json.dumps)

# Fixed identities used by the shared auth overrides below. Tests that build
# user-owned rows should reuse these ids so ownership checks line up.
TEST_AUTH_USER_ID = uuid4()
TEST_PROFILE_ID = uuid4()


def _fake_auth_user() -> AuthUser:
    return AuthUser(sub=str(TEST_AUTH_USER_ID), phone="+919999999999")


def _fake_auth_profile() -> Profile:
    return Profile(
        id=TEST_PROFILE_ID,
        auth_user_id=TEST_AUTH_USER_ID,
        name="Test User",
        phone="+919999999999",
    )


@pytest.fixture(scope="function", autouse=True)
def _supabase_auth_overrides():
    """Run route tests as an authenticated Supabase user.

    Protected routers resolve identity through ``get_current_user`` /
    ``get_current_profile``; overriding them here keeps pre-auth tests
    green. Tests that specifically exercise auth failures should clear
    ``app.dependency_overrides`` for their own assertions.
    """
    app.dependency_overrides[get_current_user] = _fake_auth_user
    app.dependency_overrides[get_current_profile] = _fake_auth_profile
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="function")
def dummy_run():
    """Shared fixture for an AnalysisRun instance (owned by the test user)."""
    return AnalysisRun(
        id=uuid4(),
        user_id=TEST_PROFILE_ID,
        location_id=uuid4(),
        business_category_id=uuid4(),
        available_capital=50000.0,
        status="created",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture(scope="function")
def dummy_status(dummy_run):
    """Shared fixture for an AnalysisStatusResponse instance."""
    return AnalysisStatusResponse(
        id=dummy_run.id,
        analysis_id=dummy_run.id,
        status="created",
        progress_percentage=10,
        current_step="created",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture(scope="function")
def dummy_district():
    """Shared fixture for a District instance."""
    return District(id=uuid4(), name="Pune", state="Maharashtra", lgd_code="123")


@pytest.fixture(scope="function")
def dummy_taluka(dummy_district):
    """Shared fixture for a Taluka instance."""
    return Taluka(id=uuid4(), name="Haveli", district_id=dummy_district.id, lgd_code="456")


@pytest.fixture(scope="function")
def dummy_village(dummy_district, dummy_taluka):
    """Shared fixture for a Village instance."""
    return Village(
        id=uuid4(),
        name="Khed",
        district_id=dummy_district.id,
        taluka_id=dummy_taluka.id,
        lgd_code="789",
    )
