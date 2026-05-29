from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
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

class SkillContext(BaseModel):
    skill: str
    context_sentence: Optional[str]
    strength: str
    strength_score: float
    reason: str

class ScoreDrivers(BaseModel):
    top_boosters: List[str]
    top_detractors: List[str]
    biggest_gap: str

class Seniority(BaseModel):
    level: str
    confidence: float
    signals: List[str]
    years_mentioned: int
    impact_quantifications: int

class Explanation(BaseModel):
    recruiter_verdict: str
    seniority: Seniority
    score_drivers: ScoreDrivers
    section_explanations: Dict[str, str]
    skill_contexts: List[SkillContext]

class StuffingTerm(BaseModel):
    term: str
    count: int
    freq: float

class SecurityReport(BaseModel):
    text_confidence: str
    text_confidence_score: float
    word_count: int
    stuffing_detected: bool
    stuffing_score: float
    flagged_terms: List[StuffingTerm]
    injection_detected: bool
    pii_types_found: List[str]
    warnings: List[str]

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
    explanation: Optional[Explanation] = None
    security: Optional[SecurityReport] = None

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None