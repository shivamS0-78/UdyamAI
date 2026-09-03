"""Tests for Supabase Auth integration (JWT verification + protected routes)."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from app.config import settings
from app.main import app
from app.services.auth_service import (
    get_bearer_token,
    verify_supabase_token,
)

TEST_SECRET = "test-supabase-jwt-secret"


def _mint_token(
    *,
    secret: str = TEST_SECRET,
    sub: str = "11111111-1111-4111-8111-111111111111",
    phone: str = "+919999999999",
    ttl_seconds: int = 3600,
) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": sub,
        "phone": phone,
        "role": "authenticated",
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    return jose_jwt.encode(claims, secret, algorithm="HS256")


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", TEST_SECRET)
    yield


def test_verify_valid_token():
    token = _mint_token()
    user = verify_supabase_token(token)
    assert user.id
    assert user.phone == "+919999999999"
    assert user.role == "authenticated"


def test_verify_token_rejects_wrong_secret():
    token = _mint_token(secret="other-secret")
    with pytest.raises(ValueError):
        verify_supabase_token(token)


def test_verify_token_rejects_expired():
    token = _mint_token(ttl_seconds=-600)
    with pytest.raises(ValueError):
        verify_supabase_token(token)


def test_verify_token_rejects_garbage():
    with pytest.raises(ValueError):
        verify_supabase_token("not-a-jwt")


def test_get_bearer_token():
    assert get_bearer_token("Bearer abc.def.ghi") == "abc.def.ghi"
    assert get_bearer_token("bearer  token ") == "token"
    assert get_bearer_token("Basic abc") is None
    assert get_bearer_token(None) is None


def test_protected_route_rejects_missing_token(client: TestClient):
    # Remove the shared auth override so this call really is anonymous.
    app.dependency_overrides.clear()
    response = client.post("/api/v1/chat", json={"message": "Hi", "history": [], "language": "en"})
    assert response.status_code == 401
    assert "authenticated" in response.json()["detail"].lower()


def test_protected_route_rejects_bad_token(client: TestClient):
    app.dependency_overrides.clear()
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hi", "history": [], "language": "en"},
        headers={"Authorization": "Bearer definitely-not-valid"},
    )
    assert response.status_code == 401


def test_protected_route_accepts_valid_token(client: TestClient):
    from unittest.mock import patch

    app.dependency_overrides.clear()
    token = _mint_token()
    with patch(
        "app.api.routes.chat.generate_chat_reply", return_value=("Hello from UdyamAI.", True)
    ):
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hi", "history": [], "language": "en"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200


def test_auth_me_returns_user_and_profile(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"]
    assert data["profile"]["id"]
