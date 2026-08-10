"""Full pipeline end-to-end test: company → job → upload → analyze → decide → onboard → employee.

Run: cd backend && .venv\Scripts\python.exe ..\scripts\test_full_pipeline.py
"""

import sys, json, time
from pathlib import Path
import httpx

BASE = "http://localhost:8000"
DEMO_DIR = Path(r"D:\honor share\ai-recruiting-saas\demo-data\resumes")

passed = 0
failed = 0

def check(step, condition, detail=""):
    global passed, failed
    d = str(detail) if detail else ""
    if condition:
        passed += 1
        print(f"  [PASS] {step}{' - ' + d if d else ''}")
    else:
        failed += 1
        print(f"  [FAIL] {step}{' - ' + d if d else ''}")

def api(method, path, **kwargs):
    return httpx.request(method, f"{BASE}{path}", timeout=kwargs.pop("timeout", 120), **kwargs)

# ============================================================
print("=" * 60)
print("FULL PIPELINE E2E TEST")
print("=" * 60)

# ── 1. Health & Dashboard ──
print("\n[1] System Health & Dashboard")
r = api("GET", "/api/health")
check("Health check", r.status_code == 200, r.json()["status"])

r = api("GET", "/api/dashboard/stats")
dash = r.json()
check("Dashboard returns stats", "job_count" in dash, f"{dash.get('job_count')} jobs, {dash.get('candidate_count')} candidates")


# ── 2. Company setup ──
print("\n[2] Company Setup")
r = api("GET", "/api/company")
check("Company info endpoint", r.status_code in (200, 404))  # may or may not exist


# ── 3. Quick-create a tech job ──
print("\n[3] Quick-Create Job (后端工程师)")
jd_text = """高级后端工程师
职责：负责微服务架构设计与开发，优化系统性能，参与技术选型。
要求：5年以上后端开发经验，精通Go/Python，熟悉分布式系统、Kubernetes、PostgreSQL。
加分：有开源项目经验，熟悉CI/CD。"""

t0 = time.time()
r = api("POST", "/api/jobs", json={"title": "高级后端工程师", "jd_text": jd_text})
elapsed = time.time() - t0
check("Quick-create job", r.status_code == 200, f"{elapsed:.1f}s")
tech_job = r.json()
tech_job_id = tech_job["id"]
rc = tech_job.get("job_profile", {}).get("role_category", "")
check("role_category = tech", rc == "tech", rc)

# Check job_profile structure
jp = tech_job["job_profile"]
check("Has responsibilities", len(jp.get("responsibilities", [])) > 0)
check("Has weight_distribution", sum(jp.get("weight_distribution", {}).values()) == 100)


# ── 4. AI Probe + Full Create (智能创建) ──
print("\n[4] Smart Create Job (UI设计师)")
probe_ctx = {
    "title": "资深UI设计师", "department": "设计部",
    "company_name": "演示科技", "company_industry": "企业SaaS",
    "company_size": "100-299人", "business_stage": "growth",
    "raw_requirements": "需要能搭建设计系统、对B端产品有感觉的设计师",
}

t0 = time.time()
r = api("POST", "/api/jobs/probe", json=probe_ctx)
check("Probe returns questions", r.status_code == 200, f"{time.time()-t0:.1f}s")
data = r.json()
questions = data.get("questions", data if isinstance(data, list) else [])
check("3-5 questions", 3 <= len(questions) <= 5, f"got {len(questions)}")

# Answer questions
qa = [{"question": q, "answer": f"回答: {q[:20]}..."} for q in questions[:3]]
full_ctx = {**probe_ctx, "ai_questions": qa}

t0 = time.time()
r = api("POST", "/api/jobs/create-full", json=full_ctx)
check("Full create job", r.status_code == 200, f"{time.time()-t0:.1f}s")
design_job = r.json()
design_job_id = design_job["id"]
rc2 = design_job.get("job_profile", {}).get("role_category", "")
check("role_category = design", rc2 == "design", rc2)
check("Has hiring_brief", "hiring_brief" in design_job.get("job_profile", {}))
check("Has competency_model", "competency_model" in design_job.get("job_profile", {}))


# ── 5. Upload resumes to tech job ──
print("\n[5] Upload Resumes to Tech Job")
pdfs = sorted(DEMO_DIR.glob("*.pdf"))
results_by_file = {}

for pdf in pdfs:
    with open(pdf, "rb") as f:
        t0 = time.time()
        r = api("POST", f"/api/jobs/{tech_job_id}/resumes",
                files=[("files", (pdf.name, f, "application/pdf"))])
        elapsed = time.time() - t0
    data = r.json()
    res = data["results"][0]
    check(f"Upload {pdf.name}", res["status"] == "completed", f"{elapsed:.1f}s → {res.get('candidate_name','?')}")

    # Fetch match report
    app_id = res.get("application_id")
    if app_id:
        mr_r = api("GET", f"/api/applications/{app_id}/report")
        if mr_r.status_code == 200:
            mr = mr_r.json().get("match_report", {})
            stars = int(mr.get("star_rating", 0))
            check(f"  Match report {pdf.name}", stars >= 1, f"{'★'*stars} {mr.get('overall_conclusion','')[:30]}")
            results_by_file[pdf.name] = {
                "app_id": app_id,
                "cand_id": res.get("candidate_id"),
                "stars": stars,
                "name": res.get("candidate_name", ""),
            }

# ── 6. Candidate detail & comparison ──
print("\n[6] Candidate Detail & Comparison")

# Get first candidate detail
first = results_by_file.get(pdfs[0].name, {})
if first.get("cand_id"):
    r = api("GET", f"/api/candidates/{first['cand_id']}")
    cand = r.json()
    check("Candidate profile loaded", cand.get("name") != "")
    check("Has tech_stack_depth", "tech_stack_depth" in (cand.get("profile") or {}),
          "tech role enrichment" if "tech_stack_depth" in (cand.get("profile") or {}) else "no tech fields")
    check("Has github_profile", "github_profile" in (cand.get("profile") or {}),
          "github data" if "github_profile" in (cand.get("profile") or {}) else "no github data")

# Comparison
r = api("GET", f"/api/jobs/{tech_job_id}/compare")
comp = r.json()
check("Comparison data", len(comp.get("candidates", [])) >= 3, f"{len(comp.get('candidates',[]))} candidates")

# Briefing
r = api("GET", f"/api/jobs/{tech_job_id}/briefing")
brief = r.json()
check("Briefing generated", len(brief.get("all_candidates", [])) >= 3)


# ── 7. HR Decision & Pipeline ──
print("\n[7] HR Decision & Pipeline")

# Decide on each candidate
decisions = [
    (pdfs[0].name, "suitable"),
    (pdfs[1].name, "maybe"),
    (pdfs[2].name, "not_suitable"),
]

for filename, decision in decisions:
    info = results_by_file.get(filename, {})
    app_id = info.get("app_id")
    if not app_id:
        check(f"Decision {filename}", False, "no app_id")
        continue
    r = api("PUT", f"/api/applications/{app_id}/decision",
            json={"hr_decision": decision, "hr_notes": f"测试决策: {decision}"})
    check(f"Decision: {info['name']} → {decision}", r.status_code == 200)

    # Verify status updated
    r = api("GET", f"/api/candidates/{info['cand_id']}")
    c = r.json()
    app_status = c.get("applications", [{}])[0].get("status", "")
    expected_status = "interviewing" if decision == "suitable" else "hr_reviewed"
    check(f"  Status: {app_status}", app_status == expected_status, f"(expected {expected_status})")


# ── 8. Interview Feedback ──
print("\n[8] Interview Feedback")

suitable_info = results_by_file.get(pdfs[0].name, {})
suitable_app_id = suitable_info.get("app_id")

if suitable_app_id:
    r = api("PUT", f"/api/applications/{suitable_app_id}/feedback",
            json={
                "interviewer": "张面试官",
                "ai_predictions_match": "match",
                "actual_rating": 4,
                "key_observations": "候选人技术功底扎实，Go和Python经验丰富，对分布式系统理解深入。表达能力好。",
            })
    check("Submit feedback", r.status_code == 200, f"status={r.status_code}")

    # Verify feedback saved and status advanced
    r = api("GET", f"/api/candidates/{suitable_info['cand_id']}")
    c = r.json()
    fb = None
    for app in c.get("applications", []):
        if app.get("application_id") == suitable_app_id:
            fb = app.get("interview_feedback")
            break
    check("Feedback stored", fb is not None)
    check("Feedback has rating", fb.get("actual_rating") == 4 if fb else False)
    check("Status = interviewed", any(a.get("status") == "interviewed" for a in c.get("applications", [])),
          [a.get("status") for a in c.get("applications", [])])


# ── 9. Confirm hire & Onboard ──
print("\n[9] Confirm Hire & Onboard Employee")

if suitable_app_id:
    r = api("POST", "/api/employees", json={
        "application_id": suitable_app_id,
        "department": "技术部",
        "position": "高级后端工程师",
        "reports_to": "CTO",
        "salary": "40K×14薪",
        "hire_date": "2026-08-08",
        "probation_months": 3,
        "contract_type": "fulltime",
        "social_insurance": "pending",
        "housing_fund": "pending",
    })
    check("Onboard employee", r.status_code == 200, f"id={r.json().get('id','?')}")
    emp_result = r.json()
    emp_id = emp_result.get("id")
    onboard_link = emp_result.get("onboard_link", "")
    onboard_token = emp_result.get("onboard_token", "")
    check("Onboard link generated", bool(onboard_link), onboard_link)

    # Verify application status → hired
    r = api("GET", f"/api/candidates/{suitable_info['cand_id']}")
    c = r.json()
    hired_status = any(a.get("status") == "hired" for a in c.get("applications", []))
    check("Application status = hired", hired_status)


# ── 10. Employee self-service onboarding ──
print("\n[10] Employee Self-Service Onboarding")

if emp_id:
    emp_id_val = emp_id
    onboard_token_val = onboard_token

    # Get employee by token
    r = api("GET", f"/api/employees/token/{onboard_token_val}")
    check("Token lookup works", r.status_code == 200, r.json().get("name", "?"))

    # Fill personal info
    r = api("PUT", f"/api/employees/token/{onboard_token_val}", json={
        "phone": "13900139000",
        "email": "newhire@example.com",
        "id_number": "110101199001011234",
        "education_degree": "硕士",
        "education_school": "清华大学",
        "education_major": "计算机科学",
        "education_graduation_year": 2018,
        "bank_name": "招商银行",
        "bank_account": "6225880123456789",
        "social_insurance_account": "SB123456789",
        "housing_fund_account": "GJJ987654321",
        "emergency_contact_name": "李四",
        "emergency_contact_phone": "13800138000",
        "emergency_contact_relation": "配偶",
        "onboard_completed": True,
    })
    check("Self-service form submitted", r.status_code == 200)

    # Verify employee record updated
    r = api("GET", f"/api/employees/{emp_id_val}")
    emp = r.json()
    check("Education filled", emp.get("education_degree") == "硕士")
    check("Bank filled", emp.get("bank_name") == "招商银行")
    check("Emergency contact filled", emp.get("emergency_contact_name") == "李四")
    check("Onboard completed = Y", emp.get("onboard_completed") == "Y")


# ── 11. Employee management ──
print("\n[11] Employee Management")

if emp_id:
    emp_id_val = emp_id

    # List employees
    r = api("GET", "/api/employees")
    emps = r.json()
    check("Employee list", len(emps) >= 1, f"{len(emps)} employees")

    # Stats
    r = api("GET", "/api/employees/stats")
    stats = r.json()
    check("Employee stats", stats.get("total", 0) >= 1)

    # Edit employee
    r = api("PUT", f"/api/employees/{emp_id_val}", json={
        "department": "技术部-基础架构组",
        "salary": "45K×14薪",
        "status": "regular",
    })
    check("Edit employee", r.status_code == 200)

    # Verify edit
    r = api("GET", f"/api/employees/{emp_id_val}")
    emp = r.json()
    check("Department updated", emp.get("department") == "技术部-基础架构组")
    check("Status updated", emp.get("status") == "regular")


# ── 12. Talent Pool ──
print("\n[12] Talent Pool Search")

# Keyword search
r = api("GET", "/api/talent-pool", params={"q": "后端"})
kw_result = r.json()
check("Keyword search", len(kw_result) >= 0, f"{len(kw_result)} results")

# Semantic search
r = api("POST", "/api/talent-pool/search", json={"query": "有后端开发经验的工程师", "threshold": 0.2})
sem_result = r.json()
check("Semantic search", "results" in sem_result, f"{len(sem_result.get('results',[]))} results")

# Similar candidates
first_cand = results_by_file.get(pdfs[0].name, {})
if first_cand.get("cand_id"):
    r = api("GET", f"/api/talent-pool/similar/{first_cand['cand_id']}")
    similar = r.json()
    check("Similar candidates", "similar" in similar, f"{len(similar.get('similar',[]))} similar")


# ── 13. File preview ──
print("\n[13] File Preview")

if emp_id:
    emp_id_val = emp_id
    # Test diploma preview (may or may not have file, but endpoint should work)
    r = api("GET", f"/api/employees/{emp_id_val}/file", params={"type": "diploma"})
    check("File preview endpoint", r.status_code in (200, 404), f"status={r.status_code}")


# ── 14. Webhook notification test ──
print("\n[14] Webhook Notifications")
r = api("POST", "/api/notify/test")
check("Webhook test endpoint", r.status_code == 200, f"ok={r.json().get('ok')}")


# ── 15. Dashboard refresh ──
print("\n[15] Final Dashboard Check")
r = api("GET", "/api/dashboard/stats")
dash2 = r.json()
check("Dashboard accessible", r.status_code == 200)
check("Stats reflect new data", dash2.get("candidate_count", 0) >= 3)


# ============================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
if failed == 0:
    print("ALL TESTS PASSED - Full pipeline is working!")
else:
    print(f"WARNING: {failed} test(s) failed - check above for details")
print("=" * 60)
