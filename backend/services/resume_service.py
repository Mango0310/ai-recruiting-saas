import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import fitz  # PyMuPDF
from ai_service.analyzers.resume_parser import parse_resume
from config import STORAGE_DIR
from models.candidate import Candidate
from models.resume import Resume
from models.application import Application
from models.job import Job

# Role classification via keyword matching on job title (fallback when job_profile has no role_category)
ROLE_KEYWORDS = {
    "tech": [
        "后端", "前端", "Backend", "Frontend", "全栈", "Full Stack",
        "Java", "Python", "Go", "Rust", "Node", "C++", "C#",
        "架构师", "Architect", "运维", "DevOps", "SRE", "DBA",
        "移动端", "Android", "iOS", "React Native", "Flutter",
        "嵌入式", "Embedded", "数据工程", "Data Engineer", "ETL",
        "测试", "QA", "Test", "安全", "Security", "网络", "Network",
        "算法", "Algorithm", "机器学习", "Machine Learning", "AI",
        "区块链", "Blockchain", "游戏开发", "Game Dev", "硬件",
    ],
    "design": [
        "UI", "UX", "设计", "Design", "视觉", "Visual",
        "品牌", "Brand", "创意", "Creative", "3D", "三维",
        "插画", "Illustration", "动效", "Motion", "动画",
        "交互", "Interaction", "体验", "Experience",
    ],
}


def classify_role_from_title(title: str) -> str:
    """Infer role category from job title using keyword matching."""
    for role, keywords in ROLE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in title.lower():
                return role
    return "generic"


def get_role_category(job) -> str:
    """Extract role_category from job, with fallback to title classification."""
    if job and job.job_profile and isinstance(job.job_profile, dict):
        rc = job.job_profile.get("role_category")
        if rc in ("tech", "design", "generic"):
            return rc
    if job and job.title:
        return classify_role_from_title(job.title)
    return "generic"


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def process_resume(db, job_id: int, file_content: bytes, original_filename: str) -> dict:
    # Save file
    file_id = uuid.uuid4().hex[:12]
    safe_filename = f"{file_id}_{original_filename}"
    job_dir = STORAGE_DIR / "resumes" / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    file_path = job_dir / safe_filename
    file_path.write_bytes(file_content)

    # Create resume record
    resume = Resume(file_name=original_filename, file_path=str(file_path), parse_status="parsing")
    db.add(resume)
    db.flush()

    try:
        # Extract text
        raw_text = extract_text_from_pdf(str(file_path))
        resume.raw_text = raw_text

        if not raw_text:
            resume.parse_status = "failed"
            resume.parse_error = "PDF无法提取文字（可能是扫描件或图片型PDF）"
            db.commit()
            db.refresh(resume)
            return {"resume_id": resume.id, "status": "failed", "error": resume.parse_error}

        # Parse with LLM (role-aware)
        job = db.query(Job).filter(Job.id == job_id).first()
        role_category = get_role_category(job)
        profile = parse_resume(raw_text, role_category=role_category)

        # Post-parse enrichment: fetch GitHub signals for tech roles
        if role_category == "tech":
            github_username = profile.get("github_username")
            if not github_username and profile.get("tech_stack_depth"):
                github_username = profile["tech_stack_depth"].get("github_username")
            if github_username:
                try:
                    from ai_service.integrations.github import fetch_github_profile
                    github_data = fetch_github_profile(github_username)
                    if github_data:
                        profile["github_profile"] = github_data
                except Exception:
                    pass  # Non-blocking: resume parsing succeeds even if GitHub API fails

        # Create or update candidate
        candidate = Candidate(name=profile.get("name", ""), email=profile.get("email"), phone=profile.get("phone"), profile=profile)

        # Generate embedding for semantic search
        try:
            from ai_service.embeddings import generate_candidate_embedding, mock_embedding
            search_text = f"{profile.get('current_position','')} {profile.get('current_company','')} {' '.join(profile.get('skills',[]))}"
            emb = generate_candidate_embedding(profile)
            if emb is None:
                emb = mock_embedding(search_text)
            candidate.embedding = emb
        except Exception:
            pass  # Non-blocking: candidate creation succeeds even if embedding fails

        db.add(candidate)
        db.flush()

        resume.candidate_id = candidate.id
        resume.parse_status = "completed"
    except Exception as e:
        resume.parse_status = "failed"
        resume.parse_error = str(e)
        db.commit()
        db.refresh(resume)
        return {"resume_id": resume.id, "status": "failed", "error": str(e)}

    # Create application
    application = Application(job_id=job_id, candidate_id=candidate.id, resume_id=resume.id, status="parsed")
    db.add(application)
    db.commit()  # Commit first so relationships work
    db.refresh(application)

    # Auto-generate match report
    from services.match_service import generate_match_report
    try:
        generate_match_report(db, application.id)
        application.status = "ai_screened"
        db.commit()
        db.refresh(application)
    except Exception as e:
        application.status = "parsed"  # Parsed but match failed
        db.commit()
        import traceback
        print(f"Match failed for app {application.id}: {e}")
        traceback.print_exc()
        # Match failed, but resume is still parsed

    # Notify via webhook
    try:
        from services.notify_service import notify_new_candidate
        conclusion = ""
        if application.status == "ai_screened":
            from models.ai_analysis import AIAnalysis
            analysis = db.query(AIAnalysis).filter(AIAnalysis.application_id == application.id).first()
            if analysis and analysis.match_report:
                conclusion = analysis.match_report.get("overall_conclusion", "")
        notify_new_candidate(candidate.name, job.title if job else "", conclusion)
    except Exception:
        pass

    return {
        "resume_id": resume.id,
        "candidate_id": candidate.id,
        "application_id": application.id,
        "status": "completed",
        "candidate_name": candidate.name,
    }
