from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.job import Job
from models.candidate import Candidate
from models.application import Application
from models.employee import Employee
from models.user import User
from auth import require_user
from models.ai_analysis import AIAnalysis
from services.multi_tenant import get_company_job_ids, filtered_job_query

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/funnel")
def get_funnel(db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Recruitment funnel with conversion rates, per-job breakdown, time-to-hire."""
    job_ids = get_company_job_ids(db, user)
    all_apps = db.query(Application).order_by(Application.created_at.desc()).all()
    all_apps = [a for a in all_apps if a.job_id in job_ids]

    stages_order = ["new", "parsed", "ai_screened", "hr_reviewed", "interviewing", "interviewed", "hired"]
    stage_labels = {"new":"简历入库","parsed":"已解析","ai_screened":"AI筛选","hr_reviewed":"HR筛选","interviewing":"面试中","interviewed":"面试完成","hired":"已入职"}

    total_candidates = len(all_apps)
    stage_counts = {s: sum(1 for a in all_apps if a.status == s) for s in stages_order}

    reached = {}
    cumulative = total_candidates
    for s in stages_order:
        reached[s] = cumulative
        cumulative -= stage_counts.get(s, 0)

    funnel = []
    prev = None
    for s in stages_order:
        count = stage_counts.get(s, 0)
        funnel.append({
            "stage": s,
            "label": stage_labels[s],
            "count": count,
            "reached": reached[s],
            "rate": round(count / total_candidates * 100, 1) if total_candidates > 0 else 0,
            "conversion": round(count / prev * 100, 1) if prev and prev > 0 else None,
        })
        prev = count if count > 0 else prev

    dropoffs = []
    for i in range(len(funnel) - 1):
        curr = funnel[i]
        nxt = funnel[i + 1]
        lost = curr["count"] - nxt["count"]
        if lost > 0:
            dropoffs.append({
                "from": curr["label"],
                "to": nxt["label"],
                "lost": lost,
                "loss_rate": round(lost / curr["count"] * 100, 1) if curr["count"] > 0 else 0,
            })

    jobs = db.query(Job).filter(Job.company_id == user.company_id, Job.status == "active").order_by(Job.created_at.desc()).limit(10).all()
    jobs_funnel = []
    for j in jobs:
        apps = [a for a in all_apps if a.job_id == j.id]
        jc = len(apps)
        hired = sum(1 for a in apps if a.status == "hired")
        interviewing = sum(1 for a in apps if a.status in ("interviewing", "interviewed"))
        passed_screening = sum(1 for a in apps if a.status in ("ai_screened", "hr_reviewed", "interviewing", "interviewed"))
        jobs_funnel.append({
            "id": j.id,
            "title": j.title,
            "total": jc,
            "screening": passed_screening,
            "interviewing": interviewing,
            "hired": hired,
            "screening_rate": round(passed_screening / jc * 100, 1) if jc > 0 else 0,
            "interview_rate": round(interviewing / jc * 100, 1) if jc > 0 else 0,
            "hire_rate": round(hired / jc * 100, 1) if jc > 0 else 0,
            "created_at": str(j.created_at),
        })

    hired_apps = [a for a in all_apps if a.status == "hired"]
    tth_days = []
    for a in hired_apps:
        delta = (a.updated_at.date() - a.created_at.date()).days if a.updated_at and a.created_at else 0
        if delta > 0:
            tth_days.append(delta)
    avg_tth = round(sum(tth_days) / len(tth_days), 1) if tth_days else None

    stage_dwell = {}
    for s in stages_order:
        in_stage = [a for a in all_apps if a.status == s]
        if in_stage:
            dwells = [(date.today() - a.created_at.date()).days for a in in_stage]
            stage_dwell[s] = {
                "label": stage_labels[s],
                "count": len(in_stage),
                "avg_days": round(sum(dwells) / len(dwells), 1),
                "max_days": max(dwells),
            }

    return {
        "total_candidates": total_candidates,
        "funnel": funnel,
        "dropoffs": dropoffs,
        "jobs_funnel": jobs_funnel,
        "avg_time_to_hire_days": avg_tth,
        "stage_dwell": stage_dwell,
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), user: User = Depends(require_user)):
    job_ids = get_company_job_ids(db, user)

    job_count = db.query(Job).filter(Job.company_id == user.company_id, Job.status == "active").count()

    all_apps = db.query(Application).all()
    all_apps = [a for a in all_apps if a.job_id in job_ids]

    candidate_ids_in_scope = {a.candidate_id for a in all_apps}
    candidate_count = len(candidate_ids_in_scope)

    pending_count = sum(1 for a in all_apps if a.hr_decision == "pending")
    interviewing_count = sum(1 for a in all_apps if a.status == "interviewing")

    all_employees = db.query(Employee).filter(Employee.status == "probation").all()
    all_employees = [e for e in all_employees if e.job_id is None or e.job_id in job_ids]
    total_employees = len(all_employees)
    probation_count = total_employees
    urgent_count = sum(1 for e in all_employees if e.probation_alert in ("urgent", "overdue"))

    talent_pool_count = sum(1 for a in all_apps if a.status in ("ai_screened", "hr_reviewed", "talent_pool"))

    pipeline_stages = {
        "new": sum(1 for a in all_apps if a.status == "new"),
        "parsed": sum(1 for a in all_apps if a.status == "parsed"),
        "ai_screened": sum(1 for a in all_apps if a.status == "ai_screened"),
        "hr_reviewed": sum(1 for a in all_apps if a.status == "hr_reviewed"),
        "interviewing": sum(1 for a in all_apps if a.status == "interviewing"),
        "interviewed": sum(1 for a in all_apps if a.status == "interviewed"),
        "hired": sum(1 for a in all_apps if a.status == "hired"),
    }

    recent_jobs = db.query(Job).filter(Job.company_id == user.company_id).order_by(Job.created_at.desc()).limit(6).all()
    jobs_data = []
    for j in recent_jobs:
        apps = db.query(Application).filter(Application.job_id == j.id).all()
        top_star = 0
        for app in apps:
            analysis = db.query(AIAnalysis).filter(
                AIAnalysis.application_id == app.id
            ).order_by(AIAnalysis.created_at.desc()).first()
            if analysis and analysis.match_report:
                s = analysis.match_report.get("star_rating", 0)
                if s > top_star:
                    top_star = int(s)

        jobs_data.append({
            "id": j.id,
            "title": j.title,
            "candidate_count": len(apps),
            "top_star": top_star,
            "new_count": sum(1 for a in apps if a.status == "new"),
            "screening_count": sum(1 for a in apps if a.status in ("ai_screened", "hr_reviewed")),
            "interviewing_count": sum(1 for a in apps if a.status in ("interviewing", "interviewed")),
            "created_at": str(j.created_at),
        })

    recent_candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).limit(6).all()
    cands_data = []
    for c in recent_candidates:
        profile = c.profile or {}
        app = db.query(Application).filter(Application.candidate_id == c.id).order_by(Application.created_at.desc()).first()

        star_rating = None
        conclusion = ""
        job_title = ""
        if app and app.job_id in job_ids:
            job_title = app.job.title if app.job else ""
            analysis = db.query(AIAnalysis).filter(
                AIAnalysis.application_id == app.id
            ).order_by(AIAnalysis.created_at.desc()).first()
            if analysis and analysis.match_report:
                star_rating = analysis.match_report.get("star_rating")
                conclusion = analysis.match_report.get("overall_conclusion", "")

        cands_data.append({
            "id": c.id,
            "name": c.name,
            "current_position": profile.get("current_position", ""),
            "current_company": profile.get("current_company", ""),
            "skills": (profile.get("skills", []) or [])[:5],
            "star_rating": star_rating,
            "conclusion": conclusion,
            "job_title": job_title,
            "created_at": str(c.created_at),
        })

    return {
        "job_count": job_count,
        "candidate_count": candidate_count,
        "pending_count": pending_count,
        "interviewing_count": interviewing_count,
        "talent_pool_count": talent_pool_count,
        "total_employees": total_employees,
        "probation_count": probation_count,
        "urgent_alerts": urgent_count,
        "pipeline_stages": pipeline_stages,
        "recent_jobs": jobs_data,
        "recent_candidates": cands_data,
    }
