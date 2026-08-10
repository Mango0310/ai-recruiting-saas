import httpx

# Test 1: ping test endpoint
r = httpx.post("http://localhost:8000/api/notify/test", timeout=10)
print("Test notify:", r.json())

# Test 2: upload resume triggers new candidate notification
with open(r"D:/honor share/ai-recruiting-saas/demo-data/resumes/candidate_02_biao_mian.pdf", "rb") as f:
    r = httpx.post("http://localhost:8000/api/jobs/1/resumes",
                   files=[("files", ("test.pdf", f, "application/pdf"))],
                   timeout=180)
    data = r.json()
    result = data["results"][0]
    print("Upload:", result["status"], result.get("candidate_name", "?"))

print("Done — check Feishu for 2 new messages!")
