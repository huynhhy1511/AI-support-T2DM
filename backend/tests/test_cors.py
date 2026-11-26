from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_preflight_headers():
    """Verify that OPTIONS preflight request with allowed origin returns proper CORS headers."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "POST" in response.headers.get("access-control-allow-methods", "")

    # Also check standard GET request with Origin
    get_res = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert get_res.status_code == 200
    assert get_res.headers.get("access-control-allow-origin") == "http://localhost:3000"
