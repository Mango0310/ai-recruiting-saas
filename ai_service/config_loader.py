import os
from pathlib import Path
from dotenv import load_dotenv

_env_loaded = False


def get_config() -> dict:
    global _env_loaded
    if not _env_loaded:
        env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        _env_loaded = True

    return {
        "provider": os.getenv("LLM_PROVIDER", "deepseek"),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        "model": os.getenv("LLM_MODEL", "deepseek-chat"),
    }
