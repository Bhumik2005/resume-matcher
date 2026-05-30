"""
Authentication Routes
----------------------
POST /auth/register  — create account
POST /auth/login     — get JWT token
GET  /auth/me        — get current user profile
GET  /auth/history   — get user's analysis history
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

from db.session import get_db
from db import crud
from auth.jwt import create_access_token
from auth.dependencies import get_current_user
from db.models import User

logger = logging.getLogger(__name__)
auth_router = APIRouter()


# ── Request/Response schemas ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime


class AnalysisSummary(BaseModel):
    id: str
    match_percentage: float
    match_label: str
    matched_skills: List[str]
    missing_skills: List[str]
    seniority_level: Optional[str]
    stuffing_detected: bool
    created_at: datetime


# ── Endpoints ─────────────────────────────────────────────────────────────────

@auth_router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    existing = crud.get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = crud.create_user(
        db=db,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login and get JWT access token."""
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.id})
    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
    )


@auth_router.get("/me", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@auth_router.get("/history", response_model=List[AnalysisSummary])
async def get_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's analysis history."""
    analyses = crud.get_user_analyses(db, current_user.id, limit=limit, offset=offset)
    return [
        AnalysisSummary(
            id=a.id,
            match_percentage=a.match_percentage,
            match_label=a.match_label,
            matched_skills=a.matched_skills or [],
            missing_skills=a.missing_skills or [],
            seniority_level=a.seniority_level,
            stuffing_detected=a.stuffing_detected,
            created_at=a.created_at,
        )
        for a in analyses
    ]


@auth_router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get platform-wide statistics."""
    return crud.get_global_stats(db)