import httpx

# Demo employees from load_demo_data have no token.
# To get a real token we need to go through the full onboarding flow:
# upload resume -> decision -> feedback -> onboard

print("1. Create job + upload + decide + feedback + onboard")
r = httpx.post("http://localhost:8000/api/jobs",
               json={"title": "测试前端", "jd_text": "前端开发工程师 React"}, timeout=30)
job_id = r.json()["id"]

with open(r"D:/honor share/ai-recruiting-saas/demo-data/resumes/candidate_01_gao_pipei.pdf", "rb") as f:
    r = httpx.post(f"http://localhost:8000/api/jobs/{job_id}/resumes",
                   files=[("files", ("test.pdf", f, "application/pdf"))], timeout=180)
    app_id = r.json()["results"][0]["application_id"]

httpx.put(f"http://localhost:8000/api/applications/{app_id}/decision",
          json={"hr_decision": "suitable", "hr_notes": "通过"})
httpx.put(f"http://localhost:8000/api/applications/{app_id}/feedback",
          json={"interviewer": "张", "actual_rating": 4, "key_observations": "ok"})

r = httpx.post("http://localhost:8000/api/employees", json={
    "application_id": app_id, "department": "技术部", "position": "测试前端",
    "hire_date": "2026-08-09", "probation_months": 3,
}, timeout=10)
emp = r.json()
emp_id = emp["id"]
token = emp["onboard_token"]
link = emp["onboard_link"]
print(f"Employee: id={emp_id}, token={token[:16]}...")
print(f"Link: {link}")

# Test 1: Valid token
r = httpx.get(f"http://localhost:8000/api/employees/token/{token}", timeout=10)
print(f"\nToken GET: {r.status_code}")

# Test 2: Verify employee details show token info
r = httpx.get(f"http://localhost:8000/api/employees/{emp_id}", timeout=10)
e = r.json()
print(f"Token status: {e['onboard_token_status']}")
print(f"Created: {e['onboard_token_created_at'][:19]}")
print(f"Expires: {e['onboard_token_expires_at'][:19]}")
print(f"Completed: {e['onboard_completed']}")

# Test 3: Regenerate token
r = httpx.post(f"http://localhost:8000/api/employees/{emp_id}/regenerate-onboard-token", timeout=10)
print(f"\nRegenerate: {r.status_code}, new link={r.json().get('onboard_link','')}")

# Verify old token expired warning (but it was replaced, so new token is valid)
r2 = httpx.get(f"http://localhost:8000/api/employees/{emp_id}", timeout=10)
e2 = r2.json()
print(f"New token status: {e2['onboard_token_status']}")

print("\nAll tests done!")
