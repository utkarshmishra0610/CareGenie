from fastapi import APIRouter, status
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns service health status to verify the backend server is operational."
)
def get_health() -> HealthResponse:
    """Check if the backend application is running."""
    return HealthResponse(
        status="UP",
        message="CareGenie Backend is running"
    )
