from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class Application(Base):
    __tablename__ = "application"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("job.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resume.id"))
    status = Column(String(20), default="new")
    hr_decision = Column(String(20), default="pending")
    hr_notes = Column(Text)
    interview_feedback = Column(JSON)  # {interviewed_at, interviewer, ai_predictions_match, actual_rating, notes, key_observations}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
