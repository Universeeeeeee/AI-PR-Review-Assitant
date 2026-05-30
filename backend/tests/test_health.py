from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_service_status():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-pr-review-assistant-backend",
    }


def test_cors_allows_local_vite_origin_for_analyze_api():
    client = TestClient(app)

    response = client.options(
        "/api/analyze-pr",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
