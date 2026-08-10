"""Company settings and knowledge base management."""
import uuid, os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.company import Company
from models.user import User
from auth import require_user
from config import STORAGE_DIR

router = APIRouter(prefix="/api/company", tags=["company"])


def _get_user_company(user: User, db: Session) -> Company:
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("")
def get_company(db: Session = Depends(get_db), user: User = Depends(require_user)):
    company = _get_user_company(user, db)
    return {
        "id": company.id,
        "name": company.name,
        "industry": company.industry,
        "size": company.size,
        "knowledge_docs": company.knowledge_docs or [],
        "knowledge_text": company.knowledge_text or "",
    }


class CompanyUpdate(BaseModel):
    name: str = ""
    industry: str = ""
    size: str = ""
    knowledge_text: str = ""


@router.put("")
def update_company(body: CompanyUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    company = _get_user_company(user, db)
    if body.name: company.name = body.name
    if body.industry: company.industry = body.industry
    if body.size: company.size = body.size
    if body.knowledge_text is not None:
        company.knowledge_text = body.knowledge_text
    db.commit()
    db.refresh(company)
    return {"ok": True}


@router.post("/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Upload a company document (PDF/txt/md) to the knowledge base."""
    company = _get_user_company(user, db)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".txt", ".md", ".docx"):
        raise HTTPException(status_code=400, detail="仅支持 PDF、TXT、MD、DOCX 格式")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过10MB")

    doc_dir = STORAGE_DIR / "company_docs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    doc_id = uuid.uuid4().hex[:10]
    safe_name = f"{doc_id}_{file.filename}"
    file_path = doc_dir / safe_name

    content = await file.read()
    file_path.write_bytes(content)

    snippet = ""
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                snippet += page.get_text()
                if len(snippet) > 2000:
                    break
            doc.close()
        except Exception:
            snippet = f"[PDF文件: {file.filename}]"
    elif ext in (".txt", ".md"):
        try:
            snippet = content.decode("utf-8")[:2000]
        except Exception:
            snippet = content.decode("gbk", errors="ignore")[:2000]

    record = {
        "id": doc_id,
        "name": file.filename,
        "file_path": str(file_path),
        "size": file.size or 0,
        "uploaded_at": datetime.utcnow().isoformat(),
        "snippet": snippet,
    }

    docs = list(company.knowledge_docs or [])
    docs.append(record)
    company.knowledge_docs = docs
    db.commit()

    return record


@router.delete("/knowledge/{doc_id}")
def delete_knowledge(doc_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    company = _get_user_company(user, db)

    docs = list(company.knowledge_docs or [])
    target = None
    for d in docs:
        if d.get("id") == doc_id:
            target = d
            break

    if not target:
        raise HTTPException(status_code=404, detail="Document not found")

    fp = target.get("file_path", "")
    if fp and os.path.isfile(fp):
        try: os.remove(fp)
        except: pass

    docs = [d for d in docs if d.get("id") != doc_id]
    company.knowledge_docs = docs
    db.commit()
    return {"ok": True}
