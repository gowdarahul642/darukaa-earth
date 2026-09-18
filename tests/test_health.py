"""
Phase 1 tests: application boots and the health endpoint responds correctly.
This is the smoke test that proves the environment/setup is sound before
any real business logic is added in later phases.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert body["docs"] == "/docs"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "darukaa-earth"
    assert "llm_provider" in body
