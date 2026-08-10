"""Test semantic search and similar candidates."""
import httpx, json

BASE = "http://localhost:8000"

print("=== Semantic Search ===")

# Test 1: Find AI product managers
r = httpx.post(f"{BASE}/api/talent-pool/search", json={"query": "有AI产品经验的候选人", "threshold": 0.2})
data = r.json()
print(f"\nQuery: '有AI产品经验的候选人'")
print(f"Status: {r.status_code}, Results: {len(data['results'])}")
for c in data["results"]:
    print(f"  {c['name']:8s} | {c['current_position']:15s} | score={c['score']:.3f} | {c['skills'][:3]}")

# Test 2: Find overseas/operations people
r = httpx.post(f"{BASE}/api/talent-pool/search", json={"query": "海外运营增长经验", "threshold": 0.3})
data = r.json()
print(f"\nQuery: '海外运营增长经验'")
print(f"Results: {len(data['results'])}")
for c in data["results"]:
    print(f"  {c['name']:8s} | {c['current_position']:15s} | score={c['score']:.3f}")

# Test 3: Find backend engineers (none in DB)
r = httpx.post(f"{BASE}/api/talent-pool/search", json={"query": "Go后端微服务架构师", "threshold": 0.3})
data = r.json()
print(f"\nQuery: 'Go后端微服务架构师' (no exact match)")
print(f"Results: {len(data['results'])}")
for c in data["results"]:
    print(f"  {c['name']:8s} | {c['current_position']:15s} | score={c['score']:.3f}")

# Test 4: Similar candidates
print(f"\n=== Similar Candidates ===")
r = httpx.get(f"{BASE}/api/talent-pool/similar/1")
data = r.json()
print(f"Similar to: {data['source']['name']}")
for c in data["similar"]:
    print(f"  {c['name']:8s} | {c['current_position']:15s} | score={c['score']:.3f}")

print("\nDone!")
