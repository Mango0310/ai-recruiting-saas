import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai_service.analyzers.matcher import match_candidate
from models.application import Application
from models.ai_analysis import AIAnalysis


def generate_match_report(db, application_id: int) -> AIAnalysis:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise ValueError(f"Application {application_id} not found")

    job = application.job
    candidate = application.candidate

    if not job.job_profile:
        raise ValueError(f"Job {job.id} has no job_profile")
    if not candidate.profile:
        raise ValueError(f"Candidate {candidate.id} has no profile")

    report = match_candidate(job.job_profile, candidate.profile)

    analysis = AIAnalysis(
        application_id=application_id,
        job_profile_snapshot=job.job_profile,
        candidate_profile_snapshot=candidate.profile,
        match_report=report,
        model_version="deepseek-chat",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis
