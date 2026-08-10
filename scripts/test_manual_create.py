import httpx, json

body = {
    "name": "测试员工", "position": "前端工程师", "department": "技术部",
    "salary": "25K×13薪", "hire_date": "2026-08-08", "probation_months": 3,
    "phone": "13800000001", "email": "test@example.com", "id_number": "320106199501011234",
    "social_insurance": "active", "social_insurance_account": "SB000001",
    "housing_fund": "active", "housing_fund_account": "GJJ000001",
    "bank_name": "工商银行", "bank_account": "6222021234567890",
    "education_degree": "本科", "education_school": "南京大学",
    "education_major": "计算机科学", "education_graduation_year": 2017,
    "emergency_contact_name": "王小明", "emergency_contact_phone": "13900000002",
    "emergency_contact_relation": "配偶",
    "contract_type": "fulltime",
}

r = httpx.post("http://localhost:8000/api/employees/manual", json=body, timeout=10)
print(f"Status: {r.status_code}")
data = r.json()
emp_id = data["id"]
print(f"Created: id={emp_id}, name={data['name']}")

# Verify all fields
r = httpx.get(f"http://localhost:8000/api/employees/{emp_id}", timeout=10)
e = r.json()
checks = [
    ("phone", "13800000001"),
    ("education_degree", "本科"),
    ("education_school", "南京大学"),
    ("bank_name", "工商银行"),
    ("bank_account", "6222021234567890"),
    ("emergency_contact_name", "王小明"),
    ("emergency_contact_relation", "配偶"),
    ("id_number", "320106199501011234"),
    ("social_insurance_account", "SB000001"),
    ("housing_fund_account", "GJJ000001"),
    ("contract_type", "fulltime"),
    ("onboard_completed", "Y"),
]
all_ok = True
for field, expected in checks:
    actual = e.get(field, "")
    ok = actual == expected
    if not ok:
        print(f"  FAIL: {field} expected={expected} got={actual}")
        all_ok = False
if all_ok:
    print(f"All {len(checks)} fields verified OK!")
