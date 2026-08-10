"""Generate text embeddings via DeepSeek API (OpenAI-compatible).

In SQLite mode, embeddings are stored as JSON arrays and compared with
cosine similarity in Python. In PostgreSQL mode, pgvector handles ANN search.
"""

import json
import math
import httpx
from typing import Optional, List

from ai_service.config_loader import get_config


def _build_search_text(profile: dict, title: str = "") -> str:
    """Build a searchable text blob from a candidate or job profile for embedding."""
    parts = []
    if title:
        parts.append(title)
    if profile:
        parts.append(profile.get("current_position", ""))
        parts.append(profile.get("current_company", ""))
        skills = profile.get("skills", [])
        if skills:
            parts.append(" ".join(skills))
        strengths = profile.get("strengths", [])
        if strengths:
            parts.append(" ".join(strengths))
        # Work experience summaries
        for exp in profile.get("work_experience", [])[:3]:
            parts.append(f"{exp.get('position','')} at {exp.get('company','')}")
            for proj in exp.get("projects", [])[:2]:
                parts.append(proj.get("description", ""))
    return " ".join(p for p in parts if p).strip()


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding vector for text via DeepSeek API.

    Returns a list of floats (1536 dims) or None on failure.
    Never raises — callers should handle None.
    """
    if not text.strip():
        return None

    cfg = get_config()
    if not cfg.get("api_key"):
        return None

    url = f"{cfg['base_url']}/embeddings"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "input": text,
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data["data"][0]["embedding"]
    except Exception:
        return None


def generate_candidate_embedding(profile: dict) -> Optional[List[float]]:
    """Generate embedding for a candidate from their profile."""
    text = _build_search_text(profile, profile.get("current_position", ""))
    return generate_embedding(text)


def generate_job_embedding(job_profile: dict, title: str = "") -> Optional[List[float]]:
    """Generate embedding for a job from its profile."""
    text = _build_search_text(job_profile, title)
    return generate_embedding(text)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# Common Chinese stopwords that don't carry semantic meaning
_STOP_TOKENS = {
    "有", "的", "和", "了", "在", "是", "我", "你", "他", "她", "它",
    "这", "那", "个", "们", "吗", "吧", "啊", "呢", "哦", "嗯",
    "及", "与", "或", "从", "到", "对", "以", "为", "用",
    "经验", "经历", "要求", "熟悉", "了解", "掌握", "具备",
    "相关", "进行", "能够", "可以", "需要",
    "工作", "负责", "参与", "完成",
    "以上", "以下",
    "候选人", "求职", "应聘", "招聘",
    "不", "就", "还", "也", "比较", "非常", "很", "都",
}


def _tokenize(text: str) -> List[str]:
    """Tokenize Chinese + English text into meaningful tokens for embedding."""
    tokens = []
    import re
    words = re.split(r'[\s,，、。；;：:！!？?()（）【】\[\]{}""''/\-_—@#\$%^&\*\+=\|\\~`]+', text.lower())
    for word in words:
        word = word.strip()
        if not word or len(word) <= 1:
            continue
        if word in _STOP_TOKENS:
            continue
        if re.match(r'^[a-z0-9]+$', word):
            if len(word) >= 2:  # skip single letters
                tokens.append(word)
        else:
            for i in range(len(word) - 1):
                bigram = word[i:i+2]
                if bigram not in _STOP_TOKENS:
                    tokens.append(bigram)
    return tokens


# Mock embeddings for offline/demo mode — keyword-bigram based so similar profiles produce similar vectors
def mock_embedding(text: str, dim: int = 1536) -> List[float]:
    """Generate a keyword-overlap-based mock embedding.

    Similar keyword sets produce similar vectors (via bigram token overlap).
    This enables semantic search to work without a real embeddings API.
    """
    import hashlib
    tokens = _tokenize(text)
    if not tokens:
        tokens = ["_empty_"]

    values = [0.0] * dim

    for tok in tokens:
        h = hashlib.shake_128(tok.encode()).digest(8)
        seed = int.from_bytes(h, 'little')
        for j in range(3):
            idx = ((seed >> (j * 16)) & 0xFFFF) % dim
            sign = 1.0 if ((seed >> (48 + j)) & 1) else -1.0
            values[idx] += sign

    norm = math.sqrt(sum(v * v for v in values))
    if norm > 0:
        values = [v / norm for v in values]
    return values
