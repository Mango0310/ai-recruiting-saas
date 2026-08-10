from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base, IS_SQLITE

if not IS_SQLITE:
    try:
        from pgvector.sqlalchemy import Vector
    except ImportError:
        Vector = None
else:
    Vector = None


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1)
    title = Column(String(200), nullable=False)
    jd_raw = Column(Text)
    job_profile = Column(JSON)
    embedding = Column(Vector(1536) if Vector is not None else JSON, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("Application", back_populates="job", lazy="dynamic")
