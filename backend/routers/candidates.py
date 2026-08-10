from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.job import Job
from models.candidate import Candidate
from models.application import Application
from models.ai_analysis import AIAnalysis
from models.user import User
from auth import get_current_user, require_user
from services.match_service import generate_match_report
from services.multi_tenant import get_company_job_ids

router = APIRouter(prefix="/api", tags=["candidates"])


def _check_job_access(job_id: int, user: User, db: Session) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return job


def _check_app_access(application_id: int, user: User, db: Session) -> Application:
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if not app.job or app.job.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return app


def _check_candidate_access(candidate_id: int, user: User, db: Session) -> Candidate:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    company_job_ids = get_company_job_ids(db, user)
    apps = db.query(Application).filter(Application.candidate_id == candidate_id).all()
    if not any(a.job_id in company_job_ids for a in apps):
        raise HTTPException(status_code=403, detail="Access denied")
    return candidate


@router.get("/jobs/{job_id}/candidates")
def list_candidates(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    _check_job_access(job_id, user, db)

    applications = db.query(Application).filter(Application.job_id == job_id).order_by(Application.created_at.desc()).all()

    result = []
    for app in applications:
        candidate = app.candidate
        latest_analysis = (
            db.query(AIAnalysis).filter(AIAnalysis.application_id == app.id).order_by(AIAnalysis.created_at.desc()).first()
        )

        report = latest_analysis.match_report if latest_analysis and latest_analysis.match_report else {}

        result.append(
            {
                "application_id": app.id,
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "current_position": candidate.profile.get("current_position", "") if candidate.profile else "",
                "years_of_experience": candidate.profile.get("years_of_experience", 0) if candidate.profile else 0,
                "skills": (candidate.profile.get("skills", []) if candidate.profile else [])[:6],
                "status": app.status,
                "hr_decision": app.hr_decision,
                "star_rating": report.get("star_rating"),
                "eval_level": report.get("eval_level", ""),
                "overall_conclusion": report.get("overall_conclusion", ""),
                "strengths": [s["point"] for s in report.get("strengths", [])[:2]],
                "gaps": [g["point"] for g in report.get("gaps", [])[:2]],
                "has_report": latest_analysis is not None,
                "created_at": str(app.created_at),
            }
        )
    return result


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    candidate = _check_candidate_access(candidate_id, user, db)

    applications = db.query(Application).filter(Application.candidate_id == candidate_id).all()

    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "profile": candidate.profile,
        "applications": [
            {
                "application_id": app.id,
                "job_id": app.job_id,
                "job_title": app.job.title if app.job else "",
                "status": app.status,
                "hr_decision": app.hr_decision,
                "hr_notes": app.hr_notes,
                "interview_feedback": app.interview_feedback,
            }
            for app in applications
            if app.job and app.job.company_id == user.company_id
        ],
        "created_at": str(candidate.created_at),
    }


class HRDecision(BaseModel):
    hr_decision: str
    hr_notes: Optional[str] = None


class InterviewFeedback(BaseModel):
    interviewer: str = ""
    ai_predictions_match: str = ""  # "match" / "partial" / "no_match"
    actual_rating: int = 0  # 1-5
    key_observations: str = ""
    notes: str = ""


@router.put("/applications/{application_id}/decision")
def update_decision(application_id: int, body: HRDecision, db: Session = Depends(get_db), user: User = Depends(require_user)):
    app = _check_app_access(application_id, user, db)
    app.hr_decision = body.hr_decision
    if body.hr_notes is not None:
        app.hr_notes = body.hr_notes
    if body.hr_decision == "suitable":
        app.status = "interviewing"
    elif body.hr_decision in ("maybe", "not_suitable"):
        app.status = "hr_reviewed"
    db.commit()
    return {"ok": True}


class StatusUpdate(BaseModel):
    status: str


@router.put("/applications/{application_id}/status")
def update_status(application_id: int, body: StatusUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    app = _check_app_access(application_id, user, db)
    valid_statuses = ["new", "parsed", "ai_screened", "hr_reviewed", "interviewing", "interviewed", "offered", "hired", "talent_pool"]
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    app.status = body.status

    from sqlalchemy.orm.attributes import flag_modified
    candidate = app.candidate
    if candidate.profile is None:
        candidate.profile = {}
    candidate.profile["talent_type"] = "hired" if body.status == "hired" else "talent_pool"
    flag_modified(candidate, "profile")

    db.commit()
    return {"ok": True, "status": app.status}


@router.put("/applications/{application_id}/feedback")
def save_feedback(application_id: int, body: InterviewFeedback, db: Session = Depends(get_db), user: User = Depends(require_user)):
    app = _check_app_access(application_id, user, db)

    analysis = db.query(AIAnalysis).filter(AIAnalysis.application_id == application_id).order_by(AIAnalysis.created_at.desc()).first()
    ai_star = analysis.match_report.get("star_rating") if analysis else None

    feedback = {
        "interviewed_at": datetime.utcnow().isoformat(),
        "interviewer": body.interviewer,
        "ai_predictions_match": body.ai_predictions_match,
        "actual_rating": body.actual_rating,
        "ai_predicted_rating": ai_star,
        "key_observations": body.key_observations,
        "notes": body.notes,
    }
    app.interview_feedback = feedback
    app.status = "interviewed"
    db.commit()
    return {"ok": True, "feedback": feedback}


@router.get("/applications/{application_id}/report")
def get_match_report(application_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    app = _check_app_access(application_id, user, db)
    analysis = db.query(AIAnalysis).filter(AIAnalysis.application_id == application_id).order_by(AIAnalysis.created_at.desc()).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found. Generate a match report first.")

    return {
        "application_id": application_id,
        "candidate_name": app.candidate.name if app.candidate else "",
        "job_title": app.job.title if app.job else "",
        "match_report": analysis.match_report,
        "job_profile_snapshot": analysis.job_profile_snapshot,
        "candidate_profile_snapshot": analysis.candidate_profile_snapshot,
        "created_at": str(analysis.created_at),
    }


@router.get("/jobs/{job_id}/compare")
def compare_candidates(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    _check_job_access(job_id, user, db)

    applications = db.query(Application).filter(Application.job_id == job_id).all()
    if not applications:
        return {"candidates": [], "dimensions": []}

    all_dims: set = set()
    candidates_data = []

    for app in applications:
        analysis = db.query(AIAnalysis).filter(AIAnalysis.application_id == app.id).order_by(AIAnalysis.created_at.desc()).first()
        candidate = app.candidate
        profile = candidate.profile or {}
        report = analysis.match_report if analysis else {}

        dims = report.get("dimension_scores", {})
        for k in dims:
            all_dims.add(k)

        candidates_data.append({
            "application_id": app.id,
            "candidate_id": candidate.id,
            "name": candidate.name,
            "current_position": profile.get("current_position", ""),
            "years_of_experience": profile.get("years_of_experience", 0),
            "star_rating": report.get("star_rating", 0),
            "overall_conclusion": report.get("overall_conclusion", ""),
            "strengths": [s["point"] for s in report.get("strengths", [])[:3]],
            "gaps": [g["point"] for g in report.get("gaps", [])[:3]],
            "dimension_scores": dims,
            "potential_level": report.get("potential_level", ""),
            "potential_signals": report.get("potential_signals", []),
            "hr_decision": app.hr_decision,
        })

    return {"candidates": candidates_data, "dimensions": sorted(all_dims)}


@router.get("/jobs/{job_id}/briefing")
def get_briefing(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    job = _check_job_access(job_id, user, db)

    applications = db.query(Application).filter(Application.job_id == job_id).order_by(Application.created_at.desc()).all()

    brief = {
        "job_title": job.title,
        "total_candidates": len(applications),
        "dimensions": list(job.job_profile.get("weight_distribution", {}).keys()) if job.job_profile else [],
        "top_picks": [],
        "all_candidates": [],
    }

    for app in applications:
        analysis = db.query(AIAnalysis).filter(AIAnalysis.application_id == app.id).order_by(AIAnalysis.created_at.desc()).first()
        candidate = app.candidate
        report = analysis.match_report if analysis else {}
        profile = candidate.profile or {}

        entry = {
            "name": candidate.name,
            "star_rating": report.get("star_rating", 0),
            "conclusion": report.get("overall_conclusion", ""),
            "key_strength": (report.get("strengths", []) or [{}])[0].get("point", ""),
            "key_gap": (report.get("gaps", []) or [{}])[0].get("point", ""),
            "interview_questions": report.get("interview_suggestions", [])[:3],
            "hr_decision": app.hr_decision,
            "candidate_id": candidate.id,
        }

        brief["all_candidates"].append(entry)

        if report.get("star_rating", 0) >= 4:
            brief["top_picks"].append(entry)

    return brief


@router.post("/applications/{application_id}/reanalyze")
def reanalyze_application(application_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    _check_app_access(application_id, user, db)
    analysis = generate_match_report(db, application_id)
    return {
        "application_id": application_id,
        "match_report": analysis.match_report,
        "created_at": str(analysis.created_at),
    }


@router.post("/applications/{application_id}/interview-questions")
def generate_interview_questions(application_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    app = _check_app_access(application_id, user, db)

    analysis = db.query(AIAnalysis).filter(
        AIAnalysis.application_id == application_id
    ).order_by(AIAnalysis.created_at.desc()).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="No match analysis found. Run match first.")

    from ai_service.interview_questions import generate_interview_questions as gen_qs

    result = gen_qs(
        candidate_profile=analysis.candidate_profile_snapshot or {},
        job_profile=analysis.job_profile_snapshot or {},
        match_report=analysis.match_report or {},
    )

    return {
        "application_id": application_id,
        "candidate_name": app.candidate.name if app.candidate else "",
        "job_title": app.job.title if app.job else "",
        "interview_questions": result,
    }


@router.get("/applications/{application_id}/resume")
def get_resume_content(application_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    app = _check_app_access(application_id, user, db)
    from models.resume import Resume

    if not app.resume_id:
        raise HTTPException(status_code=404, detail="No resume found")

    resume = db.query(Resume).filter(Resume.id == app.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "file_name": resume.file_name,
        "raw_text": resume.raw_text or "",
        "parse_status": resume.parse_status,
        "file_path": resume.file_path,
    }
