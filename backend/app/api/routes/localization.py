"""Localization and language support API routes."""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from app.localization.i18n import get_locale_data

router = APIRouter(tags=["Localization"])

SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "mr", "name": "Marathi", "native_name": "मराठी"},
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
    {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી"},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
    {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"},
]


@router.get(
    "/languages",
    response_model=List[Dict[str, str]],
    status_code=status.HTTP_200_OK,
    summary="List supported languages",
    description="Returns list of available UI and consultation languages.",
)
def list_languages() -> List[Dict[str, str]]:
    """Get supported language codes and display names."""
    return SUPPORTED_LANGUAGES


@router.get(
    "/localization/{lang}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get localized translation bundle",
    description="Returns key-value translation strings and medical guidance templates for the specified language.",
)
def get_localization_bundle(lang: str) -> Dict[str, Any]:
    """Retrieve UI and consultation strings for requested language."""
    valid_codes = [l["code"] for l in SUPPORTED_LANGUAGES]
    if lang.lower() not in valid_codes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language '{lang}' is not supported. Supported languages: {valid_codes}",
        )
    return get_locale_data(lang.lower())
