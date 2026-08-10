from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.job import Job
from models.user import User
from auth import require_user
from services.jd_service import create_job_from_jd, reanalyze_job, probe_questions, generate_full_profile
from services.multi_tenant import filtered_job_query

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _check_job_access(job_id: int, user: User, db: Session) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return job


class JobCreate(BaseModel):
    title: str
    jd_text: str


class JobUpdate(BaseModel):
    title: Optional[str] = None
    jd_raw: Optional[str] = None
    job_profile: Optional[dict] = None


class ProbeRequest(BaseModel):
    title: str
    department: str = ""
    reports_to: str = ""
    salary: str = ""
    company_name: str = ""
    company_industry: str = ""
    company_size: str = ""
    business_stage: str = ""
    target_audience: str = ""
    product_stage: str = ""
    team_role: str = ""
    tech_required: str = ""
    requirement_source: str = ""
    raw_requirements: str = ""
    hiring_reason: str = ""
    team_context: str = ""
    three_month_goal: str = ""
    notes: str = ""


class FullCreateRequest(BaseModel):
    title: str
    department: str = ""
    reports_to: str = ""
    salary: str = ""
    company_name: str = ""
    company_industry: str = ""
    company_size: str = ""
    business_stage: str = ""
    target_audience: str = ""
    product_stage: str = ""
    team_role: str = ""
    tech_required: str = ""
    requirement_source: str = ""
    raw_requirements: str = ""
    hiring_reason: str = ""
    team_context: str = ""
    three_month_goal: str = ""
    notes: str = ""
    ai_questions: list = []


@router.post("")
def create_job(body: JobCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    job = create_job_from_jd(db, body.title, body.jd_text)
    job.company_id = user.company_id
    db.commit()
    return {
        "id": job.id,
        "title": job.title,
        "job_profile": job.job_profile,
        "status": job.status,
        "created_at": str(job.created_at),
    }


@router.post("/probe")
def probe(body: ProbeRequest, user: User = Depends(require_user)):
    """AI generates follow-up questions based on the hiring context."""
    questions = probe_questions(body.model_dump())
    return {"questions": questions}


@router.post("/create-full")
def create_full(body: FullCreateRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Generate complete job profile with competency model + evaluation framework."""
    job = generate_full_profile(db, body.model_dump())
    job.company_id = user.company_id
    db.commit()
    return {
        "id": job.id,
        "title": job.title,
        "job_profile": job.job_profile,
        "status": job.status,
        "created_at": str(job.created_at),
    }


@router.get("")
def list_jobs(db: Session = Depends(get_db), user: User = Depends(require_user)):
    jobs = filtered_job_query(db, user).order_by(Job.created_at.desc()).all()
    return [
        {
            "id": j.id,
            "title": j.title,
            "status": j.status,
            "candidate_count": j.applications.count(),
            "created_at": str(j.created_at),
        }
        for j in jobs
    ]


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    job = _check_job_access(job_id, user, db)
    return {
        "id": job.id,
        "title": job.title,
        "jd_raw": job.jd_raw,
        "job_profile": job.job_profile,
        "status": job.status,
        "created_at": str(job.created_at),
        "updated_at": str(job.updated_at),
    }


@router.put("/{job_id}")
def update_job(job_id: int, body: JobUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    job = _check_job_access(job_id, user, db)
    if body.title is not None:
        job.title = body.title
    if body.jd_raw is not None:
        job.jd_raw = body.jd_raw
    if body.job_profile is not None:
        job.job_profile = body.job_profile
    db.commit()
    db.refresh(job)
    return {"id": job.id, "title": job.title, "job_profile": job.job_profile}


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    job = _check_job_access(job_id, user, db)

    from models.application import Application
    from models.ai_analysis import AIAnalysis

    for app in job.applications.all():
        db.query(AIAnalysis).filter(AIAnalysis.application_id == app.id).delete()
        db.delete(app)

    db.delete(job)
    db.commit()
    return {"ok": True}


@router.post("/{job_id}/reanalyze")
def reanalyze(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    job = _check_job_access(job_id, user, db)
    job = reanalyze_job(db, job)
    return {"id": job.id, "job_profile": job.job_profile}
