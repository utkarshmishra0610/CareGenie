"""Healthcare facility search and geographic provider locator routes."""
from typing import List, Optional
from fastapi import APIRouter, Query, status
from app.schemas.healthcare import FacilitySearchResponse
from app.services.healthcare_directory import get_all_specialties, search_facilities

router = APIRouter(prefix="/healthcare", tags=["Healthcare Provider Locator"])


@router.get(
    "/nearby",
    response_model=FacilitySearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search nearby healthcare facilities",
    description="Locates verified hospital centers, clinics, and emergency facilities within a specified radius, filtered by clinical specialty.",
)
def get_nearby_facilities(
    lat: Optional[float] = Query(None, description="Patient GPS Latitude"),
    lng: Optional[float] = Query(None, description="Patient GPS Longitude"),
    city: Optional[str] = Query(None, description="City name for fallback location"),
    specialty: Optional[str] = Query(None, description="Medical specialty to filter (e.g. Cardiologist, Pulmonologist)"),
    radius_km: float = Query(25.0, ge=1.0, le=500.0, description="Search radius in kilometers"),
    emergency_only: bool = Query(False, description="Filter to only facilities with 24/7 emergency rooms"),
    q: Optional[str] = Query(None, description="Text search by name or street address"),
) -> FacilitySearchResponse:
    """Performs Haversine distance proximity search on accredited facilities."""
    facilities, center = search_facilities(
        lat=lat,
        lng=lng,
        city=city,
        specialty=specialty,
        radius_km=radius_km,
        emergency_only=emergency_only,
        query=q,
    )
    return FacilitySearchResponse(
        facilities=facilities,
        total_count=len(facilities),
        search_center=center,
    )


@router.get(
    "/specialties",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="List available medical specialties",
    description="Returns distinct list of clinical departments and specialties represented in the directory.",
)
def list_available_specialties() -> List[str]:
    """Retrieves unique specialties list."""
    return get_all_specialties()

from pydantic import BaseModel
import json
import urllib.request

class UserLocationResponse(BaseModel):
    city: str
    region: str
    latitude: float
    longitude: float
    country: str
    is_detected: bool

@router.get(
    "/my-location",
    response_model=UserLocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect user location via network IP",
    description="Detects user's actual city and GPS coordinates server-side to guarantee accurate local healthcare navigation.",
)
def get_user_location() -> UserLocationResponse:
    """Attempts server-side IP geolocation to determine user's actual city and coordinates."""
    try:
        req = urllib.request.Request(
            "https://ipwho.is/",
            headers={"User-Agent": "CareGenieAI/1.0"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("success") and data.get("latitude") and data.get("longitude"):
                return UserLocationResponse(
                    city=data.get("city") or "Indore",
                    region=data.get("region") or "Madhya Pradesh",
                    latitude=float(data["latitude"]),
                    longitude=float(data["longitude"]),
                    country=data.get("country") or "India",
                    is_detected=True,
                )
    except Exception as e:
        print(f"Server-side IP location detection notice: {e}")

    # Fallback default location
    return UserLocationResponse(
        city="Indore",
        region="Madhya Pradesh",
        latitude=22.7179,
        longitude=75.8333,
        country="India",
        is_detected=False,
    )
