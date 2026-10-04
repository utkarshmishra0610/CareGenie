from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, username: str, email: str) -> str:
    """Helper to register and log in a test user, returning the JWT token."""
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "ChatPassword123!",
            "full_name": "Chat User",
            "preferred_language": "en",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"username_or_email": username, "password": "ChatPassword123!"},
    )
    return res.json()["access_token"]


def test_create_and_list_chat_session(client: TestClient):
    """Test creating a chat session and listing user sessions."""
    token = get_auth_token(client, "chat_user1", "chat1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_payload = {"title": "Fever Evaluation", "language": "en"}
    create_res = client.post(
        "/api/chat/sessions", json=create_payload, headers=headers
    )
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["title"] == "Fever Evaluation"
    assert data["language"] == "en"
    assert data["is_active"] is True
    session_id = data["id"]

    # List sessions
    list_res = client.get("/api/chat/sessions", headers=headers)
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id
    assert sessions[0]["message_count"] == 0


def test_send_and_retrieve_messages(client: TestClient):
    """Test sending user and assistant messages and retrieving session history."""
    token = get_auth_token(client, "chat_user2", "chat2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create session
    session_res = client.post(
        "/api/chat/sessions", json={"language": "en"}, headers=headers
    )
    session_id = session_res.json()["id"]

    # Post user message
    msg1_payload = {
        "content": "I have had a fever and headache for 2 days.",
        "sender": "user",
        "extra_metadata": {"detected_symptoms": ["fever", "headache"]},
    }
    post_res1 = client.post(
        f"/api/chat/sessions/{session_id}/messages",
        json=msg1_payload,
        headers=headers,
    )
    assert post_res1.status_code == 201
    msg1 = post_res1.json()
    assert msg1["sender"] == "user"
    assert msg1["content"] == "I have had a fever and headache for 2 days."
    assert msg1["extra_metadata"]["detected_symptoms"] == ["fever", "headache"]

    # Post assistant follow-up question
    msg2_payload = {
        "content": "How high has the fever been, and do you have chills or nausea?",
        "sender": "assistant",
        "extra_metadata": {"intent": "adaptive_questioning"},
    }
    post_res2 = client.post(
        f"/api/chat/sessions/{session_id}/messages",
        json=msg2_payload,
        headers=headers,
    )
    assert post_res2.status_code == 201

    # Get session details with full message history
    detail_res = client.get(f"/api/chat/sessions/{session_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["message_count"] == 2
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["sender"] == "user"
    assert detail["messages"][1]["sender"] == "assistant"

    # Also test messages list endpoint
    msgs_res = client.get(
        f"/api/chat/sessions/{session_id}/messages", headers=headers
    )
    assert msgs_res.status_code == 200
    assert len(msgs_res.json()) == 2


def test_delete_chat_session(client: TestClient):
    """Test deleting a chat session and verifying deletion."""
    token = get_auth_token(client, "chat_user3", "chat3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    session_res = client.post(
        "/api/chat/sessions", json={"title": "To Delete"}, headers=headers
    )
    session_id = session_res.json()["id"]

    # Add message
    client.post(
        f"/api/chat/sessions/{session_id}/messages",
        json={"content": "Hello", "sender": "user"},
        headers=headers,
    )

    # Delete session
    del_res = client.delete(f"/api/chat/sessions/{session_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify not found
    get_res = client.get(f"/api/chat/sessions/{session_id}", headers=headers)
    assert get_res.status_code == 404


def test_chat_session_user_isolation(client: TestClient):
    """Verify that User 1 cannot access or post messages to User 2's session."""
    token1 = get_auth_token(client, "alice_chat", "alice@example.com")
    token2 = get_auth_token(client, "bob_chat", "bob@example.com")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Alice creates session
    s_res = client.post(
        "/api/chat/sessions", json={"title": "Alice Consultation"}, headers=headers1
    )
    alice_session_id = s_res.json()["id"]

    # Bob tries to access Alice's session -> 404
    bob_get = client.get(
        f"/api/chat/sessions/{alice_session_id}", headers=headers2
    )
    assert bob_get.status_code == 404

    # Bob tries to post message to Alice's session -> 404
    bob_post = client.post(
        f"/api/chat/sessions/{alice_session_id}/messages",
        json={"content": "Hacking in", "sender": "user"},
        headers=headers2,
    )
    assert bob_post.status_code == 404

    # Bob tries to delete Alice's session -> 404
    bob_del = client.delete(
        f"/api/chat/sessions/{alice_session_id}", headers=headers2
    )
    assert bob_del.status_code == 404


def test_unauthenticated_chat_access(client: TestClient):
    """Test that requests without JWT tokens are rejected with 401."""
    assert client.get("/api/chat/sessions").status_code == 401
    assert client.post("/api/chat/sessions", json={}).status_code == 401
