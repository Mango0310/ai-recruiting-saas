"""Start ngrok tunnels for both frontend (3000) and backend (8000)."""
import json, httpx, subprocess, sys, time

# Check if ngrok is already running
try:
    r = httpx.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
    tunnels = r.json().get("tunnels", [])
    for t in tunnels:
        print(f"Existing: {t['config']['addr']} -> {t['public_url']}")
except:
    print("Starting ngrok...")
    subprocess.Popen(
        [r"D:\honor share\ai-recruiting-saas\tools\ngrok\ngrok.exe", "http", "3000", "--log=stdout"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(4)

# Get frontend URL
r = httpx.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
tunnels = r.json().get("tunnels", [])
fe_url = ""
for t in tunnels:
    if "3000" in t["config"]["addr"]:
        fe_url = t["public_url"]
        break

if fe_url:
    # Start backend tunnel via API
    r = httpx.post("http://127.0.0.1:4040/api/tunnels", json={
        "name": "backend", "addr": "8000", "proto": "http"
    }, timeout=10)
    be_url = r.json().get("public_url", "")

    print(f"\nFrontend: {fe_url}")
    print(f"Backend:  {be_url}")
    print(f"\nUpdate frontend/src/lib/api.ts baseURL to: {be_url}/api")
    print(f"Then restart frontend (npm run dev)\n")
else:
    print("No frontend tunnel found. Is ngrok running?")

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("\nDone.")
