import httpx, json, time

BASE = "http://localhost:8000"

# Test 1: Get company
print("1. Get company:")
r = httpx.get(f"{BASE}/api/company", timeout=10)
c = r.json()
print(f"   name={c.get('name')}, docs={len(c.get('knowledge_docs',[]))}, text_len={len(c.get('knowledge_text',''))}")

# Test 2: Update knowledge text
print("\n2. Update knowledge text:")
r = httpx.put(f"{BASE}/api/company", json={
    "knowledge_text": "我们是跨境通科技，专注跨境电商SaaS。核心产品是智能选品和广告投放工具。技术栈Go+React，团队50人，文化强调数据驱动。"
}, timeout=10)
print(f"   status={r.status_code}")

# Test 3: Upload a document
print("\n3. Upload knowledge doc:")
with open(r"D:/honor share/ai-recruiting-saas/demo-data/jobs/ai-product-manager.md", "rb") as f:
    r = httpx.post(f"{BASE}/api/company/knowledge/upload",
                   files=[("file", ("ai-product-manager.md", f, "text/markdown"))], timeout=30)
    print(f"   status={r.status_code}, id={r.json().get('id','?')[:10]}...")

# Test 4: Verify knowledge injected into JD
print("\n4. Create job (knowledge should be injected):")
t0 = time.time()
r = httpx.post(f"{BASE}/api/jobs", json={"title":"AI产品经理","jd_text":"负责AI产品设计"}, timeout=60)
print(f"   status={r.status_code} ({time.time()-t0:.1f}s)")
jp = r.json().get("job_profile", {})
# The JD should now reflect company context
print(f"   role_category={jp.get('role_category')}, skills={jp.get('skill_tags', [])[:4]}")

# Test 5: List knowledge docs
print("\n5. List knowledge docs:")
r = httpx.get(f"{BASE}/api/company", timeout=10)
docs = r.json().get("knowledge_docs", [])
print(f"   {len(docs)} docs")
for d in docs:
    print(f"   - {d['name']} ({len(d.get('snippet',''))} chars snippet)")

# Test 6: Delete
if docs:
    doc_id = docs[0]["id"]
    r = httpx.delete(f"{BASE}/api/company/knowledge/{doc_id}", timeout=10)
    print(f"\n6. Delete: status={r.status_code}")

print("\nAll done!")
