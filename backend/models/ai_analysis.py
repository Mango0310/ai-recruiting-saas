from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from database import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("application.id"), nullable=False)
    job_profile_snapshot = Column(JSON)
    candidate_profile_snapshot = Column(JSON)
    match_report = Column(JSON)
    model_version = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
