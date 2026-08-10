import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "backend" / ".env")
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"

DATA_DIR.mkdir(parents=True, exist_ok=True)
(STORAGE_DIR / "resumes").mkdir(parents=True, exist_ok=True)
(STORAGE_DIR / "exports").mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'ai_recruit.db'}")

# PostgreSQL + pgvector (set DATABASE_URL to postgresql://... to enable)
VECTOR_DIM = 1536  # DeepSeek embeddings dimension
SIMILARITY_THRESHOLD = 0.25  # minimum cosine similarity for semantic search

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

UPLOAD_MAX_SIZE_MB = 20
UPLOAD_ALLOWED_TYPES = {"application/pdf"}
