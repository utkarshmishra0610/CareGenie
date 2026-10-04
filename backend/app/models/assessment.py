from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    assessment_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    symptoms = Column(JSON, nullable=False, default=list)  # list of symptom strings
    duration = Column(String(100), nullable=True)          # e.g., "3 days"
    severity = Column(String(50), nullable=True)           # e.g., "mild", "moderate", "severe"
    predicted_condition = Column(String(200), nullable=True) # preliminary candidate
    risk_level = Column(String(50), default="Preliminary", nullable=False) # e.g., "Low", "Moderate", "High"
    ai_summary = Column(Text, nullable=True)               # conversational summary
    suggested_specialty = Column(String(150), nullable=True) # e.g., "General Physician"
    healthcare_searches = Column(JSON, default=list, nullable=False) # list of facility search queries/results

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="assessments")

    def __repr__(self) -> str:
        return f"<Assessment id={self.id} user_id={self.user_id} condition={self.predicted_condition}>"
