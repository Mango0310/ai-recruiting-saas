import httpx, json

r = httpx.get("http://localhost:8000/api/employees/1/profile-report", timeout=120)
print("Status:", r.status_code)
data = r.json()
print("Employee:", data["employee_name"], data["position"])
p = data["profile"]
print("\nSummary:", p["summary"])
print("Career stage:", p["career_stage"])
print("Team role:", p["team_role"])
print("\nScores:")
for dim, val in p["scores"].items():
    print(f"  {dim}: {val['score']}/10 — {val['evidence'][:60]}")
print("\nStrengths:")
for s in p["strengths"]:
    print(f"  + {s['point']}")
print("\nGrowth areas:")
for g in p["growth_areas"]:
    print(f"  - {g['point']} → {g['suggestion']}")
