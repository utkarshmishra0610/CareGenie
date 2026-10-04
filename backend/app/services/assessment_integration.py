"""Service uniting Chat Conversation, ML Disease Risk Prediction, and Assessment Archival."""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.chat import ChatSession
from app.prediction.predictor import DiseasePredictor
from app.prediction.symptom_data import find_matching_symptoms
from app.schemas.assessment import AssessmentCreate
from app.schemas.chat import ChatMessageCreate, FinalizedAssessmentResponse
from app.schemas.prediction import PredictionRequest
from app.services import chat_service, history_service


def finalize_session_assessment(
    db: Session, session: ChatSession, user_id: int
) -> FinalizedAssessmentResponse:
    """Aggregates multi-turn consultation symptoms, runs ML risk evaluation, persists Assessment record, and closes session."""
    # 1. Aggregate clinical features from session history
    accumulated_symptoms: List[str] = []
    duration: Optional[str] = None
    severity: Optional[str] = None

    for msg in session.messages:
        if msg.sender == "user":
            extracted = find_matching_symptoms(msg.content)
            for s in extracted:
                if s not in accumulated_symptoms:
                    accumulated_symptoms.append(s)
            if msg.extra_metadata:
                for s in msg.extra_metadata.get("detected_symptoms", []):
                    if s not in accumulated_symptoms:
                        accumulated_symptoms.append(s)
                if not duration and msg.extra_metadata.get("duration"):
                    duration = msg.extra_metadata["duration"]
                if not severity and msg.extra_metadata.get("severity"):
                    severity = msg.extra_metadata["severity"]

    if not accumulated_symptoms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot finalize assessment: No recognizable health symptoms were reported in this conversation session.",
        )

    is_hi = session.language.lower() == "hi"

    # 2. Run ML Disease Risk Prediction
    prediction_req = PredictionRequest(
        symptoms=accumulated_symptoms,
        severity=severity,
        duration=duration,
        language=session.language,
    )
    prediction = DiseasePredictor.assess(prediction_req)

    # 3. Persist Assessment in patient history
    top_disease = prediction.top_conditions[0].disease if prediction.top_conditions else "Unspecified Condition"
    top_conf = prediction.top_conditions[0].confidence_score if prediction.top_conditions else 0.0

    summary_text = (
        f"प्रारंभिक रोग जोखिम मूल्यांकन: {prediction.risk_level} जोखिम। "
        f"मुख्य संभावित स्थिति: {top_disease} ({top_conf}% विश्वास)। "
        f"अनुशंसित विशेषज्ञ: {prediction.recommended_specialty}।"
        if is_hi
        else f"Preliminary disease risk assessment: {prediction.risk_level} Risk. "
        f"Primary candidate condition: {top_disease} ({top_conf}% confidence). "
        f"Recommended specialty: {prediction.recommended_specialty}."
    )

    assessment_in = AssessmentCreate(
        symptoms=accumulated_symptoms,
        duration=duration,
        severity=severity,
        predicted_condition=top_disease,
        risk_level=prediction.risk_level,
        ai_summary=summary_text,
        suggested_specialty=prediction.recommended_specialty,
        healthcare_searches=[],
    )
    db_assessment = history_service.create_assessment(
        db=db, user_id=user_id, assessment_in=assessment_in
    )

    # 4. Generate comprehensive closing summary
    if is_hi:
        conditions_lines = "\n".join(
            [f"- **{c.disease}**: ~{c.confidence_score}% संभावित मिलान ({c.specialty})" for c in prediction.top_conditions[:3]]
        )
        precautions_lines = "\n".join([f"- {p}" for p in prediction.general_precautions])
        closing_message = (
            f"📋 **प्रारंभिक स्वास्थ्य जोखिम मूल्यांकन सारांश (Assessment Completed)**\n\n"
            f"• **नैदानिक जोखिम स्तर**: **{prediction.risk_level}** (स्कोर: {prediction.risk_score}/100)\n"
            f"• **अनुशंसित विशेषज्ञ**: **{prediction.recommended_specialty}**\n\n"
            f"🔍 **संभावित स्वास्थ्य स्थितियाँ**:\n{conditions_lines}\n\n"
            f"💡 **सामान्य सावधानियां एवं देखभाल मार्गदर्शन**:\n{precautions_lines}\n\n"
            f"⚠️ *{prediction.disclaimer}*\n\n"
            f"यह मूल्यांकन आपके स्वास्थ्य इतिहास में सुरक्षित रूप से दर्ज कर दिया गया है।"
        )
    else:
        conditions_lines = "\n".join(
            [f"- **{c.disease}**: ~{c.confidence_score}% probability ({c.specialty})" for c in prediction.top_conditions[:3]]
        )
        precautions_lines = "\n".join([f"- {p}" for p in prediction.general_precautions])
        closing_message = (
            f"📋 **Preliminary Health Risk Assessment Summary**\n\n"
            f"• **Clinical Risk Tier**: **{prediction.risk_level}** (Risk Score: {prediction.risk_score}/100)\n"
            f"• **Recommended Specialty**: **{prediction.recommended_specialty}**\n\n"
            f"🔍 **Potential Candidate Conditions**:\n{conditions_lines}\n\n"
            f"💡 **General Self-Care & Precautions**:\n{precautions_lines}\n\n"
            f"⚠️ *{prediction.disclaimer}*\n\n"
            f"This consultation has been recorded and saved to your personal health history."
        )

    # 5. Append closing message to chat session
    assistant_closing = ChatMessageCreate(
        sender="assistant",
        content=closing_message,
        extra_metadata={
            "assessment_id": db_assessment.id,
            "finalized": True,
            "risk_level": prediction.risk_level,
            "risk_score": prediction.risk_score,
            "top_disease": top_disease,
        },
    )
    chat_service.add_message(db, session=session, message_in=assistant_closing)

    # 6. Deactivate active consultation session
    session.is_active = False
    db.commit()
    db.refresh(session)

    return FinalizedAssessmentResponse(
        assessment=db_assessment,
        prediction=prediction,
        closing_message=closing_message,
    )
