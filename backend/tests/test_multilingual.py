"""Unit and integration tests for Phase 9 Multilingual Support (English & Hindi)."""
from app.ai.service import check_emergency
from app.localization.i18n import translate
from app.prediction.symptom_data import find_matching_symptoms
from tests.test_chat import get_auth_token


def test_devanagari_symptom_extraction():
    """Verify Hindi Devanagari text correctly extracts clinical symptom entities."""
    hindi_text = "मुझे 3 दिन से तेज बुखार और सिर दर्द है"
    matches = find_matching_symptoms(hindi_text)
    assert "fever" in matches
    assert "headache" in matches


def test_hinglish_transliterated_symptom_extraction():
    """Verify Hinglish (Latin script) colloquial symptom extraction."""
    hinglish_text = "mujhe kal se tez bukhar, khansi aur badan dard ho raha hai"
    matches = find_matching_symptoms(hinglish_text)
    assert "fever" in matches
    assert "coughing" in matches
    assert "muscle joint pain" in matches


def test_hindi_emergency_red_flags():
    """Verify Hindi emergency query triggers urgent triage."""
    hindi_emergency = "अचानक सीने में तेज दर्द हो रहा है और सांस फूलना शुरू हो गया"
    is_emergency, reasons, advice = check_emergency([], hindi_emergency)
    assert is_emergency is True
    assert len(reasons) > 0


def test_i18n_translation_lookup():
    """Verify localization translation lookup helper."""
    en_tag = translate("app_tagline", lang="en")
    hi_tag = translate("app_tagline", lang="hi")

    assert "Preliminary" in en_tag
    assert "प्रारंभिक" in hi_tag


def test_get_languages_endpoint(client):
    """Verify GET /api/languages returns supported languages."""
    res = client.get("/api/languages")
    assert res.status_code == 200
    languages = res.json()
    codes = [l["code"] for l in languages]
    assert "en" in codes
    assert "hi" in codes


def test_get_localization_bundle_endpoints(client):
    """Verify GET /api/localization/{lang} returns dictionary or 404 for invalid."""
    # 1. English bundle
    res_en = client.get("/api/localization/en")
    assert res_en.status_code == 200
    assert "disclaimer" in res_en.json()

    # 2. Hindi bundle
    res_hi = client.get("/api/localization/hi")
    assert res_hi.status_code == 200
    assert "प्रारंभिक" in res_hi.json()["disclaimer"]

    # 3. Invalid language
    res_inv = client.get("/api/localization/french")
    assert res_inv.status_code == 404


def test_hindi_chat_consultation_turn(client):
    """Verify full interactive chat turn in Hindi language."""
    token = get_auth_token(client, "hindi_user", "hindi@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Hindi session
    create_res = client.post(
        "/api/chat/sessions",
        json={"title": "Hindi Consult", "language": "hi"},
        headers=headers,
    )
    assert create_res.status_code == 201
    session_id = create_res.json()["id"]

    # 2. Interact in Hindi
    interact_res = client.post(
        f"/api/chat/sessions/{session_id}/interact",
        json={"content": "मुझे दो दिन से बुखार और पेट दर्द है"},
        headers=headers,
    )
    assert interact_res.status_code == 200
    data = interact_res.json()

    assert "fever" in data["structured_symptoms"]["symptoms"]
    assert "stomach pain" in data["structured_symptoms"]["symptoms"]
    # Verify assistant response is in Hindi
    assert "लक्षणों" in data["reply_text"] or "परामर्श" in data["reply_text"]
    assert "अस्वीकरण" in data["disclaimer"] or "प्रारंभिक" in data["disclaimer"]


def test_regional_languages_extraction_and_bundles(client):
    """Verify Marathi, Bengali, Telugu, Tamil, Gujarati, Kannada, Punjabi symptom extraction and bundle retrieval."""
    # 1. Marathi extraction
    mr_matches = find_matching_symptoms("मला २ दिवसांपासून ताप आणि पोटदुखी आहे")
    assert "fever" in mr_matches
    assert "stomach pain" in mr_matches

    # 2. Bengali extraction
    bn_matches = find_matching_symptoms("আমার তিন দিন ধরে জ্বর এবং মাথা ব্যথা")
    assert "fever" in bn_matches
    assert "headache" in bn_matches

    # 3. Telugu extraction
    te_matches = find_matching_symptoms("నాకు తీవ్రమైన జ్వరం మరియు దగ్గు ఉంది")
    assert "fever" in te_matches
    assert "coughing" in te_matches

    # 4. Tamil extraction
    ta_matches = find_matching_symptoms("எனக்கு இரண்டு நாட்களாக காய்ச்சல் மற்றும் தலைவலி உள்ளது")
    assert "fever" in ta_matches
    assert "headache" in ta_matches

    # 5. Gujarati extraction
    gu_matches = find_matching_symptoms("મને બે દિવસથી તાવ અને માથાનો દુખાવો છે")
    assert "fever" in gu_matches
    assert "headache" in gu_matches

    # 6. Kannada extraction
    kn_matches = find_matching_symptoms("ನನಗೆ ತೀವ್ರ ಜ್ವರ ಮತ್ತು ಕೆಮ್ಮು ಇದೆ")
    assert "fever" in kn_matches
    assert "coughing" in kn_matches

    # 7. Punjabi extraction
    pa_matches = find_matching_symptoms("ਮੈਨੂੰ ਦੋ ਦਿਨਾਂ ਤੋਂ ਬੁਖਾਰ ਅਤੇ ਸਿਰ ਦਰਦ ਹੈ")
    assert "fever" in pa_matches
    assert "headache" in pa_matches

    # Verify bundles for all regional languages return status 200 with required fields
    for lang in ["mr", "bn", "te", "ta", "gu", "kn", "pa"]:
        bundle_res = client.get(f"/api/localization/{lang}")
        assert bundle_res.status_code == 200
        bundle = bundle_res.json()
        assert "disclaimer" in bundle
        assert "app_name" in bundle
        assert "ui" in bundle

