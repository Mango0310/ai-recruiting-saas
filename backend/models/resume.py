from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from database import Base


class Resume(Base):
    __tablename__ = "resume"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidate.id"))
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(20), default="pdf")
    raw_text = Column(Text)
    parse_status = Column(String(20), default="pending")
    parse_error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
