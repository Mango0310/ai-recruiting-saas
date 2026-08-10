from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from database import Base


class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    industry = Column(String(100))
    size = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Knowledge base — list of uploaded doc records
    # [{id, name, file_path, size, uploaded_at, snippet}]
    knowledge_docs = Column(JSON, default=list)
    # Free-text knowledge: company description, values, product info, etc.
    knowledge_text = Column(String(5000))
