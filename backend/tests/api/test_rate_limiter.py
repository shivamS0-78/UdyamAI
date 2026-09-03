import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.utils.rate_limiter import RateLimiter

# Set up a test FastAPI app specifically to test the RateLimiter dependency
app = FastAPI()
api_test_limiter = RateLimiter(requests_limit=3, window_seconds=5)


@app.get("/test", dependencies=[Depends(api_test_limiter)])
def dummy_endpoint():
    return {"status": "ok"}


def test_rate_limiter_allows_requests():
    client = TestClient(app)

    # 3 requests should be allowed (limit is 3)
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    response = client.get("/test")
    assert response.status_code == 200

    response = client.get("/test")
    assert response.status_code == 200


def test_rate_limiter_blocks_excessive_requests():
    client = TestClient(app)

    # Making 4 requests: first 3 pass, 4th should return 429
    for _ in range(3):
        client.get("/test")

    response = client.get("/test")
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]


def test_rate_limiter_per_ip():
    limiter = RateLimiter(requests_limit=2, window_seconds=5)

    class MockRequest:
        class MockClient:
            def __init__(self, host):
                self.host = host

        def __init__(self, host):
            self.client = self.MockClient(host)
            self.headers = {}

    req1 = MockRequest("1.1.1.1")
    req2 = MockRequest("2.2.2.2")

    # Client 1 uses all its slots
    limiter(req1)
    limiter(req1)

    # Client 1 gets blocked
    with pytest.raises(Exception) as excinfo:
        limiter(req1)
    assert "Too many requests" in str(excinfo.value)

    # Client 2 is still allowed (separate IP)
    limiter(req2)  # Should not raise exception
