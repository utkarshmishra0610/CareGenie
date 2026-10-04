from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StructuredSymptoms(BaseModel):
    symptoms: List[str] = Field(default_factory=list, description="Primary detected symptoms")
    duration: Optional[str] = Field(None, description="Reported duration of symptoms e.g. 3 days")
    severity: Optional[str] = Field(None, description="Assessed severity e.g. mild, moderate, severe")
    additionalSymptoms: List[str] = Field(default_factory=list, description="Secondary or associated symptoms")
    age: Optional[int] = Field(None, description="Patient age if provided")
    gender: Optional[str] = Field(None, description="Patient gender if provided")
    is_emergency: bool = Field(default=False, description="Whether red-flag emergency symptoms were detected")
    emergency_reasons: List[str] = Field(default_factory=list, description="Specific warning signs triggered")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symptoms": ["fever", "body pain"],
                "duration": "3 days",
                "severity": "moderate",
                "additionalSymptoms": ["headache"],
                "age": 21,
                "gender": "female",
                "is_emergency": False,
                "emergency_reasons": []
            }
        }
    }


class AIHealthResponse(BaseModel):
    reply_text: str = Field(..., description="Conversational reply message from assistant")
    structured_symptoms: StructuredSymptoms = Field(..., description="Extracted structured clinical information")
    detected_emergency: bool = Field(default=False, description="Emergency flag")
    emergency_advice: Optional[str] = Field(None, description="Urgent action guidance if emergency detected")
    suggested_specialty: Optional[str] = Field(None, description="Recommended medical specialty to consult")
    follow_up_question: Optional[str] = Field(None, description="Targeted follow-up question generated adaptively")
    is_ready_for_prediction: bool = Field(default=False, description="True when enough clinical context is gathered for ML assessment")
    candidate_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Top potential conditions based on symptoms")
    missing_fields: List[str] = Field(default_factory=list, description="Clinical fields still missing e.g. duration, severity")
    question_turn: int = Field(default=1, description="Current question turn count in the session")
    disclaimer: str = Field(
        default=(
            "This application is an academic prototype intended strictly for preliminary "
            "health-risk assessment and healthcare navigation assistance. It is NOT a medical diagnosis "
            "or treatment plan. Always consult a licensed healthcare professional for medical concerns."
        ),
        description="Mandatory clinical safety disclaimer"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "reply_text": "I understand you have been experiencing fever and body pain for 3 days...",
                "structured_symptoms": {
                    "symptoms": ["fever", "body pain"],
                    "duration": "3 days",
                    "severity": "moderate",
                    "additionalSymptoms": [],
                    "age": 21,
                    "gender": "female",
                    "is_emergency": False,
                    "emergency_reasons": []
                },
                "detected_emergency": False,
                "emergency_advice": None,
                "suggested_specialty": "General Physician",
                "disclaimer": "This application is an academic prototype..."
            }
        }
    }
