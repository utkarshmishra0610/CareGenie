"""End-to-End integration test covering Chat -> Adaptive AI -> ML Prediction -> Patient History."""
from tests.test_chat import get_auth_token


def test_full_clinical_consultation_lifecycle(client):
    """Verifies complete end-to-end workflow from user login to history persistence."""
    # 1. Authenticate user
    token = get_auth_token(client, "lifecycle_user", "lifecycle@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Initialize chat session
    session_res = client.post(
        "/api/chat/sessions",
        json={"title": "Lifecycle Consult", "language": "en"},
        headers=headers,
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]

    # 3. Turn 1: Patient reports fever and headache
    turn1_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "I am experiencing fever and severe headache"},
        headers=headers,
    )
    assert turn1_res.status_code == 200
    turn1_data = turn1_res.json()
    assert turn1_data["detected_emergency"] is False
    assert len(turn1_data["structured_symptoms"]["symptoms"]) > 0

    # 4. Turn 2: Patient reports duration
    turn2_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "It has been going on for 4 days and feels severe"},
        headers=headers,
    )
    assert turn2_res.status_code == 200

    # 5. Finalize assessment: Executes ML risk prediction and saves to patient history
    finalize_res = client.post(
        f"/api/chat/sessions/{session_id}/finalize-assessment",
        headers=headers,
    )
    assert finalize_res.status_code == 200
    final_data = finalize_res.json()

    assert "assessment" in final_data
    assert "prediction" in final_data
    assert "closing_message" in final_data

    assessment = final_data["assessment"]
    assert assessment["id"] > 0
    assert assessment["risk_level"] in ["HIGH", "MODERATE", "CRITICAL"]
    assert assessment["predicted_condition"] is not None
    assert assessment["suggested_specialty"] != ""

    prediction = final_data["prediction"]
    assert len(prediction["top_conditions"]) > 0
    assert prediction["risk_score"] > 0.0

    # 6. Verify record is accessible in Patient History
    history_res = client.get("/api/history", headers=headers)
    assert history_res.status_code == 200
    history_items = history_res.json()
    assert len(history_items) >= 1
    assert any(h["id"] == assessment["id"] for h in history_items)

    detail_res = client.get(f"/api/history/{assessment['id']}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["predicted_condition"] == assessment["predicted_condition"]

    # 7. Verify session is now closed and contains the closing message
    sess_detail = client.get(f"/api/chat/sessions/{session_id}", headers=headers)
    assert sess_detail.status_code == 200
    assert sess_detail.json()["is_active"] is False
    messages = sess_detail.json()["messages"]
    assert len(messages) >= 4  # User1, Assis1, User2, Assis2, Closing
    assert any("Assessment Completed" in m["content"] or "Risk Assessment Summary" in m["content"] for m in messages)


def test_finalize_empty_session_error(client):
    """Verifies finalizing a session without reported symptoms returns 400."""
    token = get_auth_token(client, "empty_user", "empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(
        "/api/chat/sessions",
        json={"title": "Empty Session", "language": "en"},
        headers=headers,
    )
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    finalize_res = client.post(
        f"/api/chat/sessions/{session_id}/finalize-assessment",
        headers=headers,
    )
    assert finalize_res.status_code == 400
    assert "No recognizable health symptoms" in finalize_res.json()["detail"]
