from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify that GET /api/health returns 200 and expected payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert "CareGenie" in data["message"] or "Personalized AI Health Assistant" in data["message"]


def test_root_endpoint():
    """Verify that GET / returns 200 and points to health check and docs."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "health_check" in data
    assert data["health_check"] == "/api/health"


def test_web_app_serving():
    """Verify that GET /app serves the HTML Single-Page Application."""
    response = client.get("/app")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "CareGenie" in response.text
    assert "Preliminary" in response.text


def test_static_assets_serving():
    """Verify that static CSS and JS are served properly."""
    css_res = client.get("/css/style.css")
    assert css_res.status_code == 200
    assert "Clinical Empathy" in css_res.text or "color-navy" in css_res.text

    js_res = client.get("/js/app.js")
    assert js_res.status_code == 200
    assert "CareGenie" in js_res.text or "API" in js_res.text

