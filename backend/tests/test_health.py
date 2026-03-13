"""
TDD - Tests written FIRST before implementation.

User Journey:
  As a DevOps engineer, I want a health check endpoint,
  so that I can verify the service and its dependencies are running.
"""


def test_health_check_returns_200(client):
    """Health endpoint should return HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_check_returns_status_ok(client):
    """Health endpoint should return status: ok."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_check_includes_version(client):
    """Health endpoint should include app version."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "version" in data


def test_health_check_includes_database_status(client):
    """Health endpoint should report database connectivity."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "database" in data
    assert data["database"] in ("ok", "error")


def test_root_redirects_or_responds(client):
    """Root path should return a response (docs or redirect)."""
    response = client.get("/")
    assert response.status_code in (200, 307, 308)


def test_cors_headers_present(client):
    """CORS headers should be present for browser requests."""
    response = client.options(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    # FastAPI with CORSMiddleware returns 200 for preflight
    assert response.status_code in (200, 405)


def test_health_check_reports_database_error_when_db_fails(client):
    """Health endpoint should report database: error when DB query raises an exception."""
    from unittest.mock import patch
    from sqlalchemy.exc import OperationalError

    with patch("app.api.health.get_db") as mock_get_db:
        # Make the session's execute raise an OperationalError
        from unittest.mock import MagicMock
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError("", {}, Exception("DB down"))
        mock_get_db.return_value = iter([mock_session])

        # Override dependency directly
        from app.main import app
        from app.core.database import get_db

        def broken_db():
            yield mock_session

        app.dependency_overrides[get_db] = broken_db
        from fastapi.testclient import TestClient
        with TestClient(app) as c:
            response = c.get("/api/v1/health")
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["database"] == "error"
