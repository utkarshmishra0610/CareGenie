from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthcareSearchItem(BaseModel):
    facility_name: str = Field(..., description="Name of hospital or doctor clinic")
    specialty: Optional[str] = Field(None, description="Medical specialty searched")
    location: Optional[str] = Field(None, description="City or area of facility")
    distance: Optional[str] = Field(None, description="Distance from user e.g. 2.4 km")
    phone: Optional[str] = Field(None, description="Public contact number")
    searched_at: Optional[str] = Field(None, description="Timestamp of search action")


class AssessmentCreate(BaseModel):
    symptoms: List[str] = Field(..., description="List of recognized patient symptoms", min_length=1)
    duration: Optional[str] = Field(None, max_length=100, description="Duration of symptoms e.g. 3 days")
    severity: Optional[str] = Field(None, max_length=50, description="Severity e.g. mild, moderate, severe")
    predicted_condition: Optional[str] = Field(None, max_length=200, description="Preliminary candidate condition")
    risk_level: str = Field(default="Preliminary", max_length=50, description="Assessed risk tier")
    ai_summary: Optional[str] = Field(None, description="Summary of conversational assessment")
    suggested_specialty: Optional[str] = Field(None, max_length=150, description="Recommended consultation specialty")
    healthcare_searches: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "symptoms": ["fever", "headache"],
                "duration": "3 days",
                "severity": "moderate",
                "predicted_condition": "Dengue",
                "risk_level": "Preliminary",
                "ai_summary": "Patient reported sudden onset high fever and headache over 3 days.",
                "suggested_specialty": "General Physician",
                "healthcare_searches": []
            }
        }
    }


class AssessmentRead(BaseModel):
    id: int
    user_id: int
    assessment_date: datetime
    symptoms: List[str]
    duration: Optional[str] = None
    severity: Optional[str] = None
    predicted_condition: Optional[str] = None
    risk_level: str
    ai_summary: Optional[str] = None
    suggested_specialty: Optional[str] = None
    healthcare_searches: List[Dict[str, Any]] = []
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 1,
                "assessment_date": "2026-09-20T15:00:00Z",
                "symptoms": ["fever", "headache"],
                "duration": "3 days",
                "severity": "moderate",
                "predicted_condition": "Dengue",
                "risk_level": "Preliminary",
                "ai_summary": "Patient reported sudden onset high fever and headache over 3 days.",
                "suggested_specialty": "General Physician",
                "healthcare_searches": [],
                "created_at": "2026-09-20T15:00:00Z"
            }
        }
    }


class HealthcareSearchAdd(BaseModel):
    facility_name: str
    specialty: Optional[str] = None
    location: Optional[str] = None
    distance: Optional[str] = None
    phone: Optional[str] = None
