from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.history import router as history_router
from app.api.routes.chat import router as chat_router
from app.api.routes.prediction import router as prediction_router
from app.api.routes.localization import router as localization_router
from app.api.routes.healthcare import router as healthcare_router

api_router = APIRouter()

# Health router
api_router.include_router(health_router, prefix="", tags=["Health"])

# Authentication routes
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# User profile routes
api_router.include_router(users_router, prefix="/users", tags=["Users"])

# Patient history & assessments routes
api_router.include_router(history_router, prefix="/history", tags=["Patient History"])

# Chat system & conversation routes
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])

# Disease risk prediction routes
api_router.include_router(prediction_router, prefix="", tags=["Disease Risk Prediction"])

# Multilingual localization routes
api_router.include_router(localization_router, prefix="", tags=["Localization"])

# Healthcare provider directory & map routes
api_router.include_router(healthcare_router, prefix="", tags=["Healthcare Provider Locator"])

__all__ = ["api_router"]



