"""Prediction and disease risk assessment API routes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.prediction.predictor import DiseasePredictor
from app.schemas.prediction import PredictionRequest, RiskPredictionResponse

router = APIRouter(prefix="/assessment", tags=["Disease Risk Prediction"])


@router.post(
    "/predict",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict disease risk assessment",
    description="Evaluates reported symptoms, severity, and duration to provide preliminary candidate conditions, clinical risk score, and recommended specialist.",
)
def predict_disease_risk(
    request: PredictionRequest,
    db: Session = Depends(get_db),
) -> RiskPredictionResponse:
    """Computes ML-driven candidate condition probabilities and clinical risk grading."""
    response = DiseasePredictor.assess(request)
    return response
