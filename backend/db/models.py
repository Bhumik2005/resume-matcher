"""
Database Models
----------------
SQLAlchemy table definitions.

Tables:
  - users      : registered users
  - analyses   : every resume analysis run
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime,
    Integer, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from db.base import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True, default=generate_uuid)
    email         = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name     = Column(String, nullable=True)
    is_active     = Column(Boolean, default=True)
    is_verified   = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    analyses = relationship("Analysis", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"


class Analysis(Base):
    __tablename__ = "analyses"

    id               = Column(String, primary_key=True, default=generate_uuid)
    user_id          = Column(String, ForeignKey("users.id"), nullable=True)

    # Scores
    overall_score    = Column(Float, nullable=False)
    match_percentage = Column(Float, nullable=False)
    match_label      = Column(String, nullable=False)
    tfidf_score      = Column(Float, nullable=True)
    sbert_score      = Column(Float, nullable=True)
    skill_score      = Column(Float, nullable=True)

    # Skills (stored as JSON — no PII)
    matched_skills   = Column(JSON, default=list)
    missing_skills   = Column(JSON, default=list)
    extra_skills     = Column(JSON, default=list)
    jd_skills        = Column(JSON, default=list)

    # Security
    stuffing_detected      = Column(Boolean, default=False)
    text_confidence        = Column(String, nullable=True)
    injection_detected     = Column(Boolean, default=False)
    pii_types_found        = Column(JSON, default=list)

    # Explainability
    match_label      = Column(String, nullable=False)
    seniority_level  = Column(String, nullable=True)
    recruiter_verdict = Column(Text, nullable=True)
    suggestions      = Column(JSON, default=list)

    # Metadata
    word_count       = Column(Integer, nullable=True)
    resume_snippet   = Column(String(300), nullable=True)  # first 300 chars only
    created_at       = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="analyses")

    def __repr__(self):
        return f"<Analysis {self.id} — {self.match_percentage}%>"