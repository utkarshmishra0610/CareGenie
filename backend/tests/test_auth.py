from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient):
    """Test successful user registration."""
    payload = {
        "email": "aarav.sharma@example.com",
        "username": "aarav",
        "full_name": "Aarav Sharma",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "aarav.sharma@example.com"
    assert data["username"] == "aarav"
    assert data["full_name"] == "Aarav Sharma"
    assert data["preferred_language"] == "en"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email(client: TestClient):
    """Test rejection when registering with an existing email."""
    payload = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "Password123!"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    payload_dup = {
        "email": "duplicate@example.com",
        "username": "user2",
        "password": "Password123!"
    }
    res2 = client.post("/api/auth/register", json=payload_dup)
    assert res2.status_code == 400
    assert "email" in res2.json()["detail"].lower()


def test_register_duplicate_username(client: TestClient):
    """Test rejection when registering with an existing username."""
    payload1 = {
        "email": "user1@example.com",
        "username": "unique_name",
        "password": "Password123!"
    }
    res1 = client.post("/api/auth/register", json=payload1)
    assert res1.status_code == 201

    payload2 = {
        "email": "user2@example.com",
        "username": "unique_name",
        "password": "Password123!"
    }
    res2 = client.post("/api/auth/register", json=payload2)
    assert res2.status_code == 400
    assert "username" in res2.json()["detail"].lower()


def test_login_success_json(client: TestClient):
    """Test user login via JSON endpoint returning JWT token."""
    # Register user first
    reg_payload = {
        "email": "login_test@example.com",
        "username": "login_user",
        "password": "MySecretPassword123!"
    }
    client.post("/api/auth/register", json=reg_payload)

    # Login with username
    login_res = client.post(
        "/api/auth/login",
        json={"username_or_email": "login_user", "password": "MySecretPassword123!"}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Login with email
    login_email_res = client.post(
        "/api/auth/login",
        json={"username_or_email": "login_test@example.com", "password": "MySecretPassword123!"}
    )
    assert login_email_res.status_code == 200


def test_login_invalid_credentials(client: TestClient):
    """Test login with wrong password."""
    reg_payload = {
        "email": "wrong_pw@example.com",
        "username": "wrong_pw_user",
        "password": "CorrectPassword123!"
    }
    client.post("/api/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/auth/login",
        json={"username_or_email": "wrong_pw_user", "password": "WrongPassword!"}
    )
    assert login_res.status_code == 401


def test_login_oauth2_form(client: TestClient):
    """Test OAuth2 standard form-data login endpoint for Swagger UI."""
    reg_payload = {
        "email": "oauth_test@example.com",
        "username": "oauth_user",
        "password": "OAuthPassword123!"
    }
    client.post("/api/auth/register", json=reg_payload)

    token_res = client.post(
        "/api/auth/token",
        data={"username": "oauth_user", "password": "OAuthPassword123!"}
    )
    assert token_res.status_code == 200
    assert "access_token" in token_res.json()


def test_get_current_user_profile(client: TestClient):
    """Test accessing protected /api/users/me endpoint with Bearer token."""
    reg_payload = {
        "email": "profile_test@example.com",
        "username": "profile_user",
        "full_name": "Profile Tester",
        "password": "ProfilePassword123!",
        "preferred_language": "hi"
    }
    client.post("/api/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/auth/login",
        json={"username_or_email": "profile_user", "password": "ProfilePassword123!"}
    )
    token = login_res.json()["access_token"]

    # Request without token -> 401
    unauth_res = client.get("/api/users/me")
    assert unauth_res.status_code == 401

    # Request with valid Bearer token -> 200
    headers = {"Authorization": f"Bearer {token}"}
    auth_res = client.get("/api/users/me", headers=headers)
    assert auth_res.status_code == 200
    user_data = auth_res.json()
    assert user_data["username"] == "profile_user"
    assert user_data["email"] == "profile_test@example.com"
    assert user_data["preferred_language"] == "hi"


def test_update_current_user_profile(client: TestClient):
    """Test updating user profile details via PATCH /api/users/me."""
    reg_payload = {
        "email": "update_test@example.com",
        "username": "update_user",
        "password": "UpdatePassword123!"
    }
    client.post("/api/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/auth/login",
        json={"username_or_email": "update_user", "password": "UpdatePassword123!"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "full_name": "Updated Name",
        "preferred_language": "hi"
    }
    patch_res = client.patch("/api/users/me", json=update_payload, headers=headers)
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["full_name"] == "Updated Name"
    assert updated_data["preferred_language"] == "hi"
