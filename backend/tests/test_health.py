import logging
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

logger = logging.getLogger(__name__)
client = TestClient(app)


def test_health_check():
    """Test GET /api/v1/health with current environment."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "AI-support-T2DM"
    assert "database" in data
    assert data["database"] in ["connected", "disconnected"]

    if data["database"] == "disconnected":
        logger.info(
            "Health check note: Database status is 'disconnected'. "
            "Please check PostgreSQL service, credentials in .env, and ensure 'diabetes_ai_dev' exists."
        )


def test_health_check_connected_mock():
    """Verify health endpoint response when database connection succeeds."""
    mock_db = MagicMock()
    mock_scalar = MagicMock(return_value=1)
    mock_db.execute.return_value.scalar = mock_scalar

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "AI-support-T2DM"
        assert data["database"] == "connected"
    finally:
        app.dependency_overrides.clear()


def test_health_check_disconnected_mock():
    """Verify health endpoint handles database connection failure gracefully without crashing."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Simulated DB connection failure")

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "AI-support-T2DM"
        assert data["database"] == "disconnected"
    finally:
        app.dependency_overrides.clear()


def test_root_endpoint():
    """Test root info endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI-support-T2DM"
    assert data["status"] == "running"
    assert data["health_url"] == "/api/v1/health"
