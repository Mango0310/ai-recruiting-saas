import httpx

r = httpx.post("http://localhost:8000/api/auth/register", json={
    "email": "admin@demo.com",
    "password": "demo123",
    "name": "HR管理员",
    "company_name": "跨境通科技"
}, timeout=10)
print(r.status_code)
if r.status_code == 200:
    d = r.json()
    print("User:", d["user"]["name"])
    print("Company:", d["user"]["company_name"])
    print("CoID:", d["user"]["company_id"])
else:
    print(r.text)
