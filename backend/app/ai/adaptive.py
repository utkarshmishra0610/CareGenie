"""Adaptive clinical inquiry engine for multi-turn symptom collection and differential clarification."""
from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.chat import ChatSession
from app.prediction.symptom_data import (
    DISEASE_SYMPTOMS_MAP,
    find_matching_symptoms,
    get_diseases_for_symptoms,
)
from app.schemas.ai import StructuredSymptoms


class AdaptiveQuestionEngine:
    """Manages conversational state, differential symptom probing, and inquiry termination."""

    MAX_QUESTIONS = 4

    @classmethod
    def aggregate_session_context(
        cls,
        session: ChatSession,
        current_user_text: str,
        current_structured: StructuredSymptoms,
    ) -> Tuple[List[str], Optional[str], Optional[str], Optional[int], Optional[str], int, Set[str]]:
        """Aggregates symptoms, duration, severity, age, gender, turn count, and previously asked questions."""
        accumulated_symptoms: List[str] = list(current_structured.symptoms)
        duration: Optional[str] = current_structured.duration
        severity: Optional[str] = current_structured.severity
        age: Optional[int] = current_structured.age
        gender: Optional[str] = current_structured.gender
        asked_symptoms: Set[str] = set()

        user_message_count = 1  # current message is at least the 1st
        for msg in session.messages:
            if msg.sender == "user":
                user_message_count += 1
                prior_matches = find_matching_symptoms(msg.content)
                for s in prior_matches:
                    if s not in accumulated_symptoms:
                        accumulated_symptoms.append(s)
            elif msg.sender == "assistant" and msg.extra_metadata:
                # Check for previously asked differential symptoms
                if "asked_symptom" in msg.extra_metadata and msg.extra_metadata["asked_symptom"]:
                    asked_symptoms.add(msg.extra_metadata["asked_symptom"])
                if not duration and msg.extra_metadata.get("duration"):
                    duration = msg.extra_metadata["duration"]
                if not severity and msg.extra_metadata.get("severity"):
                    severity = msg.extra_metadata["severity"]

        return (
            accumulated_symptoms,
            duration,
            severity,
            age,
            gender,
            user_message_count,
            asked_symptoms,
        )

    @classmethod
    def find_discriminating_symptom(
        cls,
        candidate_conditions: List[Tuple[str, float]],
        accumulated_symptoms: List[str],
        asked_symptoms: Set[str],
    ) -> Optional[str]:
        """Finds a key symptom that differentiates the top candidate diseases."""
        if len(candidate_conditions) < 2:
            if len(candidate_conditions) == 1:
                top_disease = candidate_conditions[0][0]
                disease_syms = DISEASE_SYMPTOMS_MAP.get(top_disease, set())
                remaining = [
                    s for s in disease_syms
                    if s not in accumulated_symptoms and s not in asked_symptoms
                ]
                return remaining[0] if remaining else None
            return None

        top_disease_1 = candidate_conditions[0][0]
        top_disease_2 = candidate_conditions[1][0]

        syms_1 = DISEASE_SYMPTOMS_MAP.get(top_disease_1, set())
        syms_2 = DISEASE_SYMPTOMS_MAP.get(top_disease_2, set())

        diff_syms = (syms_1 ^ syms_2) - set(accumulated_symptoms) - asked_symptoms

        if diff_syms:
            for s in sorted(diff_syms, key=lambda x: len(x)):
                if len(s) > 2 and "subtype" not in s and "doesnt" not in s:
                    return s
            return next(iter(diff_syms))

        return None

    @classmethod
    def determine_next_step(
        cls,
        session: ChatSession,
        current_text: str,
        structured: StructuredSymptoms,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Determines the next adaptive question, candidate diseases, and whether ready for risk prediction."""
        is_hi = language.lower() == "hi"

        # 1. Emergency takes unconditional precedence
        if structured.is_emergency:
            return {
                "next_question": None,
                "is_ready_for_prediction": False,
                "candidate_conditions": [],
                "missing_fields": [],
                "question_turn": 1,
                "asked_symptom": None,
                "accumulated_symptoms": structured.symptoms,
            }

        # 2. Aggregate session state
        (
            accumulated_symptoms,
            duration,
            severity,
            age,
            gender,
            turn_count,
            asked_symptoms,
        ) = cls.aggregate_session_context(session, current_text, structured)

        # 3. Calculate candidate conditions
        raw_candidates = get_diseases_for_symptoms(accumulated_symptoms)
        candidate_conditions = [
            {"disease": d, "score": round(score, 3)}
            for d, score in raw_candidates[:5]
        ]

        # 4. Identify missing clinical fields
        missing_fields: List[str] = []
        if not duration:
            missing_fields.append("duration")
        if not severity:
            missing_fields.append("severity")

        # 5. Check termination / stopping condition
        has_sufficient_context = (
            len(accumulated_symptoms) >= 3
            and duration is not None
            and severity is not None
        )
        is_max_turns = turn_count >= cls.MAX_QUESTIONS

        if (has_sufficient_context or is_max_turns) and len(accumulated_symptoms) > 0:
            ready_msg = (
                "पर्याप्त प्रारंभिक जानकारी प्राप्त हो गई है। क्या आप अपने रोग जोखिम मूल्यांकन को देखना चाहते हैं?"
                if is_hi
                else "We have gathered sufficient preliminary information. Would you like to proceed to your preliminary disease risk assessment?"
            )
            return {
                "next_question": ready_msg,
                "is_ready_for_prediction": True,
                "candidate_conditions": candidate_conditions,
                "missing_fields": missing_fields,
                "question_turn": turn_count,
                "asked_symptom": None,
                "accumulated_symptoms": accumulated_symptoms,
            }

        # 6. If no symptoms detected at all, ask for primary complaint
        if not accumulated_symptoms:
            q = (
                "कृपया मुझे बताएं कि आप वर्तमान में कौन से लक्षण या शारीरिक परेशानी महसूस कर रहे हैं?"
                if is_hi
                else "Could you please describe the specific symptoms or physical discomfort you are currently experiencing?"
            )
            return {
                "next_question": q,
                "is_ready_for_prediction": False,
                "candidate_conditions": [],
                "missing_fields": ["symptoms"],
                "question_turn": turn_count,
                "asked_symptom": None,
                "accumulated_symptoms": [],
            }

        # 7. Ask for missing duration
        if not duration:
            q = (
                "आप इन लक्षणों का अनुभव कितने समय से कर रहे हैं (उदा. कुछ घंटे, 2-3 दिन, या 1 सप्ताह)?"
                if is_hi
                else "How long have you been experiencing these symptoms (e.g., hours, 2-3 days, or over a week)?"
            )
            return {
                "next_question": q,
                "is_ready_for_prediction": False,
                "candidate_conditions": candidate_conditions,
                "missing_fields": missing_fields,
                "question_turn": turn_count,
                "asked_symptom": None,
                "accumulated_symptoms": accumulated_symptoms,
            }

        # 8. Ask for missing severity
        if not severity:
            q = (
                "क्या आप अपने लक्षणों की गंभीरता को हल्का (mild), मध्यम (moderate) या गंभीर (severe) मानेंगे?"
                if is_hi
                else "Would you describe the intensity of your symptoms as mild, moderate, or severe?"
            )
            return {
                "next_question": q,
                "is_ready_for_prediction": False,
                "candidate_conditions": candidate_conditions,
                "missing_fields": missing_fields,
                "question_turn": turn_count,
                "asked_symptom": None,
                "accumulated_symptoms": accumulated_symptoms,
            }

        # 9. Ask differential symptom between top candidate diseases
        diff_symptom = cls.find_discriminating_symptom(
            raw_candidates, accumulated_symptoms, asked_symptoms
        )
        if diff_symptom:
            q = (
                f"बेहतर स्पष्टता के लिए, क्या आप '{diff_symptom}' का भी अनुभव कर रहे हैं?"
                if is_hi
                else f"To help narrow down the possibilities, are you also experiencing '{diff_symptom}'?"
            )
            return {
                "next_question": q,
                "is_ready_for_prediction": False,
                "candidate_conditions": candidate_conditions,
                "missing_fields": missing_fields,
                "question_turn": turn_count,
                "asked_symptom": diff_symptom,
                "accumulated_symptoms": accumulated_symptoms,
            }

        # 10. Default ready
        default_ready_msg = (
            "हमने आपके लक्षणों का विवरण संकलित कर लिया है। क्या आप प्रारंभिक जोखिम मूल्यांकन शुरू करना चाहते हैं?"
            if is_hi
            else "We have recorded your reported symptoms. Would you like to proceed with your preliminary disease risk assessment?"
        )
        return {
            "next_question": default_ready_msg,
            "is_ready_for_prediction": True,
            "candidate_conditions": candidate_conditions,
            "missing_fields": missing_fields,
            "question_turn": turn_count,
            "asked_symptom": None,
            "accumulated_symptoms": accumulated_symptoms,
        }
