import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db

init_db()
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_full_pipeline_chat_endpoint():
    payload = {
        "message": "My farm is in a semi-arid region growing continuous wheat with soil organic carbon at 0.3%.",
        "conversation_id": None,
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "conversation_id" in data
    assert data["environmental_state"]["region"] == "semi-arid"
    assert data["environmental_state"]["soil"]["organic_carbon_percent"] == 0.3
    assert "## Environmental Assessment" in data["response"]

    # Multi-turn interaction using same conversation_id
    conv_id = data["conversation_id"]
    followup_payload = {
        "message": "Annual rainfall is low.",
        "conversation_id": conv_id,
    }
    res_followup = client.post("/api/v1/chat", json=followup_payload)
    assert res_followup.status_code == 200
    data_followup = res_followup.json()

    assert data_followup["conversation_id"] == conv_id
    assert data_followup["environmental_state"]["region"] == "semi-arid"
    assert data_followup["environmental_state"]["climate"]["rainfall_category"] == "low"