from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, is_sqlite
from models.candidate import Candidate
from models.application import Application
from models.ai_analysis import AIAnalysis
from models.job import Job
from models.user import User
from auth import require_user
from config import SIMILARITY_THRESHOLD
from services.multi_tenant import get_company_job_ids

router = APIRouter(prefix="/api/talent-pool", tags=["talent-pool"])


def _candidate_in_company(candidate_id: int, db: Session, company_job_ids: set) -> bool:
    """Check if candidate has any application in the company's jobs."""
    apps = db.query(Application).filter(Application.candidate_id == candidate_id).all()
    return any(a.job_id in company_job_ids for a in apps)


@router.get("")
def search_talent_pool(
    q: str = Query(default="", description="Search keyword"),
    skill: str = Query(default="", description="Filter by skill tag"),
    status: str = Query(default="", description="Filter by HR decision"),
    type: str = Query(default="", description="Filter by talent type: hired, talent_pool, or empty for all"),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    company_job_ids = get_company_job_ids(db, user)
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).limit(200).all()

    results = []
    for c in candidates:
        if not _candidate_in_company(c.id, db, company_job_ids):
            continue

        profile = c.profile or {}
        skills = profile.get("skills", [])
        current_position = profile.get("current_position", "")
        current_company = profile.get("current_company", "")

        if q:
            q_lower = q.lower().strip()
            searchable = " ".join([
                c.name or "",
                current_position,
                current_company,
                " ".join(skills),
            ]).lower()
            if q_lower not in searchable:
                continue

        if skill:
            if skill.lower().strip() not in " ".join(skills).lower():
                continue

        applications = db.query(Application).filter(
            Application.candidate_id == c.id
        ).order_by(Application.created_at.desc()).all()
        latest_app = applications[0] if applications else None

        hr_decision = (latest_app.hr_decision or "pending") if latest_app else "pending"

        if status and hr_decision != status:
            continue

        talent_type = profile.get("talent_type", "")
        if type:
            if type == "hired" and talent_type != "hired":
                continue
            if type == "talent_pool" and talent_type == "hired":
                continue
            if type == "all_candidates" and talent_type:
                continue

        star_rating = None
        job_title = ""
        app_id = None
        if latest_app:
            app_id = latest_app.id
            job_title = latest_app.job.title if latest_app.job else ""
            analysis = (
                db.query(AIAnalysis)
                .filter(AIAnalysis.application_id == latest_app.id)
                .order_by(AIAnalysis.created_at.desc())
                .first()
            )
            if analysis and analysis.match_report:
                star_rating = analysis.match_report.get("star_rating")

        results.append({
            "id": c.id,
            "name": c.name,
            "current_position": current_position,
            "current_company": current_company,
            "skills": skills,
            "years_of_experience": profile.get("years_of_experience", 0),
            "application_count": len(applications),
            "latest_job": job_title,
            "application_id": app_id,
            "hr_decision": hr_decision,
            "star_rating": star_rating,
            "created_at": str(c.created_at),
        })

    return results


class SemanticQuery(BaseModel):
    query: str
    threshold: float = 0.0


@router.post("/search")
def semantic_search(body: SemanticQuery, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Semantic search candidates by natural language description."""
    query = body.query.strip()
    if not query:
        return {"results": [], "query": query}

    threshold = body.threshold or SIMILARITY_THRESHOLD

    from ai_service.embeddings import generate_embedding, mock_embedding, cosine_similarity
    query_emb = generate_embedding(query)
    if query_emb is None:
        query_emb = mock_embedding(query)

    company_job_ids = get_company_job_ids(db, user)
    candidates = db.query(Candidate).filter(Candidate.embedding.isnot(None)).limit(500).all()

    scored = []
    for c in candidates:
        if not _candidate_in_company(c.id, db, company_job_ids):
            continue

        cand_emb = c.embedding
        if not cand_emb:
            continue
        if hasattr(cand_emb, 'tolist'):
            cand_emb = cand_emb.tolist()
        elif isinstance(cand_emb, str):
            import json
            cand_emb = json.loads(cand_emb)

        sim = cosine_similarity(query_emb, cand_emb)
        if sim >= threshold:
            profile = c.profile or {}
            scored.append({
                "id": c.id,
                "name": c.name,
                "current_position": profile.get("current_position", ""),
                "current_company": profile.get("current_company", ""),
                "skills": profile.get("skills", [])[:8],
                "years_of_experience": profile.get("years_of_experience", 0),
                "score": round(sim, 3),
                "created_at": str(c.created_at),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"results": scored[:20], "query": query, "total": len(scored)}


@router.get("/similar/{candidate_id}")
def similar_candidates(candidate_id: int, top_k: int = Query(default=5), db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Find candidates similar to a given candidate based on embedding similarity."""
    company_job_ids = get_company_job_ids(db, user)

    source = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not _candidate_in_company(source.id, db, company_job_ids):
        raise HTTPException(status_code=403, detail="Access denied")
    if not source.embedding:
        return {"source": {"id": source.id, "name": source.name}, "similar": [], "message": "Source candidate has no embedding"}

    from ai_service.embeddings import cosine_similarity

    source_emb = source.embedding
    if hasattr(source_emb, 'tolist'):
        source_emb = source_emb.tolist()
    elif isinstance(source_emb, str):
        import json
        source_emb = json.loads(source_emb)

    candidates = db.query(Candidate).filter(
        Candidate.id != candidate_id,
        Candidate.embedding.isnot(None)
    ).limit(500).all()

    scored = []
    for c in candidates:
        if not _candidate_in_company(c.id, db, company_job_ids):
            continue
        cand_emb = c.embedding
        if hasattr(cand_emb, 'tolist'):
            cand_emb = cand_emb.tolist()
        elif isinstance(cand_emb, str):
            import json
            cand_emb = json.loads(cand_emb)
        if not cand_emb:
            continue

        sim = cosine_similarity(source_emb, cand_emb)
        profile = c.profile or {}
        scored.append({
            "id": c.id,
            "name": c.name,
            "current_position": profile.get("current_position", ""),
            "skills": profile.get("skills", [])[:6],
            "score": round(sim, 3),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {
        "source": {"id": source.id, "name": source.name},
        "similar": scored[:top_k],
    }


@router.get("/{candidate_id}")
def get_talent_detail(candidate_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    company_job_ids = get_company_job_ids(db, user)
    if not _candidate_in_company(candidate.id, db, company_job_ids):
        raise HTTPException(status_code=403, detail="Access denied")

    applications = db.query(Application).filter(Application.candidate_id == candidate_id).all()

    return {
        "id": candidate.id,
        "name": candidate.name,
        "profile": candidate.profile,
        "applications": [
            {
                "application_id": app.id,
                "job_id": app.job_id,
                "job_title": app.job.title if app.job else "",
                "status": app.status,
                "hr_decision": app.hr_decision,
                "hr_notes": app.hr_notes,
            }
            for app in applications
            if app.job_id in company_job_ids
        ],
    }
