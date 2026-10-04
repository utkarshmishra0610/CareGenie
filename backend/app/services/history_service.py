from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate


def create_assessment(
    db: Session, user_id: int, assessment_in: AssessmentCreate
) -> Assessment:
    """Create and persist a new patient health assessment record."""
    db_assessment = Assessment(
        user_id=user_id,
        assessment_date=datetime.now(timezone.utc),
        symptoms=assessment_in.symptoms,
        duration=assessment_in.duration,
        severity=assessment_in.severity,
        predicted_condition=assessment_in.predicted_condition,
        risk_level=assessment_in.risk_level or "Preliminary",
        ai_summary=assessment_in.ai_summary,
        suggested_specialty=assessment_in.suggested_specialty,
        healthcare_searches=assessment_in.healthcare_searches or [],
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


def get_user_assessments(
    db: Session, user_id: int, skip: int = 0, limit: int = 50
) -> List[Assessment]:
    """Retrieve all assessments for a specific user, newest first."""
    return (
        db.query(Assessment)
        .filter(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_assessment_by_id(
    db: Session, user_id: int, assessment_id: int
) -> Optional[Assessment]:
    """Retrieve a specific assessment by ID ensuring user ownership."""
    return (
        db.query(Assessment)
        .filter(Assessment.id == assessment_id, Assessment.user_id == user_id)
        .first()
    )


def delete_user_assessment(db: Session, user_id: int, assessment_id: int) -> bool:
    """Delete an assessment record owned by the authenticated user."""
    assessment = get_user_assessment_by_id(db, user_id, assessment_id)
    if not assessment:
        return False
    db.delete(assessment)
    db.commit()
    return True


def add_search_to_assessment(
    db: Session, user_id: int, assessment_id: int, search_data: Dict[str, Any]
) -> Optional[Assessment]:
    """Appends a healthcare facility search record to an existing assessment."""
    assessment = get_user_assessment_by_id(db, user_id, assessment_id)
    if not assessment:
        return None

    current_searches = list(assessment.healthcare_searches or [])
    if "searched_at" not in search_data or not search_data["searched_at"]:
        search_data["searched_at"] = datetime.now(timezone.utc).isoformat()
    current_searches.append(search_data)

    assessment.healthcare_searches = current_searches
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment
