"""End-to-end test: create tech/design jobs, upload resumes, verify role-aware parsing.

Run from backend dir: cd backend && .venv\Scripts\python.exe ..\scripts\test_e2e_role.py
"""
import sys, json, time
from pathlib import Path
import httpx

BASE = "http://localhost:8000"
DEMO_PDF = Path(r"D:\honor share\ai-recruiting-saas\demo-data\resumes\candidate_01_gao_pipei.pdf")

print("=" * 60)
print("E2E: Role-Aware Resume Parsing")
print("=" * 60)

# Step 1: Create a tech job (后端工程师)
print("\n1. Creating tech job (后端工程师)...")
t0 = time.time()
tech_jd = "高级后端工程师\n职责：负责微服务架构设计与开发，优化系统性能，参与技术选型。\n要求：5年以上后端开发经验，精通Go/Python，熟悉分布式系统。"
r = httpx.post(f"{BASE}/api/jobs", json={"title": "高级后端工程师", "jd_text": tech_jd}, timeout=120)
tech_job = r.json()
elapsed = time.time() - t0
print(f"   Job created: id={tech_job['id']} ({elapsed:.1f}s)")
rc = tech_job.get("job_profile", {}).get("role_category", "MISSING")
print(f"   role_category: {rc} {'[OK]' if rc == 'tech' else '[UNEXPECTED]'}")

# Step 2: Upload resume to tech job
print(f"\n2. Uploading resume to tech job ({tech_job['id']})...")
with open(DEMO_PDF, "rb") as f:
    t0 = time.time()
    r = httpx.post(f"{BASE}/api/jobs/{tech_job['id']}/resumes",
                   files=[("files", (DEMO_PDF.name, f, "application/pdf"))], timeout=180)
    elapsed = time.time() - t0

data = r.json()
result = data["results"][0]
print(f"   Status: {result.get('status')} ({elapsed:.1f}s)")
cand_id = result.get("candidate_id")
print(f"   Candidate: {result.get('candidate_name')} (id={cand_id})")

# Step 3: Check candidate profile for tech-specific fields
print(f"\n3. Checking candidate {cand_id} profile for tech fields...")
r = httpx.get(f"{BASE}/api/candidates/{cand_id}", timeout=30)
cand = r.json()
profile = cand.get("profile", {})

has_tech = "tech_stack_depth" in profile
has_github = "github_username" in profile
print(f"   tech_stack_depth: {'PRESENT' if has_tech else 'MISSING'}")
print(f"   github_username: {'PRESENT' if has_github else 'MISSING'}")
if has_tech:
    tsd = profile["tech_stack_depth"]
    print(f"     primary_languages: {tsd.get('primary_languages')}")
    print(f"     scale_context: {tsd.get('scale_context', '')[:80]}...")

# Step 4: Create a design job
print("\n4. Creating design job (UI设计师)...")
design_jd = "资深UI设计师\n职责：负责B2B SaaS产品界面设计，搭建和维护设计系统。\n要求：3年以上UI设计经验，精通Figma，有设计系统搭建经验。"
r = httpx.post(f"{BASE}/api/jobs", json={"title": "资深UI设计师", "jd_text": design_jd}, timeout=120)
design_job = r.json()
rc = design_job.get("job_profile", {}).get("role_category", "MISSING")
print(f"   role_category: {rc} {'[OK]' if rc == 'design' else '[UNEXPECTED]'}")

# Step 5: Upload resume to design job
print(f"\n5. Uploading resume to design job ({design_job['id']})...")
with open(DEMO_PDF, "rb") as f:
    t0 = time.time()
    r = httpx.post(f"{BASE}/api/jobs/{design_job['id']}/resumes",
                   files=[("files", (DEMO_PDF.name, f, "application/pdf"))], timeout=180)
    elapsed = time.time() - t0

data = r.json()
result = data["results"][0]
cand_id2 = result.get("candidate_id")
print(f"   Candidate: {result.get('candidate_name')} (id={cand_id2})")

# Step 6: Check design candidate profile
print(f"\n6. Checking candidate {cand_id2} profile for design fields...")
r = httpx.get(f"{BASE}/api/candidates/{cand_id2}", timeout=30)
cand2 = r.json()
profile2 = cand2.get("profile", {})

has_portfolio = "portfolio_url" in profile2
has_design_tools = "design_tools" in profile2
print(f"   portfolio_url: {'PRESENT' if has_portfolio else 'MISSING'}")
print(f"   design_tools: {'PRESENT' if has_design_tools else 'MISSING'}")
if has_portfolio:
    print(f"     url: {profile2.get('portfolio_url')}")
if has_design_tools:
    tools = profile2.get("design_tools", [])
    print(f"     tools: {[(t.get('tool'), t.get('proficiency')) for t in tools]}")

print("\n" + "=" * 60)
print("E2E test complete!")
print("=" * 60)
