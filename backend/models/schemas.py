from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class ScoreBreakdownItem(BaseModel):
    score: float
    weight: float

class ScoreBreakdown(BaseModel):
    tfidf: ScoreBreakdownItem
    sbert: ScoreBreakdownItem
    skill: ScoreBreakdownItem

class KeywordItem(BaseModel):
    term: str
    jd_weight: float
    in_resume: bool

class SkillAnalysis(BaseModel):
    score: float
    resume_skills: List[str]
    jd_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    extra_skills: List[str]

class MatchResponse(BaseModel):
    analysis_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    overall_score: float
    match_percentage: float
    match_label: str
    score_breakdown: ScoreBreakdown
    skill_analysis: SkillAnalysis
    keyword_analysis: List[KeywordItem]
    section_scores: Dict[str, float]
    suggestions: List[str]

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None