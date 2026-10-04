"""Schemas for disease risk prediction and clinical assessment."""
from typing import List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    symptoms: List[str] = Field(..., description="List of recognized symptoms reported by patient", min_length=1)
    severity: Optional[str] = Field(None, description="Reported symptom severity e.g. mild, moderate, severe")
    duration: Optional[str] = Field(None, description="Reported duration of symptoms e.g. 3 days")
    age: Optional[int] = Field(None, description="Patient age if provided")
    gender: Optional[str] = Field(None, description="Patient gender if provided")
    language: str = Field(default="en", description="Preferred response language ('en' or 'hi')")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symptoms": ["fever", "coughing", "headache"],
                "severity": "moderate",
                "duration": "3 days",
                "age": 28,
                "gender": "male",
                "language": "en"
            }
        }
    }


class ConditionCandidate(BaseModel):
    disease: str = Field(..., description="Potential clinical condition name")
    confidence_score: float = Field(..., description="Confidence probability percentage (0.0 - 100.0)")
    specialty: str = Field(..., description="Recommended medical specialty for this condition")


class RiskPredictionResponse(BaseModel):
    risk_level: str = Field(..., description="Clinical risk tier: LOW, MODERATE, HIGH, or CRITICAL")
    risk_score: float = Field(..., description="Aggregate quantitative risk score from 0.0 to 100.0")
    risk_rationale: str = Field(..., description="Clinical reasoning explaining the assigned risk tier")
    top_conditions: List[ConditionCandidate] = Field(..., description="Ranked candidate conditions")
    recommended_specialty: str = Field(..., description="Primary medical specialty recommended for consultation")
    general_precautions: List[str] = Field(..., description="Evidence-based general care precautions")
    disclaimer: str = Field(
        default=(
            "Preliminary health risk indication only — NOT a medical diagnosis or treatment plan. "
            "Please consult a certified healthcare professional for clinical examination."
        ),
        description="Mandatory medical safety disclaimer"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "risk_level": "MODERATE",
                "risk_score": 62.5,
                "risk_rationale": "Multiple symptoms present with moderate severity persisting for several days.",
                "top_conditions": [
                    {
                        "disease": "Influenza",
                        "confidence_score": 76.4,
                        "specialty": "General Physician"
                    }
                ],
                "recommended_specialty": "General Physician",
                "general_precautions": [
                    "Maintain adequate hydration with water and warm fluids.",
                    "Ensure sufficient physical rest and monitor body temperature.",
                    "Avoid self-medicating with unprescribed pharmaceuticals.",
                    "Seek medical care if symptoms worsen or breathing difficulty develops."
                ],
                "disclaimer": "Preliminary health risk indication only..."
            }
        }
    }
