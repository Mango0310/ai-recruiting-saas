from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base


class User(Base):
    __tablename__ = "user_account"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    name = Column(String(100), nullable=False)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
