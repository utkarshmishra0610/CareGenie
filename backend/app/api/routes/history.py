from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.assessment import AssessmentCreate, AssessmentRead, HealthcareSearchAdd
from app.services import history_service

router = APIRouter()


@router.get(
    "",
    response_model=List[AssessmentRead],
    status_code=status.HTTP_200_OK,
    summary="List patient health history",
    description="Returns all previous assessments for the authenticated user, newest first."
)
def list_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[AssessmentRead]:
    """Retrieve user-specific health assessments history."""
    return history_service.get_user_assessments(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.post(
    "",
    response_model=AssessmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save a health assessment",
    description="Persists a completed disease risk assessment to the patient's personalized history."
)
def create_assessment_record(
    assessment_in: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> AssessmentRead:
    """Save an assessment to authenticated user's history."""
    return history_service.create_assessment(
        db=db, user_id=current_user.id, assessment_in=assessment_in
    )


@router.get(
    "/{assessment_id}",
    response_model=AssessmentRead,
    status_code=status.HTTP_200_OK,
    summary="Get assessment details",
    description="Fetches detailed breakdown of a past assessment by ID for the authenticated user."
)
def get_assessment_details(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> AssessmentRead:
    """Fetch details for a specific assessment."""
    assessment = history_service.get_user_assessment_by_id(
        db=db, user_id=current_user.id, assessment_id=assessment_id
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment record not found."
        )
    return assessment


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an assessment record",
    description="Deletes a specific assessment record belonging to the authenticated user."
)
def delete_assessment_record(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an assessment from authenticated user's history."""
    success = history_service.delete_user_assessment(
        db=db, user_id=current_user.id, assessment_id=assessment_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment record not found."
        )
    return None


@router.post(
    "/{assessment_id}/searches",
    response_model=AssessmentRead,
    status_code=status.HTTP_200_OK,
    summary="Link healthcare search to assessment",
    description="Records a facility lookup or doctor search conducted following this assessment."
)
def log_healthcare_search(
    assessment_id: int,
    search_data: HealthcareSearchAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> AssessmentRead:
    """Add a healthcare search to an assessment record."""
    assessment = history_service.add_search_to_assessment(
        db=db,
        user_id=current_user.id,
        assessment_id=assessment_id,
        search_data=search_data.model_dump(),
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment record not found."
        )
    return assessment
