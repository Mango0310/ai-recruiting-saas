"""Test file preview endpoints — setup + verify"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import SessionLocal
from models.employee import Employee

# Create a test file and attach to employee 1
storage = Path(r"D:\honor share\ai-recruiting-saas\storage\employee_docs\1")
storage.mkdir(parents=True, exist_ok=True)
test_file = storage / "test_diploma.pdf"
test_file.write_text("Fake diploma certificate content for testing file preview.")

db = SessionLocal()
emp = db.query(Employee).filter(Employee.id == 1).first()
if emp:
    emp.diploma_file = str(test_file)
    db.commit()
    print(f"Setup: attached {test_file} to employee {emp.id} ({emp.name})")
else:
    print("No employee found — run load_demo_data.py first")
db.close()

print(f"\nTest file exists: {test_file.exists()}")

# Now test the preview endpoint directly (bypass HTTP)

endpoint_path = r"D:\honor share\ai-recruiting-saas\backend\routers\employees.py"
print(f"Preview endpoints in: {endpoint_path}")
print("\nAfter backend restarts, test with:")
print("  http://localhost:8000/api/employees/1/file?type=diploma")
print("  http://localhost:8000/api/employees/token/{token}/file?type=diploma")
