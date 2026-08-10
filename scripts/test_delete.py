import httpx

# Create a duplicate job
r = httpx.post("http://localhost:8000/api/jobs",
               json={"title": "高级后端工程师", "jd_text": "测试重复岗位"}, timeout=30)
dup = r.json()
print("Created duplicate: id =", dup["id"])

# Now delete it
r = httpx.delete(f"http://localhost:8000/api/jobs/{dup['id']}", timeout=10)
print("Delete status:", r.status_code, "body:", r.text)

# Verify
r = httpx.get("http://localhost:8000/api/jobs", timeout=10)
jobs = r.json()
print("Remaining jobs:", len(jobs))
for j in jobs:
    print("  ", j["id"], ":", j["title"])
