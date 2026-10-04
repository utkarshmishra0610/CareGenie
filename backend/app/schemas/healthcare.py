"""Schemas for healthcare facility directory and map locator."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthcareFacility(BaseModel):
    id: int
    name: str = Field(..., description="Facility name")
    facility_type: str = Field(..., description="Hospital, Specialty Clinic, or Urgent Care")
    specialties: List[str] = Field(default_factory=list, description="Medical specialties available")
    latitude: float = Field(..., description="GPS Latitude")
    longitude: float = Field(..., description="GPS Longitude")
    address: str = Field(..., description="Physical street address")
    phone: str = Field(..., description="Direct contact phone number")
    is_emergency_24x7: bool = Field(default=False, description="Whether 24/7 Emergency Room is available")
    rating: float = Field(default=4.5, description="Average patient satisfaction rating")
    distance_km: Optional[float] = Field(None, description="Calculated distance in kilometers from patient")


class FacilitySearchResponse(BaseModel):
    facilities: List[HealthcareFacility]
    total_count: int
    search_center: Dict[str, float] = Field(default_factory=dict, description="Center coordinates used for search")
