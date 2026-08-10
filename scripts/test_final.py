import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import httpx

BASE = "http://localhost:8000"
pdf_path = Path(r"D:\honor share\ai-recruiting-saas\demo-data\resumes\candidate_01_gao_pipei.pdf")

# Test against job 2 (海外运营经理) for cross-job matching
with open(pdf_path, "rb") as f:
    t0 = time.time()
    resp = httpx.post(f"{BASE}/api/jobs/2/resumes",
                      files=[("files", (pdf_path.name, f, "application/pdf"))],
                      timeout=180)
    elapsed = time.time() - t0

print(f"Upload: {resp.status_code} ({elapsed:.1f}s)")
data = resp.json()
for r in data["results"]:
    print(f"Status: {r.get('status')}, Name: {r.get('candidate_name')}")
    if r.get("application_id"):
        app_id = r["application_id"]
        mr = httpx.get(f"{BASE}/api/applications/{app_id}/report", timeout=60).json()
        rep = mr.get("match_report", {})
        stars = int(rep.get("star_rating", 0))
        filled = "*" * stars
        empty = "o" * (5 - stars)
        print(f"Stars: {filled}{empty}")
        print(f"Conclusion: {rep.get('overall_conclusion')}")
        print(f"Summary: {rep.get('summary')}")
        strengths = [s["point"] for s in rep.get("strengths", [])]
        print(f"Strengths ({len(strengths)}): {strengths}")
        gaps = [g["point"] for g in rep.get("gaps", [])]
        print(f"Gaps ({len(gaps)}): {gaps}")

print("\nPipeline test complete.")
