from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, username: str, email: str) -> str:
    """Helper to register and log in a test user, returning the JWT token."""
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "TestPassword123!",
            "full_name": "Test User",
            "preferred_language": "en",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"username_or_email": username, "password": "TestPassword123!"},
    )
    return res.json()["access_token"]


def test_create_and_list_assessment(client: TestClient):
    """Test saving an assessment and listing user history."""
    token = get_auth_token(client, "user_hist", "hist@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    assessment_payload = {
        "symptoms": ["fever", "headache", "red rash"],
        "duration": "3 days",
        "severity": "moderate",
        "predicted_condition": "Dengue",
        "risk_level": "Moderate",
        "ai_summary": "Patient presented with 3-day history of acute fever and headache with red rash.",
        "suggested_specialty": "General Physician",
        "healthcare_searches": [],
    }

    create_res = client.post("/api/history", json=assessment_payload, headers=headers)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["predicted_condition"] == "Dengue"
    assert created_data["symptoms"] == ["fever", "headache", "red rash"]
    assert "id" in created_data
    assessment_id = created_data["id"]

    # List history
    list_res = client.get("/api/history", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == assessment_id
    assert items[0]["duration"] == "3 days"


def test_get_assessment_details_and_delete(client: TestClient):
    """Test retrieving details of an assessment and then deleting it."""
    token = get_auth_token(client, "user_detail", "detail@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "symptoms": ["wheezing", "coughing"],
        "duration": "1 week",
        "severity": "mild",
        "predicted_condition": "Asthma",
        "risk_level": "Preliminary",
        "ai_summary": "Mild cough and wheezing.",
        "suggested_specialty": "Pulmonologist",
    }
    create_res = client.post("/api/history", json=payload, headers=headers)
    assessment_id = create_res.json()["id"]

    # Get details
    get_res = client.get(f"/api/history/{assessment_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["predicted_condition"] == "Asthma"

    # Delete
    del_res = client.delete(f"/api/history/{assessment_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify not found
    get_again = client.get(f"/api/history/{assessment_id}", headers=headers)
    assert get_again.status_code == 404


def test_add_healthcare_search_to_assessment(client: TestClient):
    """Test linking a healthcare facility search to a past assessment."""
    token = get_auth_token(client, "user_search", "search@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "symptoms": ["chest pain", "shortness breath"],
        "predicted_condition": "Coronary Heart Disease",
        "risk_level": "High",
        "suggested_specialty": "Cardiologist",
    }
    create_res = client.post("/api/history", json=payload, headers=headers)
    assessment_id = create_res.json()["id"]

    # Link healthcare search
    search_payload = {
        "facility_name": "Apollo Heart Institute",
        "specialty": "Cardiology",
        "location": "Central Delhi",
        "distance": "3.1 km",
        "phone": "+91-11-26925858",
    }
    search_res = client.post(
        f"/api/history/{assessment_id}/searches",
        json=search_payload,
        headers=headers,
    )
    assert search_res.status_code == 200
    updated_data = search_res.json()
    assert len(updated_data["healthcare_searches"]) == 1
    assert (
        updated_data["healthcare_searches"][0]["facility_name"]
        == "Apollo Heart Institute"
    )


def test_user_history_isolation(client: TestClient):
    """Verify that User 1 cannot view or delete User 2's assessment records."""
    token1 = get_auth_token(client, "patient1", "p1@example.com")
    token2 = get_auth_token(client, "patient2", "p2@example.com")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Patient 1 creates an assessment
    payload = {
        "symptoms": ["fever"],
        "predicted_condition": "Common cold",
    }
    create_res = client.post("/api/history", json=payload, headers=headers1)
    assessment_id = create_res.json()["id"]

    # Patient 2 tries to read Patient 1's assessment -> 404
    read_attempt = client.get(f"/api/history/{assessment_id}", headers=headers2)
    assert read_attempt.status_code == 404

    # Patient 2 tries to delete Patient 1's assessment -> 404
    del_attempt = client.delete(f"/api/history/{assessment_id}", headers=headers2)
    assert del_attempt.status_code == 404

    # Patient 2 listing history should be empty
    list2 = client.get("/api/history", headers=headers2)
    assert list2.status_code == 200
    assert len(list2.json()) == 0


def test_unauthenticated_history_access(client: TestClient):
    """Test that unauthorized requests are rejected with 401."""
    res = client.get("/api/history")
    assert res.status_code == 401
