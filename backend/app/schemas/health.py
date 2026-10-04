from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status indicator")
    message: str = Field(..., description="Service status message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "UP",
                "message": "Personalized AI Health Assistant Backend is running"
            }
        }
    }
