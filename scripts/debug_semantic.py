"""Debug semantic search: compare query embedding vs candidate embeddings."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import SessionLocal
from models.candidate import Candidate
from ai_service.embeddings import mock_embedding, cosine_similarity, _tokenize, generate_embedding

db = SessionLocal()
candidates = db.query(Candidate).filter(Candidate.embedding.isnot(None)).all()

queries = [
    "有AI产品经验的候选人",
    "海外运营增长经验",
    "Go后端微服务架构师",
    "AI产品经理",
]

for query_text in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query_text}")
    query_tokens = _tokenize(query_text)
    print(f"Tokens: {query_tokens[:20]}...")

    # Try real embedding
    query_emb = generate_embedding(query_text)
    if query_emb is None:
        query_emb = mock_embedding(query_text)
    print(f"Embedding: first 5 values: {query_emb[:5]}")

    scored = []
    for c in candidates:
        emb = c.embedding
        if hasattr(emb, 'tolist'):
            emb = emb.tolist()
        elif isinstance(emb, str):
            emb = json.loads(emb)
        if not emb:
            continue
        sim = cosine_similarity(query_emb, emb)
        scored.append((c.name, c.profile.get("current_position", ""), sim))

    scored.sort(key=lambda x: x[2], reverse=True)
    for name, pos, sim in scored:
        marker = " *** MATCH ***" if sim >= 0.35 else ""
        print(f"  {name:8s} | {pos:15s} | sim={sim:.4f}{marker}")

db.close()
