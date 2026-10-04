from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's unique email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    full_name: Optional[str] = Field(None, max_length=150, description="Full name of user")
    preferred_language: str = Field(default="en", max_length=10, description="Language preference (e.g. en, hi)")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plain text password (minimum 8 characters)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "username": "health_user",
                "full_name": "Aarav Sharma",
                "password": "StrongPassword123!",
                "preferred_language": "en"
            }
        }
    }


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "username": "health_user",
                "full_name": "Aarav Sharma",
                "preferred_language": "en",
                "is_active": True,
                "created_at": "2026-09-20T14:30:00Z"
            }
        }
    }


class UserLogin(BaseModel):
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User's account password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username_or_email": "health_user",
                "password": "StrongPassword123!"
            }
        }
    }


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=150)
    preferred_language: Optional[str] = Field(None, max_length=10)
