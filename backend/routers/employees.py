import uuid
import os
import mimetypes
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.employee import Employee
from models.application import Application
from models.user import User
from auth import require_user
from services.multi_tenant import get_company_job_ids

router = APIRouter(prefix="/api/employees", tags=["employees"])

ALLOWED_DOC_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_DOC_SIZE = 10 * 1024 * 1024  # 10MB


def _check_employee_access(employee_id: int, user: User, db: Session) -> Employee:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp.job_id:
        from models.job import Job
        job = db.query(Job).filter(Job.id == emp.job_id).first()
        if not job or job.company_id != user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
    # If no job_id (manual employee), allow — require_user already ensures login
    return emp


def _safe_file_response(file_path: str) -> FileResponse:
    """Serve a file after validating it's within the storage directory."""
    if not file_path or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    real = os.path.realpath(file_path)
    storage_root = os.path.realpath("storage")
    if not real.startswith(storage_root + os.sep) and real != storage_root:
        raise HTTPException(status_code=403, detail="Access denied")
    mime_type, _ = mimetypes.guess_type(real)
    return FileResponse(real, media_type=mime_type or "application/octet-stream", filename=os.path.basename(real))


class OnboardRequest(BaseModel):
    application_id: int
    department: str = ""
    position: str = ""
    reports_to: str = ""
    salary: str = ""
    hire_date: str = ""
    probation_months: int = 3
    id_number: str = ""
    contract_type: str = "fulltime"
    contract_end_date: str = ""
    social_insurance: str = "pending"
    social_insurance_account: str = ""
    housing_fund: str = "pending"
    housing_fund_account: str = ""
    bank_name: str = ""
    bank_account: str = ""
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    emergency_contact_relation: str = ""
    notes: str = ""


@router.post("")
def onboard_employee(body: OnboardRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Create an employee record from a hired application."""
    app = db.query(Application).filter(Application.id == body.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.job and app.job.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    candidate = app.candidate
    job = app.job
    profile = candidate.profile or {}

    hire_date = datetime.strptime(body.hire_date, "%Y-%m-%d").date() if body.hire_date else date.today()
    probation_end = hire_date + timedelta(days=body.probation_months * 30)
    contract_end = datetime.strptime(body.contract_end_date, "%Y-%m-%d").date() if body.contract_end_date else None

    onboard_token = uuid.uuid4().hex
    token_created = datetime.utcnow()
    token_expires = token_created + timedelta(days=7)

    employee = Employee(
        candidate_id=candidate.id,
        job_id=app.job_id,
        application_id=app.id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        id_number=body.id_number,
        department=body.department or job.title,
        position=body.position or job.title,
        reports_to=body.reports_to,
        salary=body.salary,
        hire_date=hire_date,
        probation_months=body.probation_months,
        probation_end_date=probation_end,
        contract_type=body.contract_type,
        contract_end_date=contract_end,
        social_insurance=body.social_insurance,
        social_insurance_account=body.social_insurance_account,
        housing_fund=body.housing_fund,
        housing_fund_account=body.housing_fund_account,
        bank_name=body.bank_name,
        bank_account=body.bank_account,
        emergency_contact_name=body.emergency_contact_name,
        emergency_contact_phone=body.emergency_contact_phone,
        emergency_contact_relation=body.emergency_contact_relation,
        onboard_token=onboard_token,
        onboard_token_created_at=token_created,
        onboard_token_expires_at=token_expires,
        onboard_completed="N",
        notes=body.notes,
        status="probation",
    )
    db.add(employee)
    app.status = "hired"

    from sqlalchemy.orm.attributes import flag_modified
    if candidate.profile is None:
        candidate.profile = {}
    candidate.profile["talent_type"] = "hired"
    flag_modified(candidate, "profile")

    db.commit()
    db.refresh(employee)

    try:
        from services.notify_service import notify_new_employee
        onboard_link = f"http://localhost:3000/onboarding/{onboard_token}"
        notify_new_employee(employee.name, employee.position, employee.department, onboard_link)
    except Exception:
        pass

    result = _employee_dict(employee)
    result["onboard_token"] = onboard_token
    result["onboard_link"] = onboard_link
    return result


# ── Token endpoints (public — employee self-service) ──

@router.get("/token/{token}")
def get_by_token(token: str, db: Session = Depends(get_db)):
    """Employee self-service: view onboarding info by token."""
    emp = db.query(Employee).filter(Employee.onboard_token == token).first()
    if not emp:
        raise HTTPException(status_code=404, detail="无效链接")
    if emp.onboard_token_status == "expired":
        raise HTTPException(status_code=410, detail="链接已过期，请联系HR重新发送")
    if emp.onboard_token_status == "used":
        return _employee_dict(emp)
    return _employee_dict(emp)


class EmployeeSelfServiceUpdate(BaseModel):
    phone: str = ""
    email: str = ""
    id_number: str = ""
    education_degree: str = ""
    education_school: str = ""
    education_major: str = ""
    education_graduation_year: int = 0
    bank_name: str = ""
    bank_account: str = ""
    social_insurance_account: str = ""
    housing_fund_account: str = ""
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    emergency_contact_relation: str = ""
    onboard_completed: bool = False


@router.put("/token/{token}")
def update_by_token(token: str, body: EmployeeSelfServiceUpdate, db: Session = Depends(get_db)):
    """Employee self-service: fill in personal info."""
    emp = db.query(Employee).filter(Employee.onboard_token == token).first()
    if not emp:
        raise HTTPException(status_code=404, detail="无效链接")
    if emp.onboard_token_status == "expired":
        raise HTTPException(status_code=410, detail="链接已过期，请联系HR重新发送")

    data = body.model_dump()
    for key, val in data.items():
        if key == "onboard_completed":
            if val:
                emp.onboard_completed = "Y"
            continue
        if val:
            setattr(emp, key, val)

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(emp, "onboard_completed")

    db.commit()
    return {"ok": True}


@router.post("/token/{token}/upload")
async def upload_document(token: str, file: UploadFile = File(...), doc_type: str = Form(""), db: Session = Depends(get_db)):
    """Employee self-service: upload degree certificate or ID card."""
    emp = db.query(Employee).filter(Employee.onboard_token == token).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Invalid token")
    if emp.onboard_token_status == "expired":
        raise HTTPException(status_code=410, detail="链接已过期，请联系HR重新发送")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"仅支持 {', '.join(ALLOWED_DOC_EXTENSIONS)} 格式")

    content = await file.read()
    if len(content) > MAX_DOC_SIZE:
        raise HTTPException(status_code=400, detail=f"文件不能超过 {MAX_DOC_SIZE // 1024 // 1024}MB")

    upload_dir = os.path.join("storage", "employee_docs", str(emp.id))
    os.makedirs(upload_dir, exist_ok=True)

    saved_name = f"{doc_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{ext}"
    saved_path = os.path.join(upload_dir, saved_name)

    with open(saved_path, "wb") as f:
        f.write(content)

    if doc_type == "diploma":
        emp.diploma_file = saved_path
    elif doc_type == "id_card":
        emp.id_card_file = saved_path

    db.commit()
    return {"ok": True, "file_path": saved_path}


@router.get("/token/{token}/file")
def preview_token_file(token: str, type: str = Query(..., description="diploma or id_card"), db: Session = Depends(get_db)):
    """Serve uploaded documents via onboarding token (for self-service preview)."""
    emp = db.query(Employee).filter(Employee.onboard_token == token).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Invalid token")

    file_path = emp.diploma_file if type == "diploma" else (emp.id_card_file if type == "id_card" else None)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    return _safe_file_response(file_path)


# ── HR endpoints (require login) ──

class ManualCreateRequest(BaseModel):
    name: str
    position: str
    department: str = ""
    salary: str = ""
    hire_date: str = ""
    probation_months: int = 3
    phone: str = ""
    email: str = ""
    id_number: str = ""
    social_insurance: str = "pending"
    social_insurance_account: str = ""
    housing_fund: str = "pending"
    housing_fund_account: str = ""
    bank_name: str = ""
    bank_account: str = ""
    education_degree: str = ""
    education_school: str = ""
    education_major: str = ""
    education_graduation_year: int = 0
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    emergency_contact_relation: str = ""
    contract_type: str = "fulltime"


@router.post("/manual")
def manual_create_employee(body: ManualCreateRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Manually add an existing employee (predating the system)."""
    hire_date = datetime.strptime(body.hire_date, "%Y-%m-%d").date() if body.hire_date else date.today()
    probation_end = hire_date + timedelta(days=body.probation_months * 30)

    emp = Employee(
        name=body.name,
        position=body.position,
        department=body.department,
        salary=body.salary,
        hire_date=hire_date,
        probation_months=body.probation_months,
        probation_end_date=probation_end,
        phone=body.phone,
        email=body.email,
        id_number=body.id_number,
        social_insurance=body.social_insurance,
        social_insurance_account=body.social_insurance_account,
        housing_fund=body.housing_fund,
        housing_fund_account=body.housing_fund_account,
        bank_name=body.bank_name,
        bank_account=body.bank_account,
        education_degree=body.education_degree,
        education_school=body.education_school,
        education_major=body.education_major,
        education_graduation_year=body.education_graduation_year,
        emergency_contact_name=body.emergency_contact_name,
        emergency_contact_phone=body.emergency_contact_phone,
        emergency_contact_relation=body.emergency_contact_relation,
        contract_type=body.contract_type,
        onboard_completed="Y",
        status="probation" if probation_end > date.today() else "regular",
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {"id": emp.id, "name": emp.name, "status": emp.status, "probation_end_date": str(emp.probation_end_date)}


@router.get("")
def list_employees(
    status: str = "",
    alert: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    company_job_ids = get_company_job_ids(db, user)
    query = db.query(Employee).order_by(Employee.hire_date.desc())
    if status:
        query = query.filter(Employee.status == status)

    employees = query.limit(200).all()
    # Filter to company's jobs (or manual employees without job_id)
    employees = [e for e in employees if e.job_id is None or e.job_id in company_job_ids]

    if alert == "pending":
        employees = [e for e in employees if e.probation_alert in ("urgent", "overdue")]
    elif alert == "upcoming":
        employees = [e for e in employees if e.probation_alert == "upcoming"]

    return [_employee_dict(e) for e in employees]


@router.get("/stats")
def employee_stats(db: Session = Depends(get_db), user: User = Depends(require_user)):
    company_job_ids = get_company_job_ids(db, user)
    all_employees = db.query(Employee).all()
    all_employees = [e for e in all_employees if e.job_id is None or e.job_id in company_job_ids]

    total = len(all_employees)
    probation = sum(1 for e in all_employees if e.status == "probation")
    regular = sum(1 for e in all_employees if e.status == "regular")
    urgent = sum(1 for e in all_employees if e.probation_alert in ("urgent", "overdue"))
    upcoming = sum(1 for e in all_employees if e.probation_alert == "upcoming")
    contract_urgent = sum(1 for e in all_employees if e.contract_alert == "urgent")
    si_pending = sum(1 for e in all_employees if e.social_insurance == "pending")
    hf_pending = sum(1 for e in all_employees if e.housing_fund == "pending")

    return {
        "total": total, "probation": probation, "regular": regular,
        "urgent_alerts": urgent, "upcoming_alerts": upcoming,
        "contract_urgent": contract_urgent,
        "si_pending": si_pending, "hf_pending": hf_pending,
    }


@router.get("/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    emp = _check_employee_access(employee_id, user, db)
    return _employee_dict(emp)


@router.put("/{employee_id}")
def update_employee(employee_id: int, body: dict, db: Session = Depends(get_db), user: User = Depends(require_user)):
    emp = _check_employee_access(employee_id, user, db)

    allowed = [
        "department", "position", "reports_to", "salary", "status", "notes",
        "id_number", "social_insurance", "social_insurance_account",
        "housing_fund", "housing_fund_account", "bank_name", "bank_account",
        "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation",
        "contract_type",
    ]
    for key in allowed:
        if key in body:
            setattr(emp, key, body[key])

    if "contract_end_date" in body and body["contract_end_date"]:
        emp.contract_end_date = datetime.strptime(body["contract_end_date"], "%Y-%m-%d").date()

    db.commit()
    return {"ok": True}


@router.get("/{employee_id}/file")
def preview_employee_file(employee_id: int, type: str = Query(..., description="diploma or id_card"), db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Serve uploaded employee documents for preview (HR only)."""
    emp = _check_employee_access(employee_id, user, db)

    file_path = emp.diploma_file if type == "diploma" else (emp.id_card_file if type == "id_card" else None)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    return _safe_file_response(file_path)


# ── Probation Management (require login) ──

class ManagerEvaluation(BaseModel):
    notes: str
    scores: Optional[dict] = None


@router.get("/{employee_id}/probation")
def get_probation_status(employee_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    emp = _check_employee_access(employee_id, user, db)

    from services.probation_service import _get_days_employed, _get_current_milestone, MILESTONES

    days = _get_days_employed(emp.hire_date)
    current = _get_current_milestone(days, emp.probation_months)
    completed = {e.get("stage", "") for e in (emp.probation_evaluations or [])}

    milestones_config = []
    for d, label in MILESTONES:
        reached = days >= d
        evaluated = label in completed
        milestones_config.append({
            "day": d,
            "label": label,
            "reached": reached,
            "evaluated": evaluated,
            "is_current": current and current[1] == label,
        })

    return {
        "employee_name": emp.name,
        "hire_date": str(emp.hire_date),
        "days_employed": days,
        "probation_months": emp.probation_months,
        "probation_end_date": str(emp.probation_end_date) if emp.probation_end_date else "",
        "status": emp.status,
        "current_milestone": current[1] if current else None,
        "milestones": milestones_config,
        "evaluations": emp.probation_evaluations or [],
    }


@router.post("/{employee_id}/probation/evaluate")
def generate_probation_evaluation(employee_id: int, manager_notes: str = "", db: Session = Depends(get_db), user: User = Depends(require_user)):
    emp = _check_employee_access(employee_id, user, db)

    from services.probation_service import generate_evaluation, _get_days_employed

    days = _get_days_employed(emp.hire_date)

    employee_data = {
        "name": emp.name,
        "position": emp.position,
        "department": emp.department,
        "hire_date": str(emp.hire_date),
        "probation_months": emp.probation_months,
        "education_degree": emp.education_degree,
        "education_school": emp.education_school,
        "education_major": emp.education_major,
        "phone": emp.phone,
        "email": emp.email,
        "id_number": emp.id_number,
        "bank_name": emp.bank_name,
        "bank_account": emp.bank_account,
        "emergency_contact_name": emp.emergency_contact_name,
        "emergency_contact_phone": emp.emergency_contact_phone,
    }

    try:
        evaluation = generate_evaluation(employee_data, manager_notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    evals = list(emp.probation_evaluations or [])
    evals.append(evaluation)
    emp.probation_evaluations = evals
    db.commit()

    try:
        from services.notify_service import send
        avg_score = sum(evaluation["scores"].values()) / 4
        level = "urgent" if avg_score < 2.5 else ("warning" if avg_score < 3.5 else "info")
        content = (
            f"**{emp.name}** · {emp.position}\n"
            f"评估节点: {evaluation['stage']}\n"
            f"综合评分: {avg_score:.1f}/5.0\n"
            f"优势: {evaluation['strengths']}\n"
            f"建议: {evaluation['recommendation']}"
        )
        send(f"试用期评估 · {emp.name}", content, level)
    except Exception:
        pass

    return {"evaluation": evaluation, "days_employed": days}


@router.post("/{employee_id}/probation/evaluate/manual")
def add_manager_evaluation(employee_id: int, body: ManagerEvaluation, db: Session = Depends(get_db), user: User = Depends(require_user)):
    emp = _check_employee_access(employee_id, user, db)

    from services.probation_service import add_manager_evaluation, _get_days_employed

    employee_data = {
        "name": emp.name,
        "hire_date": str(emp.hire_date),
        "probation_months": emp.probation_months,
    }

    evaluation = add_manager_evaluation(employee_data, body.notes, body.scores)
    evals = list(emp.probation_evaluations or [])
    evals.append(evaluation)
    emp.probation_evaluations = evals
    db.commit()

    return {"evaluation": evaluation}


@router.get("/{employee_id}/feedback-loop")
def get_feedback_loop(employee_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    emp = _check_employee_access(employee_id, user, db)

    from models.ai_analysis import AIAnalysis
    from services.feedback_loop import generate_feedback_report

    match_report = None
    interview_fb = None
    if emp.application_id:
        analysis = (
            db.query(AIAnalysis)
            .filter(AIAnalysis.application_id == emp.application_id)
            .order_by(AIAnalysis.created_at.desc())
            .first()
        )
        if analysis:
            match_report = analysis.match_report

    if emp.application_id:
        app = db.query(Application).filter(Application.id == emp.application_id).first()
        if app:
            interview_fb = app.interview_feedback

    report = generate_feedback_report(
        match_report=match_report,
        interview_feedback=interview_fb,
        probation_evaluations=emp.probation_evaluations or [],
        employee_name=emp.name,
        position=emp.position,
    )

    return {
        "employee_id": emp.id,
        "employee_name": emp.name,
        "position": emp.position,
        "hire_date": str(emp.hire_date),
        "status": emp.status,
        "feedback": report,
    }


@router.get("/{employee_id}/profile-report")
def get_employee_profile_report(employee_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    emp = _check_employee_access(employee_id, user, db)

    from models.ai_analysis import AIAnalysis
    from models.application import Application
    from models.candidate import Candidate
    from services.employee_profile import generate_employee_profile

    candidate_profile = None
    match_report = None
    interview_fb = None

    if emp.candidate_id:
        cand = db.query(Candidate).filter(Candidate.id == emp.candidate_id).first()
        if cand:
            candidate_profile = cand.profile

    if emp.application_id:
        analysis = (
            db.query(AIAnalysis)
            .filter(AIAnalysis.application_id == emp.application_id)
            .order_by(AIAnalysis.created_at.desc()).first()
        )
        if analysis:
            match_report = analysis.match_report

        app = db.query(Application).filter(Application.id == emp.application_id).first()
        if app:
            interview_fb = app.interview_feedback

    education = {}
    if emp.education_degree:
        education = {
            "degree": emp.education_degree,
            "school": emp.education_school or "",
            "major": emp.education_major or "",
            "year": emp.education_graduation_year or 0,
        }

    employee_data = {
        "name": emp.name,
        "position": emp.position,
        "department": emp.department,
        "candidate_profile": candidate_profile,
        "match_report": match_report,
        "interview_feedback": interview_fb,
        "probation_evaluations": emp.probation_evaluations or [],
        "education": education,
    }

    profile = generate_employee_profile(employee_data)

    return {
        "employee_id": emp.id,
        "employee_name": emp.name,
        "position": emp.position,
        "status": emp.status,
        "profile": profile,
    }


@router.post("/{employee_id}/regenerate-onboard-token")
def regenerate_onboard_token(employee_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """HR regenerates the onboarding token/link for an employee."""
    emp = _check_employee_access(employee_id, user, db)
    if emp.onboard_completed == "Y":
        raise HTTPException(status_code=400, detail="员工已完成入职登记，无需重新生成链接")

    emp.onboard_token = uuid.uuid4().hex
    emp.onboard_token_created_at = datetime.utcnow()
    emp.onboard_token_expires_at = datetime.utcnow() + timedelta(days=7)
    db.commit()
    db.refresh(emp)

    onboard_link = f"http://localhost:3000/onboarding/{emp.onboard_token}"
    return {"ok": True, "onboard_token": emp.onboard_token, "onboard_link": onboard_link}


def _employee_dict(e: Employee) -> dict:
    return {
        "id": e.id, "name": e.name, "position": e.position,
        "department": e.department, "reports_to": e.reports_to,
        "email": e.email, "phone": e.phone, "id_number": e.id_number or "",
        "salary": e.salary,
        "hire_date": str(e.hire_date),
        "probation_end_date": str(e.probation_end_date) if e.probation_end_date else "",
        "contract_type": e.contract_type,
        "contract_end_date": str(e.contract_end_date) if e.contract_end_date else "",
        "social_insurance": e.social_insurance,
        "social_insurance_account": e.social_insurance_account or "",
        "housing_fund": e.housing_fund,
        "housing_fund_account": e.housing_fund_account or "",
        "education_degree": e.education_degree or "",
        "education_school": e.education_school or "",
        "education_major": e.education_major or "",
        "education_graduation_year": e.education_graduation_year or 0,
        "diploma_file": e.diploma_file or "",
        "id_card_file": e.id_card_file or "",
        "bank_name": e.bank_name or "", "bank_account": e.bank_account or "",
        "emergency_contact_name": e.emergency_contact_name or "",
        "emergency_contact_phone": e.emergency_contact_phone or "",
        "emergency_contact_relation": e.emergency_contact_relation or "",
        "status": e.status, "notes": e.notes or "",
        "probation_evaluations": e.probation_evaluations or [],
        "probation_months": e.probation_months,
        "onboard_completed": e.onboard_completed,
        "onboard_token": e.onboard_token or "",
        "onboard_token_created_at": str(e.onboard_token_created_at) if e.onboard_token_created_at else "",
        "onboard_token_expires_at": str(e.onboard_token_expires_at) if e.onboard_token_expires_at else "",
        "onboard_token_status": e.onboard_token_status,
        "days_until_probation_end": e.days_until_probation_end,
        "probation_alert": e.probation_alert,
        "contract_alert": e.contract_alert,
        "created_at": str(e.created_at),
    }
