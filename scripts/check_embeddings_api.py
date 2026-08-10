"""Check if DeepSeek Embeddings API is available."""
import httpx, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ai_service.config_loader import get_config

cfg = get_config()
api_key = cfg["api_key"]
print(f"API Key: {'YES' if api_key else 'NO'}")
print(f"Base URL: {cfg['base_url']}")

url = f"{cfg['base_url']}/embeddings"
print(f"Trying: {url}")

try:
    r = httpx.post(url, json={"model": "deepseek-chat", "input": "test"},
                   headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                   timeout=15)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        dims = len(data["data"][0]["embedding"])
        print(f"Embedding dims: {dims}")
        print("DeepSeek Embeddings API: AVAILABLE")
    else:
        print(f"Response: {r.text[:200]}")
        print("DeepSeek Embeddings API: NOT AVAILABLE")
except Exception as e:
    print(f"Error: {e}")
    print("DeepSeek Embeddings API: NOT AVAILABLE")
