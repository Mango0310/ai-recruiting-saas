"""Quick test script for PDF upload pipeline. Run from backend dir with venv Python."""
import sys, json, time
from pathlib import Path
import httpx

BASE = "http://localhost:8000"
DEMO_DIR = Path(r"D:\honor share\ai-recruiting-saas\demo-data\resumes")
# Test only the third PDF (first two already uploaded successfully)
TEST_FILES = [DEMO_DIR / "candidate_03_di_pipei.pdf"]
JOB_ID = 1

def test_upload(pdf_path: Path):
    print(f"\n{'='*60}")
    print(f"Uploading: {pdf_path.name}")
    print(f"{'='*60}")

    with open(pdf_path, "rb") as f:
        files = [("files", (pdf_path.name, f, "application/pdf"))]
        t0 = time.time()
        resp = httpx.post(f"{BASE}/api/jobs/{JOB_ID}/resumes", files=files, timeout=180)
        elapsed = time.time() - t0

    print(f"Status: {resp.status_code} ({elapsed:.1f}s)")
    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))

    if data.get("results"):
        for r in data["results"]:
            status = r.get("status")
            if status == "completed":
                app_id = r.get("application_id")
                cand_id = r.get("candidate_id")
                print(f"\n  Candidate: {r.get('candidate_name')} (id={cand_id})")
                print(f"  Application id: {app_id}")

                if app_id:
                    t0 = time.time()
                    mr_resp = httpx.get(f"{BASE}/api/applications/{app_id}/report", timeout=60)
                    print(f"  Match report: {mr_resp.status_code} ({time.time()-t0:.1f}s)")
                    if mr_resp.status_code == 200:
                        mr = mr_resp.json()
                        report = mr.get("match_report", {})
                        stars = int(report.get('star_rating', 0))
                        print(f"  Stars: {'★'*stars}{'☆'*(5-stars)}")
                        print(f"  Conclusion: {report.get('overall_conclusion', 'N/A')}")
                        print(f"  Strengths: {len(report.get('strengths',[]))} items")
                        print(f"  Gaps: {len(report.get('gaps',[]))} items")
                        for s in report.get('strengths', [])[:2]:
                            print(f"    + {s.get('point','')}")
                        for g in report.get('gaps', [])[:2]:
                            print(f"    - {g.get('point','')}")

            elif status == "failed":
                print(f"  FAILED: {r.get('error')}")

if __name__ == "__main__":
    for pdf in TEST_FILES:
        test_upload(pdf)
    print("\nDone.")
