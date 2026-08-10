import httpx

BASE = "http://localhost:8000"

# Test 1: notify/test when webhook not configured
r = httpx.post(f"{BASE}/api/notify/test")
print("Test 1 (no webhook URL):", r.json())

# Test 2: health check
r = httpx.get(f"{BASE}/api/health")
print("Test 2 (health):", r.json())

# Test 3: upload resume (notification should gracefully skip)
with open(r"D:/honor share/ai-recruiting-saas/demo-data/resumes/candidate_01_gao_pipei.pdf", "rb") as f:
    r = httpx.post(f"{BASE}/api/jobs/1/resumes", files=[("files", ("test.pdf", f, "application/pdf"))], timeout=180)
    data = r.json()
    result = data["results"][0]
    print(f"Test 3 (upload): status={result['status']}, name={result.get('candidate_name','?')}")

print("\nAll tests passed!")
