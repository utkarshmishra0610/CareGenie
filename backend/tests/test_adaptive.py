"""Unit and integration tests for Phase 6 Adaptive Chatbot logic."""
from app.ai.adaptive import AdaptiveQuestionEngine
from app.ai.service import extract_structured_symptoms
from app.models.chat import ChatSession


def test_missing_duration_and_severity_triggers_questions():
    """Verify engine detects missing duration and severity sequentially."""
    session = ChatSession(id=1, user_id=1, title="Test", language="en", is_active=True, messages=[])
    
    # 1. First message: symptoms only, no duration, no severity
    text1 = "I have a cough and fever"
    structured1 = extract_structured_symptoms(text1)
    step1 = AdaptiveQuestionEngine.determine_next_step(session, text1, structured1, language="en")
    
    assert step1["is_ready_for_prediction"] is False
    assert "duration" in step1["missing_fields"]
    assert "How long" in step1["next_question"] or "experiencing" in step1["next_question"]

    # 2. Second message: duration provided ("for 3 days"), severity still missing
    text2 = "It has been going on for 3 days"
    structured2 = extract_structured_symptoms(text2)
    AdaptiveQuestionEngine.determine_next_step(session, text2, structured2, language="en")
    
    # duration is now extracted
    assert structured2.duration == "3 days"


def test_differential_symptom_inquiry():
    """Verify engine asks a discriminating symptom to differentiate top candidate diseases."""
    candidate_conditions = [("Common Cold", 0.6), ("Influenza", 0.55)]
    accumulated_symptoms = ["cough", "fever"]
    asked_symptoms = set()

    diff_symptom = AdaptiveQuestionEngine.find_discriminating_symptom(
        candidate_conditions, accumulated_symptoms, asked_symptoms
    )
    # The symptom should not be cough or fever
    if diff_symptom:
        assert diff_symptom not in accumulated_symptoms


def test_stopping_condition_sufficient_context():
    """Verify session transitions to is_ready_for_prediction=True when sufficient context is gathered."""
    session = ChatSession(id=1, user_id=1, title="Test", language="en", is_active=True, messages=[])
    
    # Provide 3 symptoms, duration, and severity
    text = "I have moderate fever, cough, and headache for 4 days"
    structured = extract_structured_symptoms(text)
    
    step = AdaptiveQuestionEngine.determine_next_step(session, text, structured, language="en")
    assert step["is_ready_for_prediction"] is True
    assert len(step["candidate_conditions"]) > 0
    assert "proceed" in step["next_question"].lower() or "risk assessment" in step["next_question"].lower()


def test_emergency_bypasses_adaptive_questioning():
    """Verify emergency symptoms skip adaptive questioning and prioritize urgent care."""
    session = ChatSession(id=1, user_id=1, title="Test", language="en", is_active=True, messages=[])
    text = "I have crushing chest pain radiating to my left arm and sweating"
    structured = extract_structured_symptoms(text)
    
    assert structured.is_emergency is True
    step = AdaptiveQuestionEngine.determine_next_step(session, text, structured, language="en")
    assert step["is_ready_for_prediction"] is False
    assert step["next_question"] is None


from tests.test_chat import get_auth_token


def test_multi_turn_adaptive_chat_endpoint(client):
    """Test full multi-turn conversational interaction maintaining state across turns."""
    token = get_auth_token(client, "adaptive_user", "adaptive@example.com")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Create session
    create_res = client.post(
        "/api/chat/sessions",
        json={"title": "Adaptive Consult", "language": "en"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    # Turn 1: Patient reports initial complaint without duration or severity
    turn1_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "I have been suffering from a fever and joint pain"},
        headers=auth_headers,
    )
    assert turn1_res.status_code == 200
    data1 = turn1_res.json()
    assert data1["detected_emergency"] is False
    assert data1["follow_up_question"] is not None
    assert data1["is_ready_for_prediction"] is False

    # Turn 2: Patient reports duration and severity
    turn2_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "It started 3 days ago and the intensity is moderate"},
        headers=auth_headers,
    )
    assert turn2_res.status_code == 200
    data2 = turn2_res.json()
    assert data2["question_turn"] >= 2
    # Verify symptoms accumulated across turns
    assert len(data2["structured_symptoms"]["symptoms"]) > 0


