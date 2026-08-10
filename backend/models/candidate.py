from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from database import Base, IS_SQLITE

# Conditionally use pgvector or fall back to JSON
if not IS_SQLITE:
    try:
        from pgvector.sqlalchemy import Vector
    except ImportError:
        Vector = None
else:
    Vector = None


class Candidate(Base):
    __tablename__ = "candidate"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200))
    phone = Column(String(50))
    profile = Column(JSON)
    embedding = Column(Vector(1536) if Vector is not None else JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("Application", back_populates="candidate")
