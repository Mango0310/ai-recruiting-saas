import httpx, json

BASE = "http://localhost:8000"

# Test 1: Health
r = httpx.get(f"{BASE}/api/health", timeout=5)
print(f"1. Health: {r.status_code} {r.json()}")

# Test 2: Register
r = httpx.post(f"{BASE}/api/auth/register", json={
    "email": "hr1@demo.com", "password": "1234",
    "name": "张HR", "company_name": "跨境通科技"
}, timeout=10)
print(f"2. Register: {r.status_code}")
d = r.json()
token = d.get("token", "")
print(f"   user={d['user']['name']}, company={d['user']['company_name']}, token={token[:20]}...")

# Test 3: Login
r = httpx.post(f"{BASE}/api/auth/login", json={
    "email": "hr1@demo.com", "password": "1234"
}, timeout=10)
print(f"3. Login: {r.status_code}, token={r.json().get('token','')[:20]}...")

# Test 4: Me
r = httpx.get(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
print(f"4. Me: {r.status_code} {r.json().get('name')}")

# Test 5: Register same company
r = httpx.post(f"{BASE}/api/auth/register", json={
    "email": "hr2@demo.com", "password": "1234",
    "name": "李HR", "company_name": "跨境通科技"
}, timeout=10)
print(f"5. Register same co: {r.status_code}, co_id={r.json()['user']['company_id']}")

# Test 6: Dashboard with auth
r = httpx.get(f"{BASE}/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"}, timeout=10)
s = r.json()
print(f"6. Dashboard auth: jobs={s.get('job_count')}, cands={s.get('candidate_count')}")

print("\nAll auth tests done!")
