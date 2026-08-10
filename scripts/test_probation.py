"""Test probation evaluation end-to-end."""
import httpx, json

BASE = "http://localhost:8000"

# Step 1: Create a tech job + upload resume to get an application
print("1. Creating job...")
r = httpx.post(f"{BASE}/api/jobs", json={"title": "高级后端工程师", "jd_text": "后端开发 微服务 Go"}, timeout=30)
job = r.json()
print(f"   Job id={job['id']}")

print("2. Uploading resume...")
with open(r"D:/honor share/ai-recruiting-saas/demo-data/resumes/candidate_01_gao_pipei.pdf", "rb") as f:
    r = httpx.post(f"{BASE}/api/jobs/{job['id']}/resumes",
                   files=[("files", ("test.pdf", f, "application/pdf"))], timeout=180)
    up_result = r.json()["results"][0]
    app_id = up_result["application_id"]
    print(f"   App id={app_id}, name={up_result.get('candidate_name','?')}")

# Step 2: Decision → suitable
print("3. HR decision: suitable...")
r = httpx.put(f"{BASE}/api/applications/{app_id}/decision",
              json={"hr_decision": "suitable", "hr_notes": "技术面试通过"})
print(f"   Decision: {r.status_code}")

# Step 3: Feedback → interviewed
print("4. Interview feedback...")
r = httpx.put(f"{BASE}/api/applications/{app_id}/feedback",
              json={"interviewer": "张面试官", "ai_predictions_match": "match", "actual_rating": 4, "key_observations": "技术扎实"})
print(f"   Feedback: {r.status_code}")

# Step 4: Onboard
print("5. Onboard employee...")
r = httpx.post(f"{BASE}/api/employees", json={
    "application_id": app_id, "department": "技术部", "position": "高级后端工程师",
    "reports_to": "CTO", "salary": "40K", "hire_date": "2026-07-10",
    "probation_months": 3, "social_insurance": "pending", "housing_fund": "pending",
})
emp = r.json()
emp_id = emp["id"]
print(f"   Employee id={emp_id}")

# Step 5: Check probation status (should be ~30 days in)
print(f"\n6. Probation status (employee {emp_id})...")
r = httpx.get(f"{BASE}/api/employees/{emp_id}/probation")
prob = r.json()
print(f"   Hire date: {prob['hire_date']}, Days: {prob['days_employed']}")
print(f"   Current milestone: {prob['current_milestone']}")
print(f"   Timeline: {len(prob['milestones'])} milestones")
for m in prob["milestones"]:
    print(f"     Day {m['day']}: {m['label']} | reached={m['reached']} | current={m['is_current']}")

# Step 6: Generate AI evaluation with manager notes
print(f"\n7. Generate AI evaluation...")
r = httpx.post(f"{BASE}/api/employees/{emp_id}/probation/evaluate?manager_notes=技术能力扎实，已完成第一个Sprint任务。需要加强跨团队沟通，周报质量待提升。", timeout=120)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    ev = r.json()["evaluation"]
    print(f"   Stage: {ev['stage']}")
    print(f"   Scores: {ev['scores']}")
    print(f"   Strengths: {ev['strengths']}")
    print(f"   Risks: {ev['risks']}")
    print(f"   Recommendation: {ev['recommendation']}")
else:
    print(f"   Error: {r.text[:200]}")

# Step 7: Add manual evaluation
print(f"\n8. Add manual evaluation...")
r = httpx.post(f"{BASE}/api/employees/{emp_id}/probation/evaluate/manual",
               json={"notes": "主管观察：本周主动组织了技术分享，团队反馈很好。代码review通过率明显提高。", "scores": {"adaption": 4, "performance": 3, "collaboration": 5, "potential": 4}})
print(f"   Status: {r.status_code}")

# Step 8: Check evaluations
print(f"\n9. Check evaluations...")
r = httpx.get(f"{BASE}/api/employees/{emp_id}/probation")
prob = r.json()
print(f"   Evaluations: {len(prob['evaluations'])}")
for e in prob["evaluations"]:
    print(f"   - {e['stage']} ({e['generated_by']}): {e['recommendation']}")

print("\nDone!")
