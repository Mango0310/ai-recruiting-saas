"""Initialize database with default company."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import engine, Base, SessionLocal
from models.company import Company

Base.metadata.create_all(bind=engine)

db = SessionLocal()
if db.query(Company).count() == 0:
    db.add(Company(name="演示公司", industry="互联网", size="50-200人"))
    db.commit()
    print("Created default company.")
else:
    print("Company already exists.")

db.close()
print("Database initialized.")
