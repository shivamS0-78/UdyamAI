from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.models.analysis import AnalysisRun
from app.schemas.feasibility import AnalysisStatusResponse

dummy_run = AnalysisRun(
    id=uuid4(),
    user_id=uuid4(),
    location_id=uuid4(),
    business_category_id=uuid4(),
    available_capital=50000.0,
    status="created",
    created_at=datetime.now(timezone.utc),
)

dummy_status = AnalysisStatusResponse(
    id=dummy_run.id,
    analysis_id=dummy_run.id,
    status="created",
    progress_percentage=10,
    current_step="created",
    created_at=datetime.now(timezone.utc),
)


def test_create_analysis_v1(client, dummy_run):
    payload = {
        "user_id": str(dummy_run.user_id),
        "location_id": str(dummy_run.location_id),
        "business_category_id": str(dummy_run.business_category_id),
        "available_capital": 50000.0,
    }
    with patch(
        "app.api.routes.analysis.AnalysisOrchestrator.run_analysis_pipeline", return_value=dummy_run
    ):
        response = client.post("/api/v1/analysis", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["analysis_id"] == str(dummy_run.id)
        assert data["id"] == str(dummy_run.id)
        assert data["status"] == "created"


def test_create_analysis_location_not_found(client, dummy_run):
    payload = {
        "user_id": str(dummy_run.user_id),
        "location_id": str(uuid4()),
        "available_capital": 50000.0,
    }
    with patch(
        "app.api.routes.analysis.AnalysisOrchestrator.run_analysis_pipeline",
        side_effect=HTTPException(
            status_code=404, detail="Location with identifier 'xyz' not found"
        ),
    ):
        response = client.post("/api/v1/analysis", json=payload)
        assert response.status_code == 404
        assert "Location" in response.json()["detail"]


def test_get_analysis_success(client, dummy_run):
    with patch("app.api.routes.analysis.AnalysisService.get_analysis_run", return_value=dummy_run):
        response = client.get(f"/api/v1/analysis/{dummy_run.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == str(dummy_run.id)
        assert data["id"] == str(dummy_run.id)
        assert data["available_capital"] == 50000.0


def test_get_analysis_not_found(client):
    non_existent_id = uuid4()
    with patch("app.api.routes.analysis.AnalysisService.get_analysis_run", return_value=None):
        response = client.get(f"/api/v1/analysis/{non_existent_id}")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


def test_get_analysis_status_success(client, dummy_run, dummy_status):
    with patch(
        "app.api.routes.analysis.AnalysisService.get_analysis_run_status",
        return_value=dummy_status,
    ):
        response = client.get(f"/api/v1/analysis/{dummy_run.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == str(dummy_run.id)
        assert data["status"] == "created"
        assert data["progress_percentage"] == 10
        assert data["current_step"] == "created"


def test_get_analysis_status_not_found(client):
    non_existent_id = uuid4()
    with patch(
        "app.api.routes.analysis.AnalysisService.get_analysis_run_status", return_value=None
    ):
        response = client.get(f"/api/v1/analysis/{non_existent_id}/status")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


def test_get_consolidated_analysis_success(client, dummy_run):
    from app.schemas.feasibility import ConsolidatedAnalysisResponse

    dummy_consolidated = ConsolidatedAnalysisResponse(
        analysis_id=dummy_run.id,
        status="completed",
        location={"village_name": "Khed"},
        business={"category_name": "Dairy Farming"},
        financial={"available_capital": 50000.0},
        market={"population_estimate": 10000},
        competition={"competitor_count": 5},
        schemes=[],
        feasibility={"overall_score": 84.0},
        risks=[],
        ai_advice={"summary": "Highly feasible"},
    )
    with patch(
        "app.api.routes.analysis.AnalysisService.get_consolidated_analysis",
        return_value=dummy_consolidated,
    ):
        response = client.get(f"/api/v1/analysis/{dummy_run.id}/consolidated")
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == str(dummy_run.id)
        assert data["status"] == "completed"
        assert data["location"]["village_name"] == "Khed"
        assert data["ai_advice"]["summary"] == "Highly feasible"


def test_get_consolidated_analysis_not_found(client):
    non_existent_id = uuid4()
    with patch(
        "app.api.routes.analysis.AnalysisService.get_consolidated_analysis", return_value=None
    ):
        response = client.get(f"/api/v1/analysis/{non_existent_id}/consolidated")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
