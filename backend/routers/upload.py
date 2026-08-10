from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models.job import Job
from models.user import User
from auth import require_user
from services.resume_service import process_resume

router = APIRouter(prefix="/api/jobs", tags=["upload"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/{job_id}/resumes")
async def upload_resumes(
    job_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    results = []
    for file in files:
        if file.content_type != "application/pdf":
            results.append({"filename": file.filename, "status": "failed", "error": "仅支持PDF文件"})
            continue

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            results.append({"filename": file.filename, "status": "failed", "error": f"文件超过{MAX_FILE_SIZE // 1024 // 1024}MB限制"})
            continue

        try:
            result = process_resume(db, job_id, content, file.filename)
            results.append({"filename": file.filename, **result})
        except Exception as e:
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})

    return {"results": results, "total": len(results), "succeeded": sum(1 for r in results if r.get("status") == "completed")}
