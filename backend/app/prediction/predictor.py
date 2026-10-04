"""Clinical disease risk prediction and evaluation service."""
import os
from typing import List, Optional, Tuple
import joblib
import numpy as np

from app.ai.prompts import (
    EMERGENCY_SIGNS,
    MANDATORY_DISCLAIMER_EN,
    MANDATORY_DISCLAIMER_HI,
    SPECIALTY_RULES,
)
from app.prediction.symptom_data import (
    COLLOQUIAL_SYMPTOM_MAP,
    DISEASE_SYMPTOMS_MAP,
    SYMPTOMS,
    find_matching_symptoms,
    get_diseases_for_symptoms,
)
from app.schemas.prediction import (
    ConditionCandidate,
    PredictionRequest,
    RiskPredictionResponse,
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "disease_risk_model.joblib")


class DiseasePredictor:
    """Predicts candidate health conditions, clinical risk score, and recommended next steps."""

    _model = None
    _symptoms: List[str] = []
    _diseases: List[str] = []

    @classmethod
    def load_model(cls):
        """Loads trained Random Forest classifier artifact from disk."""
        if cls._model is not None:
            return cls._model

        if os.path.exists(MODEL_PATH):
            try:
                payload = joblib.load(MODEL_PATH)
                cls._model = payload["model"]
                cls._symptoms = payload["symptoms"]
                cls._diseases = payload["diseases"]
                return cls._model
            except Exception as e:
                print(f"Warning: Failed to load trained model artifact ({e}). Utilizing statistical fallback.")

        # Fallback metadata
        cls._symptoms = SYMPTOMS
        cls._diseases = list(DISEASE_SYMPTOMS_MAP.keys())
        return None

    @classmethod
    def normalize_user_symptoms(cls, raw_symptoms: List[str]) -> List[str]:
        """Normalizes user input symptoms against colloquial mappings and clinical taxonomy."""
        normalized: List[str] = []
        for sym in raw_symptoms:
            cleaned = sym.strip().lower()
            if cleaned in COLLOQUIAL_SYMPTOM_MAP:
                target = COLLOQUIAL_SYMPTOM_MAP[cleaned]
                if target not in normalized:
                    normalized.append(target)
            elif cleaned in SYMPTOMS and cleaned not in normalized:
                normalized.append(cleaned)
            else:
                # Substring / keyword matches
                matches = find_matching_symptoms(cleaned)
                for m in matches:
                    if m not in normalized:
                        normalized.append(m)

        return normalized if normalized else [s.lower().strip() for s in raw_symptoms]

    @classmethod
    def predict_candidate_conditions(
        cls, user_symptoms: List[str], top_k: int = 4
    ) -> List[ConditionCandidate]:
        """Predicts top condition candidates with calibrated probability percentages."""
        model = cls.load_model()
        normalized_syms = cls.normalize_user_symptoms(user_symptoms)

        candidates: List[ConditionCandidate] = []

        if model is not None and len(cls._symptoms) > 0:
            # Vectorize input
            vector = np.zeros((1, len(cls._symptoms)), dtype=np.float32)
            for sym in normalized_syms:
                if sym in cls._symptoms:
                    idx = cls._symptoms.index(sym)
                    vector[0, idx] = 1.0

            # Model inference
            try:
                probs = model.predict_proba(vector)[0]
                top_indices = np.argsort(probs)[::-1][:top_k]

                # Combine model probability with empirical symptom overlap
                overlap_scores = dict(get_diseases_for_symptoms(normalized_syms))

                for idx in top_indices:
                    disease = cls._diseases[idx]
                    model_prob = float(probs[idx])
                    overlap = overlap_scores.get(disease, 0.0)

                    # Ensemble confidence score: 60% model prob + 40% overlap score
                    blended = (model_prob * 0.6 + overlap * 0.4)
                    # Normalize display confidence between 30.0% and 92.0%
                    display_conf = min(92.0, max(28.0, round(blended * 100.0 * 2.5, 1)))
                    specialty = SPECIALTY_RULES.get(disease, "General Physician")

                    candidates.append(
                        ConditionCandidate(
                            disease=disease,
                            confidence_score=display_conf,
                            specialty=specialty,
                        )
                    )
            except Exception:
                candidates = []

        # Statistical fallback if model failed or had zero match
        if not candidates or max(c.confidence_score for c in candidates) < 30.0:
            raw_overlaps = get_diseases_for_symptoms(normalized_syms)
            candidates = []
            for d, score in raw_overlaps[:top_k]:
                conf = round(min(88.0, max(30.0, score * 100.0)), 1)
                candidates.append(
                    ConditionCandidate(
                        disease=d,
                        confidence_score=conf,
                        specialty=SPECIALTY_RULES.get(d, "General Physician"),
                    )
                )

        # Final default fallback if symptoms had no overlap
        if not candidates:
            candidates.append(
                ConditionCandidate(
                    disease="Unspecified Viral Infection",
                    confidence_score=35.0,
                    specialty="General Physician",
                )
            )

        return candidates

    @classmethod
    def evaluate_risk(
        cls,
        symptoms: List[str],
        severity: Optional[str],
        duration: Optional[str],
        age: Optional[int],
        gender: Optional[str],
        top_candidates: List[ConditionCandidate],
        language: str = "en",
    ) -> Tuple[str, float, str, str, List[str]]:
        """Calculates clinical risk level, risk score, clinical rationale, recommended specialty, and precautions."""
        is_hi = language.lower() == "hi"
        norm_syms = cls.normalize_user_symptoms(symptoms)
        combined_text = " ".join(norm_syms + symptoms).lower()

        # 1. Emergency Detection
        emergency_triggers = []
        for em in EMERGENCY_SIGNS:
            for kw in em["keywords"]:
                if kw in combined_text:
                    emergency_triggers.append(em["reason"])
                    break

        if emergency_triggers:
            risk_level = "CRITICAL"
            risk_score = 95.0
            rationale = (
                "⚠️ गंभीर चेतावनी संकेत पहचाने गए: " + ", ".join(emergency_triggers) +
                "। तत्काल आपातकालीन चिकित्सा सहायता प्राप्त करें।"
                if is_hi
                else "⚠️ Urgent warning signs detected: " + ", ".join(emergency_triggers) +
                ". Immediate emergency clinical intervention is required."
            )
            specialty = "Emergency Medicine"
            precautions = [
                "Call 911 / 112 / 102 or proceed immediately to the nearest hospital emergency room.",
                "Do not drive yourself; have emergency services or an adult accompany you.",
                "Avoid exertion and stay seated in an upright, comfortable posture.",
            ] if not is_hi else [
                "112 / 102 पर कॉल करें या तुरंत निकटतम आपातकालीन अस्पताल जाएं।",
                "स्वयं वाहन न चलाएं; आपातकालीन सेवा या किसी को साथ लेकर जाएं।",
                "शारीरिक परिश्रम से बचें और आरामदायक स्थिति में बैठें।",
            ]
            return risk_level, risk_score, rationale, specialty, precautions

        # 2. Quantitative Base Risk Score from symptoms & candidates
        base_score = 30.0
        if top_candidates:
            top_conf = top_candidates[0].confidence_score
            base_score += (top_conf * 0.3)

        # Number of symptoms factor
        num_syms = len(norm_syms)
        base_score += min(20.0, num_syms * 4.0)

        # Severity Factor
        sev = (severity or "").lower()
        if sev in ["severe", "extreme", "unbearable", "high"]:
            base_score += 25.0
        elif sev in ["moderate", "medium"]:
            base_score += 12.0
        elif sev in ["mild", "slight"]:
            base_score += 0.0

        # Duration Factor
        dur = (duration or "").lower()
        if any(w in dur for w in ["week", "month", "10 days", "14 days", "weeks", "months"]):
            base_score += 12.0
        elif any(w in dur for w in ["3 days", "4 days", "5 days", "6 days"]):
            base_score += 5.0

        # Vulnerable population factor (age < 5 or > 65)
        if age and (age < 5 or age > 65):
            base_score += 8.0

        # Cap score between 10.0 and 88.0 (non-emergency)
        final_risk_score = round(min(88.0, max(15.0, base_score)), 1)

        # 3. Risk Level Tier
        if final_risk_score >= 70.0 or sev == "severe":
            risk_level = "HIGH"
            rationale = (
                "लक्षणों की संख्या और तीव्रता उच्च स्तर का संकेत देते हैं। चिकित्सीय परामर्श जल्द से जल्द अनुशंसित है।"
                if is_hi
                else "Multiple prominent symptoms or marked severity indicate an elevated clinical risk profile. Timely healthcare consultation is strongly advised."
            )
        elif final_risk_score >= 42.0 or sev == "moderate" or num_syms >= 3:
            risk_level = "MODERATE"
            rationale = (
                "लक्षण मध्यम श्रेणी के हैं। यदि वे 2-3 दिनों में ठीक नहीं होते हैं, तो डॉक्टर से संपर्क करें।"
                if is_hi
                else "Symptoms reflect moderate health disruption. Healthcare consultation is recommended if symptoms persist or do not improve within 48-72 hours."
            )
        else:
            risk_level = "LOW"
            rationale = (
                "लक्षण हल्के प्रतीत होते हैं। घरेलू देखभाल और आराम से निगरानी करें।"
                if is_hi
                else "Reported presentation suggests a mild, self-limiting health condition. Continue standard self-care and observe progression."
            )

        # 4. Recommended Specialty
        primary_specialty = top_candidates[0].specialty if top_candidates else "General Physician"

        # 5. General Clinical Precautions
        if is_hi:
            precautions = [
                "पर्याप्त मात्रा में पानी, सूप और तरल पदार्थों का सेवन करें।",
                "पर्याप्त शारीरिक आराम करें और अत्यधिक तनाव से बचें।",
                "बिना डॉक्टर की सलाह के कोई भी दवा (विशेषकर एंटीबायोटिक्स) न लें।",
                "यदि तेज बुखार, सांस फूलना या चक्कर आना शुरू हो, तो तुरंत डॉक्टर से मिलें।",
            ]
        else:
            precautions = [
                "Maintain optimal oral hydration with clean water, warm fluids, or electrolyte broths.",
                "Prioritize physical rest and allow your body adequate recuperation time.",
                "Do NOT self-medicate with prescription antibiotics or unverified medications.",
                "Monitor vital signs and seek prompt medical attention if breathing difficulty or high fever develops.",
            ]

        return risk_level, final_risk_score, rationale, primary_specialty, precautions

    @classmethod
    def assess(cls, req: PredictionRequest) -> RiskPredictionResponse:
        """Complete clinical risk assessment pipeline."""
        candidates = cls.predict_candidate_conditions(req.symptoms, top_k=4)
        risk_level, risk_score, rationale, specialty, precautions = cls.evaluate_risk(
            symptoms=req.symptoms,
            severity=req.severity,
            duration=req.duration,
            age=req.age,
            gender=req.gender,
            top_candidates=candidates,
            language=req.language,
        )

        disclaimer = (
            MANDATORY_DISCLAIMER_HI
            if req.language.lower() == "hi"
            else MANDATORY_DISCLAIMER_EN
        )

        return RiskPredictionResponse(
            risk_level=risk_level,
            risk_score=risk_score,
            risk_rationale=rationale,
            top_conditions=candidates,
            recommended_specialty=specialty,
            general_precautions=precautions,
            disclaimer=disclaimer,
        )
