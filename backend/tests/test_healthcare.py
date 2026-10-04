"""Unit and integration tests for Phase 12 Healthcare Facility Locator."""
from app.services.healthcare_directory import (
    haversine_distance,
    search_facilities,
)


def test_haversine_distance_calculation():
    """Verify great-circle distance between two known geographic points."""
    # Delhi center (28.6139, 77.2090) to Mumbai center (19.0760, 72.8777)
    dist = haversine_distance(28.6139, 77.2090, 19.0760, 72.8777)
    # Approximately 1,140 - 1,160 km
    assert 1100.0 <= dist <= 1200.0

    # Local distance: AIIMS (28.5672, 77.2100) to Max Saket (28.5284, 77.2144)
    local_dist = haversine_distance(28.5672, 77.2100, 28.5284, 77.2144)
    assert 3.0 <= local_dist <= 6.0


def test_specialty_filtering():
    """Verify filtering directory by clinical specialty."""
    facilities, _ = search_facilities(
        lat=28.6139,
        lng=77.2090,
        specialty="Cardiologist",
        radius_km=50.0,
    )
    assert len(facilities) > 0
    for fac in facilities:
        assert any("Cardio" in s for s in fac.specialties)


def test_emergency_24x7_filtering():
    """Verify emergency toggle limits results strictly to 24/7 emergency centers."""
    facilities, _ = search_facilities(
        lat=28.6139,
        lng=77.2090,
        emergency_only=True,
        radius_km=50.0,
    )
    assert len(facilities) > 0
    assert all(f.is_emergency_24x7 is True for f in facilities)


def test_city_fallback_search():
    """Verify manual city search fallback centers search on selected hub."""
    # Mumbai query
    mumbai_facilities, center = search_facilities(
        city="mumbai",
        radius_km=30.0,
    )
    assert len(mumbai_facilities) > 0
    assert any("Lilavati" in f.name or "Hinduja" in f.name for f in mumbai_facilities)
    assert center["latitude"] > 18.0 and center["latitude"] < 20.0


def test_get_specialties_endpoint(client):
    """Verify GET /api/healthcare/specialties endpoint."""
    res = client.get("/api/healthcare/specialties")
    assert res.status_code == 200
    specialties = res.json()
    assert isinstance(specialties, list)
    assert "General Physician" in specialties
    assert "Cardiologist" in specialties


def test_get_nearby_facilities_endpoint(client):
    """Verify GET /api/healthcare/nearby returns schema compliant results."""
    res = client.get("/api/healthcare/nearby?lat=28.5450&lng=77.2600&radius_km=15")
    assert res.status_code == 200
    data = res.json()

    assert "facilities" in data
    assert "total_count" in data
    assert data["total_count"] > 0

    first = data["facilities"][0]
    assert "name" in first
    assert "address" in first
    assert "phone" in first
    assert "distance_km" in first
    assert first["distance_km"] <= 15.0
