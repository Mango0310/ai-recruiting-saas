"""Authentication endpoints: register, login, me."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.user import User
from models.company import Company
from auth import hash_password, verify_password, create_token, get_current_user, require_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    company_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if not body.email or not body.password or not body.name:
        raise HTTPException(status_code=400, detail="邮箱、密码和姓名为必填")
    if len(body.password) < 4:
        raise HTTPException(status_code=400, detail="密码至少4位")

    # Check existing user
    existing = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    # Find or create company
    company_name = body.company_name.strip() or "未命名公司"
    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        company = Company(name=company_name)
        db.add(company)
        db.flush()

    user = User(
        email=body.email.strip().lower(),
        password_hash=hash_password(body.password),
        name=body.name.strip(),
        company_id=company.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "name": user.name, "company_id": user.company_id, "company_name": company.name},
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    token = create_token(user.id)
    company = db.query(Company).filter(Company.id == user.company_id).first()
    return {
        "token": token,
        "user": {
            "id": user.id, "email": user.email, "name": user.name,
            "company_id": user.company_id,
            "company_name": company.name if company else "",
        },
    }


@router.get("/me")
def me(user: User = Depends(require_user), db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == user.company_id).first()
    return {
        "id": user.id, "email": user.email, "name": user.name,
        "company_id": user.company_id,
        "company_name": company.name if company else "",
    }
