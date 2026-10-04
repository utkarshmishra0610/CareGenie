"""Comprehensive End-to-End System Test Suite.

Validates the full patient journey across:
1. User registration & profile management
2. OAuth2 / JWT authentication & profile updates
3. Bilingual localization verification (EN & HI)
4. Conversational symptom checker with adaptive clinical follow-ups
5. Machine learning disease risk prediction finalization
6. Healthcare provider discovery with specialty matching & proximity
7. Patient health history archival, healthcare query tracking, and deletion
8. Red-flag emergency triage escalation workflow
"""
from tests.test_chat import get_auth_token


def test_complete_patient_journey_e2e(client):
    """Verifies the complete end-to-end user and clinical journey."""
    # Step 1: User Registration
    reg_payload = {
        "email": "e2e_patient@example.com",
        "username": "e2e_patient",
        "password": "SecurePassword123!",
        "full_name": "Aarav Sharma",
        "preferred_language": "en",
    }
    reg_resp = client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, reg_resp.text
    user_data = reg_resp.json()
    assert user_data["username"] == "e2e_patient"
    assert user_data["email"] == "e2e_patient@example.com"

    # Step 2: Authentication via OAuth2 form
    login_resp = client.post(
        "/api/auth/token",
        data={"username": "e2e_patient@example.com", "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Fetch & Update Profile via PATCH /api/users/me
    me_resp = client.get("/api/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Aarav Sharma"

    update_resp = client.patch(
        "/api/users/me",
        json={"full_name": "Aarav K. Sharma", "preferred_language": "en"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["full_name"] == "Aarav K. Sharma"

    # Step 4: Verify Multilingual Support endpoints
    lang_resp = client.get("/api/languages")
    assert lang_resp.status_code == 200
    langs = {l["code"] for l in lang_resp.json()}
    assert "en" in langs and "hi" in langs

    en_bundle = client.get("/api/localization/en").json()
    hi_bundle = client.get("/api/localization/hi").json()
    assert "app_name" in en_bundle and "app_name" in hi_bundle

    # Step 5: Start English Consultation Chat Session
    session_res = client.post(
        "/api/chat/sessions",
        json={"title": "Respiratory & Fever Consultation", "language": "en"},
        headers=headers,
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]

    # Step 6: Patient Turn 1 - Symptom presentation (cough & high fever)
    turn1_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "I have been coughing persistently and have a high fever"},
        headers=headers,
    )
    assert turn1_res.status_code == 200
    t1 = turn1_res.json()
    assert t1["detected_emergency"] is False
    extracted_symptoms = [str(s).lower() for s in t1["structured_symptoms"]["symptoms"]]
    assert any("cough" in s or "fever" in s for s in extracted_symptoms)
    assert t1["follow_up_question"] is not None or len(t1["missing_fields"]) > 0

    # Step 7: Patient Turn 2 - Providing duration and severity
    turn2_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "It started 5 days ago and is moderate to severe, also feeling fatigued"},
        headers=headers,
    )
    assert turn2_res.status_code == 200

    # Step 8: Finalize Assessment with ML Prediction Engine
    finalize_res = client.post(
        f"/api/chat/sessions/{session_id}/finalize-assessment",
        headers=headers,
    )
    assert finalize_res.status_code == 200
    final_payload = finalize_res.json()
    assessment = final_payload["assessment"]
    prediction = final_payload["prediction"]

    assert assessment["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert assessment["predicted_condition"] is not None
    assert len(prediction["top_conditions"]) > 0
    suggested_specialty = assessment["suggested_specialty"]
    assert len(suggested_specialty) > 0

    # Step 9: Find Nearby Healthcare Facilities matching the suggested specialty
    care_resp = client.get(
        f"/api/healthcare/nearby?specialty={suggested_specialty}&emergency_only=false",
        headers=headers,
    )
    assert care_resp.status_code == 200
    care_data = care_resp.json()
    assert care_data["total_count"] > 0
    facilities = care_data["facilities"]
    spec_tokens = [t.strip().lower() for t in suggested_specialty.split("/")]
    assert any(
        any(t in s.lower() or s.lower() in t for s in f["specialties"] for t in spec_tokens)
        for f in facilities
    )
    first_facility = facilities[0]

    # Step 10: Associate facility search with patient assessment history
    add_search_resp = client.post(
        f"/api/history/{assessment['id']}/searches",
        json={
            "facility_name": first_facility["name"],
            "specialty": suggested_specialty,
            "location": first_facility["address"],
            "distance": f"{first_facility.get('distance_km', 5.0)} km",
            "phone": first_facility["phone"],
        },
        headers=headers,
    )
    assert add_search_resp.status_code == 200
    updated_assessment = add_search_resp.json()
    assert len(updated_assessment["healthcare_searches"]) >= 1

    # Step 11: Inspect Patient History
    history_res = client.get("/api/history", headers=headers)
    assert history_res.status_code == 200
    history_list = history_res.json()
    assert len(history_list) >= 1
    found_rec = next(item for item in history_list if item["id"] == assessment["id"])
    assert found_rec["predicted_condition"] == assessment["predicted_condition"]

    # Step 12: Delete assessment from history
    del_res = client.delete(f"/api/history/{assessment['id']}", headers=headers)
    assert del_res.status_code == 204

    # Verify deletion
    verify_del = client.get(f"/api/history/{assessment['id']}", headers=headers)
    assert verify_del.status_code == 404


def test_hindi_multilingual_consultation_e2e(client):
    """Verifies end-to-end Hindi consultation with Devanagari symptoms and ML evaluation."""
    token = get_auth_token(client, "hindi_e2e_user", "hindi_e2e@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Start Hindi session
    session_res = client.post(
        "/api/chat/sessions",
        json={"title": "स्वास्थ्य परामर्श (Hindi Consult)", "language": "hi"},
        headers=headers,
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]

    # Hindi consultation with Devanagari symptoms
    turn_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "मुझे पिछले 3 दिनों से तेज़ बुखार और खांसी है"},
        headers=headers,
    )
    assert turn_res.status_code == 200
    data = turn_res.json()
    extracted = [str(s).lower() for s in data["structured_symptoms"]["symptoms"]]
    assert any("fever" in s or "cough" in s for s in extracted)

    # Finalize Hindi assessment
    finalize_res = client.post(
        f"/api/chat/sessions/{session_id}/finalize-assessment",
        headers=headers,
    )
    assert finalize_res.status_code == 200
    final_data = finalize_res.json()
    assert len(final_data["prediction"]["general_precautions"]) > 0


def test_emergency_triage_escalation_e2e(client):
    """Verifies instant emergency detection and crisis referral."""
    token = get_auth_token(client, "er_triage_user", "er_triage@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    session_res = client.post(
        "/api/chat/sessions",
        json={"title": "Chest Emergency", "language": "en"},
        headers=headers,
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]

    # Send critical red-flag emergency symptoms
    turn_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "I have severe crushing chest pain radiating to left arm and cannot breathe"},
        headers=headers,
    )
    assert turn_res.status_code == 200
    data = turn_res.json()
    assert data["detected_emergency"] is True
    assert "112" in data["reply_text"] or "911" in data["reply_text"] or data["emergency_advice"] is not None

    # Query 24x7 emergency facilities immediately
    er_facilities = client.get(
        "/api/healthcare/nearby?emergency_only=true",
        headers=headers,
    ).json()
    assert er_facilities["total_count"] > 0
    assert all(f["is_emergency_24x7"] is True for f in er_facilities["facilities"])
