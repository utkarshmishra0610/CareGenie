"""Unit and integration tests for Phase 7 ML Disease Risk Prediction."""
from app.prediction.predictor import DiseasePredictor
from app.schemas.prediction import PredictionRequest


def test_disease_predictor_model_loaded():
    """Verify model loads successfully from artifact or fallback."""
    candidates = DiseasePredictor.predict_candidate_conditions(["fever", "coughing"], top_k=3)
    assert len(candidates) > 0
    assert all(c.confidence_score > 0 for c in candidates)
    assert all(c.specialty != "" for c in candidates)


def test_colloquial_symptom_normalization():
    """Verify colloquial user phrases (e.g., 'body pain') map to dataset features."""
    norm = DiseasePredictor.normalize_user_symptoms(["body pain", "stomach ache", "high fever"])
    assert "muscle joint pain" in norm
    assert "stomach pain" in norm
    assert "fever" in norm


def test_risk_evaluation_tiers():
    """Verify clinical risk tiers: LOW, MODERATE, HIGH, CRITICAL."""
    # 1. Critical tier (emergency sign)
    cand_crit = DiseasePredictor.predict_candidate_conditions(["chest pain"])
    crit_level, crit_score, _, crit_spec, _ = DiseasePredictor.evaluate_risk(
        symptoms=["chest pain", "crushing pressure"],
        severity="severe",
        duration="1 hour",
        age=55,
        gender="male",
        top_candidates=cand_crit,
        language="en",
    )
    assert crit_level == "CRITICAL"
    assert crit_score >= 90.0
    assert crit_spec == "Emergency Medicine"

    # 2. High tier (severe intensity, non-emergency)
    cand_high = DiseasePredictor.predict_candidate_conditions(["fever", "headache", "vomiting"])
    high_level, high_score, _, _, _ = DiseasePredictor.evaluate_risk(
        symptoms=["fever", "headache", "vomiting"],
        severity="severe",
        duration="5 days",
        age=30,
        gender="female",
        top_candidates=cand_high,
        language="en",
    )
    assert high_level == "HIGH"
    assert high_score >= 70.0

    # 3. Low tier (mild, single symptom, short duration)
    cand_low = DiseasePredictor.predict_candidate_conditions(["runny nose"])
    low_level, low_score, _, _, _ = DiseasePredictor.evaluate_risk(
        symptoms=["runny nose"],
        severity="mild",
        duration="1 day",
        age=25,
        gender="female",
        top_candidates=cand_low,
        language="en",
    )
    assert low_level in ["LOW", "MODERATE"]
    assert low_score < 60.0


def test_hindi_language_localization():
    """Verify Hindi localized rationale, precautions, and disclaimer."""
    req = PredictionRequest(
        symptoms=["fever", "coughing"],
        severity="moderate",
        duration="2 days",
        language="hi",
    )
    response = DiseasePredictor.assess(req)
    assert "चिकित्सीय" in response.risk_rationale or "लक्षण" in response.risk_rationale
    assert len(response.general_precautions) > 0
    assert "सलाह" in response.general_precautions[2] or "दवा" in response.general_precautions[2]
    assert "प्रारंभिक" in response.disclaimer


def test_predict_endpoint_success(client):
    """Verify POST /api/assessment/predict endpoint returns compliant schema."""
    payload = {
        "symptoms": ["fever", "headache", "body pain"],
        "severity": "moderate",
        "duration": "3 days",
        "age": 28,
        "gender": "female",
        "language": "en",
    }
    res = client.post("/api/assessment/predict", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "risk_level" in data
    assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 100.0
    assert len(data["top_conditions"]) > 0
    assert data["recommended_specialty"] != ""
    assert len(data["general_precautions"]) >= 3
    assert "disclaimer" in data
    assert "preliminary" in data["disclaimer"].lower() or "not a medical diagnosis" in data["disclaimer"].lower()


def test_predict_endpoint_emergency(client):
    """Verify emergency symptoms via API trigger CRITICAL tier with emergency specialty."""
    payload = {
        "symptoms": ["crushing chest pain", "difficulty breathing"],
        "severity": "severe",
        "duration": "30 minutes",
        "language": "en",
    }
    res = client.post("/api/assessment/predict", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["risk_level"] == "CRITICAL"
    assert data["risk_score"] >= 90.0
    assert data["recommended_specialty"] == "Emergency Medicine"
    assert any("911" in p or "112" in p or "emergency" in p.lower() for p in data["general_precautions"])


def test_predict_endpoint_validation_error(client):
    """Verify empty symptoms list triggers 422 Unprocessable Entity."""
    payload = {
        "symptoms": [],
        "severity": "mild",
    }
    res = client.post("/api/assessment/predict", json=payload)
    assert res.status_code == 422
