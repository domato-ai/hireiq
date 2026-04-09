"""Email/password authentication with JWT tokens — DB-backed."""
from __future__ import annotations
import hashlib
import hmac
import logging
import time
import json
import base64

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    email: str
    name: str
    plan: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _hash_password(password: str) -> str:
    """Simple password hashing."""
    settings = get_settings()
    return hashlib.pbkdf2_hmac(
        'sha256', password.encode(), settings.secret_key.encode(), 100000
    ).hex()


def _create_token(email: str) -> str:
    """Create a simple JWT-like token (base64-encoded JSON with HMAC signature)."""
    settings = get_settings()
    payload = {
        "email": email,
        "exp": int(time.time()) + 86400 * 7,  # 7 days
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(settings.secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_token(token: str) -> dict | None:
    """Verify and decode a token. Returns payload or None."""
    try:
        settings = get_settings()
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts
        expected_sig = hmac.new(settings.secret_key.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Look up a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user with email and password."""
    email = body.email.lower().strip()

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")

    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    password_hash = _hash_password(body.password)
    user = User(
        email=email,
        name=body.name or email.split("@")[0],
        password_hash=password_hash,
        plan="free",
    )
    db.add(user)
    await db.flush()

    token = _create_token(email)

    logger.info("User registered: %s", email)
    return AuthResponse(
        access_token=token,
        user=UserOut(email=user.email, name=user.name or "", plan=user.plan),
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    email = body.email.lower().strip()

    user = await get_user_by_email(db, email)
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.password_hash != _hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token(email)

    logger.info("User logged in: %s", email)
    return AuthResponse(
        access_token=token,
        user=UserOut(email=user.email, name=user.name or "", plan=user.plan),
    )


@router.get("/me", response_model=UserOut)
async def me(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get current user from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization[7:]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await get_user_by_email(db, payload["email"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return UserOut(email=user.email, name=user.name or "", plan=user.plan)
