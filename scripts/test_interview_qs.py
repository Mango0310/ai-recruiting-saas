import httpx, json

BASE = "http://localhost:8000"

# Get an application with match data
r = httpx.get(f"{BASE}/api/jobs/1/candidates", timeout=10)
cands = r.json()
if cands:
    app_id = cands[0]["application_id"]
    name = cands[0]["candidate_name"]
    print(f"Testing with: {name} (app_id={app_id})")

    r = httpx.post(f"{BASE}/api/applications/{app_id}/interview-questions", timeout=120)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        iq = d["interview_questions"]
        print(f"Focus: {iq.get('interview_focus', [])}")
        print(f"Duration: {iq.get('estimated_total_duration')}")
        print(f"Difficulty: {iq.get('difficulty_assessment')}")
        structure = iq.get("interview_structure", {})
        for phase, qs in structure.items():
            print(f"\n[{phase}] {len(qs)} questions:")
            for q in qs[:2]:
                print(f"  Q: {q['question'][:60]}...")
                if q.get("why"):
                    print(f"     Why: {q['why'][:60]}")
    else:
        print(f"Error: {r.text[:300]}")
else:
    print("No candidates found!")
