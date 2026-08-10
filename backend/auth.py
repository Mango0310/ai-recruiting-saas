"""JWT authentication utilities."""
import hashlib
import logging
import os
import sys
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import SessionLocal
from models.user import User

JWT_SECRET = os.getenv("JWT_SECRET", "ai-recruit-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

_is_default_secret = JWT_SECRET == "ai-recruit-dev-secret-change-me"


def check_jwt_secret_on_startup():
    """Refuse to start in production with the default JWT secret."""
    if not _is_default_secret:
        return
    env = os.getenv("ENV", "").lower()
    if env in ("production", "prod"):
        logging.critical("JWT_SECRET must be set to a real secret in production. Refusing to start.")
        sys.exit(1)
    logging.warning(
        "SECURITY: Using default JWT_SECRET. "
        "Set JWT_SECRET environment variable before deploying to production."
    )

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + dk.hex()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt_hex, dk_hex = hashed.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(dk_hex)
        actual = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 100000)
        return actual == expected
    except (ValueError, AttributeError):
        return False


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, ValueError):
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """FastAPI dependency: extract current user from Bearer token.
    Returns None if no token (backward-compatible with single-user mode).
    """
    if not credentials:
        return None
    user_id = decode_token(credentials.credentials)
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    """FastAPI dependency: require authentication. Raises 401 if not logged in."""
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user
