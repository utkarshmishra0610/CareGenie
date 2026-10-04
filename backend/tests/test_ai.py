from fastapi.testclient import TestClient
from app.ai.service import (
    extract_structured_symptoms,
    check_emergency,
    determine_suggested_specialty,
)


def get_auth_token(client: TestClient, username: str, email: str) -> str:
    """Helper to register and log in a test user, returning the JWT token."""
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "AIPassword123!",
            "full_name": "AI Test User",
            "preferred_language": "en",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"username_or_email": username, "password": "AIPassword123!"},
    )
    return res.json()["access_token"]


def test_symptom_extraction_structured():
    """Verify structured clinical symptom, duration, and severity extraction."""
    text = "I am a 21 years old female and I have had a moderate fever and body pain for 3 days"
    structured = extract_structured_symptoms(text)

    assert "fever" in structured.symptoms
    assert "body pain" in structured.symptoms or any("pain" in s for s in structured.symptoms)
    assert structured.duration == "3 days"
    assert structured.severity == "moderate"
    assert structured.age == 21
    assert structured.gender == "female"
    assert structured.is_emergency is False


def test_emergency_detection():
    """Verify red-flag emergency detection for acute cardiac symptoms."""
    emergency_text = "I have sudden severe crushing chest pain radiating to my arm and cold sweat"
    symptoms = ["chest pain", "cold sweat"]
    is_emergency, reasons, advice = check_emergency(symptoms, emergency_text)

    assert is_emergency is True
    assert len(reasons) > 0
    assert any("cardiac" in r.lower() or "chest" in r.lower() for r in reasons)
    assert advice is not None


def test_specialty_suggestion():
    """Verify specialist recommendation mapping."""
    specialty1 = determine_suggested_specialty([("Asthma", 0.8)], ["wheezing"])
    assert specialty1 == "Pulmonologist"

    specialty2 = determine_suggested_specialty([("Eczema", 0.7)], ["itchiness"])
    assert specialty2 == "Dermatologist"


def test_interactive_chat_endpoint(client: TestClient):
    """Test full conversational turn via POST /api/chat/sessions/{id}/interact."""
    token = get_auth_token(client, "ai_user", "ai@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a session
    s_res = client.post(
        "/api/chat/sessions", json={"language": "en"}, headers=headers
    )
    assert s_res.status_code == 201
    session_id = s_res.json()["id"]

    # 2. Interact with patient message
    interact_payload = {
        "content": "I have had a high fever and headache for 3 days."
    }
    res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json=interact_payload,
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "reply_text" in data
    assert "structured_symptoms" in data
    assert "fever" in data["structured_symptoms"]["symptoms"]
    assert data["structured_symptoms"]["duration"] == "3 days"
    assert data["disclaimer"] != ""
    assert data["suggested_specialty"] != ""

    # 3. Verify messages were persisted in database
    detail_res = client.get(f"/api/chat/sessions/{session_id}", headers=headers)
    assert detail_res.status_code == 200
    messages = detail_res.json()["messages"]
    assert len(messages) == 2  # user + assistant
    assert messages[0]["sender"] == "user"
    assert messages[1]["sender"] == "assistant"


def test_interactive_chat_emergency_flow(client: TestClient):
    """Test emergency alert response through the interact endpoint."""
    token = get_auth_token(client, "emer_user", "emer@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    s_res = client.post("/api/chat/sessions", json={}, headers=headers)
    session_id = s_res.json()["id"]

    emergency_msg = {"content": "Help me, severe crushing chest pain and cold sweat"}
    res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json=emergency_msg,
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["detected_emergency"] is True
    assert "Urgent Medical Care" in data["reply_text"]
    assert data["suggested_specialty"] == "Emergency Medicine"
