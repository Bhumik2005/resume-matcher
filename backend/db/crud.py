"""
CRUD Operations
----------------
All database read/write operations.
Never store raw resume text — only scores and metadata.
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from db.models import User, Analysis
from auth.hashing import hash_password, verify_password

logger = logging.getLogger(__name__)


# ── User Operations ───────────────────────────────────────────────────────────

def create_user(db: Session, email: str, password: str, full_name: str = None) -> User:
    """Create a new user with hashed password."""
    user = User(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created user: {email}")
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Verify email and password. Returns user if valid, None if not."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ── Analysis Operations ───────────────────────────────────────────────────────

def save_analysis(
    db: Session,
    analysis_id: str,
    result: Dict[str, Any],
    security: Dict[str, Any],
    user_id: Optional[str] = None,
    resume_text: str = "",
) -> Analysis:
    """
    Save analysis to PostgreSQL.
    NEVER stores raw resume text — only scores and metadata.
    """
    explanation = result.get("explanation", {})
    seniority = explanation.get("seniority", {}) if explanation else {}

    analysis = Analysis(
        id=analysis_id,
        user_id=user_id,
        overall_score=result["overall_score"],
        match_percentage=result["match_percentage"],
        match_label=result["match_label"],
        tfidf_score=result["score_breakdown"]["tfidf"]["score"],
        sbert_score=result["score_breakdown"]["sbert"]["score"],
        skill_score=result["score_breakdown"]["skill"]["score"],
        matched_skills=result["skill_analysis"]["matched_skills"],
        missing_skills=result["skill_analysis"]["missing_skills"],
        extra_skills=result["skill_analysis"]["extra_skills"],
        jd_skills=result["skill_analysis"]["jd_skills"],
        stuffing_detected=security.get("stuffing_detected", False),
        text_confidence=security.get("text_confidence", "unknown"),
        injection_detected=security.get("injection_detected", False),
        pii_types_found=security.get("pii_types_found", []),
        seniority_level=seniority.get("level"),
        recruiter_verdict=explanation.get("recruiter_verdict") if explanation else None,
        suggestions=result.get("suggestions", []),
        word_count=security.get("word_count"),
        resume_snippet=resume_text[:300] if resume_text else None,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    logger.info(f"Saved analysis: {analysis_id}")
    return analysis


def get_user_analyses(
    db: Session,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
) -> List[Analysis]:
    """Get all analyses for a user, newest first."""
    return (
        db.query(Analysis)
        .filter(Analysis.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def get_analysis_by_id(
    db: Session,
    analysis_id: str,
    user_id: Optional[str] = None,
) -> Optional[Analysis]:
    """Get analysis by ID. If user_id provided, ensures ownership."""
    query = db.query(Analysis).filter(Analysis.id == analysis_id)
    if user_id:
        query = query.filter(Analysis.user_id == user_id)
    return query.first()


def get_global_stats(db: Session) -> Dict:
    """Get platform-wide statistics."""
    total_analyses = db.query(Analysis).count()
    total_users = db.query(User).count()
    avg_score = db.query(Analysis).with_entities(
        Analysis.match_percentage
    ).all()
    avg = sum(s[0] for s in avg_score) / len(avg_score) if avg_score else 0

    return {
        "total_analyses": total_analyses,
        "total_users": total_users,
        "average_match_percentage": round(avg, 1),
    }