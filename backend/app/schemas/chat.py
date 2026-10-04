from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Message text content")
    sender: str = Field(default="user", description="Message sender: user, assistant, system")
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata like extracted symptoms")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "I have had a high fever and headache for 3 days.",
                "sender": "user",
                "extra_metadata": {}
            }
        }
    }


class ChatMessageRead(BaseModel):
    id: int
    session_id: int
    sender: str
    content: str
    extra_metadata: Dict[str, Any] = {}
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "session_id": 1,
                "sender": "user",
                "content": "I have had a high fever and headache for 3 days.",
                "extra_metadata": {"detected_symptoms": ["fever", "headache"]},
                "created_at": "2026-09-20T15:10:00Z"
            }
        }
    }


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Session title")
    language: str = Field(default="en", max_length=10, description="Preferred conversation language (e.g. en, hi)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Fever Evaluation",
                "language": "en"
            }
        }
    }


class ChatSessionRead(BaseModel):
    id: int
    user_id: int
    title: str
    language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "Fever Evaluation",
                "language": "en",
                "is_active": True,
                "created_at": "2026-09-20T15:10:00Z",
                "updated_at": "2026-09-20T15:10:00Z",
                "message_count": 2
            }
        }
    }


class ChatSessionDetail(ChatSessionRead):
    messages: List[ChatMessageRead] = []


from app.schemas.assessment import AssessmentRead
from app.schemas.prediction import RiskPredictionResponse


class FinalizedAssessmentResponse(BaseModel):
    assessment: AssessmentRead = Field(..., description="Persisted patient health assessment record")
    prediction: RiskPredictionResponse = Field(..., description="ML disease risk prediction details")
    closing_message: str = Field(..., description="Conversational closing message summarizing results")

