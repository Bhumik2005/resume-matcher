import logging
import re
from typing import Dict, Any, Optional
from core.config import settings
from core.tfidf_scorer import get_tfidf_score
from core.sbert_scorer import get_sbert_score, get_section_sbert_scores
from core.skill_extractor import get_skill_gap_analysis

logger = logging.getLogger(__name__)

def _extract_resume_sections(resume_text: str) -> Dict[str, str]:
    section_headers = {
        "experience": r"(work\s+experience|experience|employment)",
        "education": r"(education|academic|qualifications)",
        "skills": r"(skills|technical\s+skills|competencies)",
        "projects": r"(projects|personal\s+projects|portfolio)",
        "summary": r"(summary|objective|profile|about)",
    }
    sections = {}
    text_lower = resume_text.lower()
    for name, pattern in section_headers.items():
        match = re.search(pattern, text_lower)
        if match:
            start = match.start()
            next_starts = []
            for other_name, other_pattern in section_headers.items():
                if other_name == name:
                    continue
                other_match = re.search(other_pattern, text_lower[start + 10:])
                if other_match:
                    next_starts.append(start + 10 + other_match.start())
            end = min(next_starts) if next_starts else len(resume_text)
            sections[name] = resume_text[start:end].strip()
    if not sections:
        sections["general"] = resume_text
    return sections

def _score_to_label(score: float) -> str:
    if score >= 0.80: return "Excellent"
    elif score >= 0.65: return "Good"
    elif score >= 0.50: return "Fair"
    elif score >= 0.35: return "Weak"
    else: return "Poor"

def _generate_suggestions(missing_skills, keyword_analysis, overall_score, section_scores) -> list:
    suggestions = []
    if missing_skills:
        suggestions.append(f"Add these skills to your resume: {', '.join(missing_skills[:5])}.")
    missing_keywords = [k["term"] for k in keyword_analysis if not k["in_resume"]][:5]
    if missing_keywords:
        suggestions.append(f"Include these keywords: {', '.join(missing_keywords)}.")
    if section_scores.get("experience", 1.0) < 0.5:
        suggestions.append("Reframe your experience bullet points to mirror the JD language.")
    if overall_score < 0.5:
        suggestions.append("Overall match is below 50%. Tailor this resume specifically for this role.")
    if not suggestions:
        suggestions.append("Strong match! Ensure your top achievements are near the top of each section.")
    return suggestions

def compute_match_score(resume_text: str, job_text: str, sbert_model: Optional[str] = None, spacy_model: Optional[str] = None) -> Dict[str, Any]:
    sbert_model = sbert_model or settings.SBERT_MODEL
    spacy_model = spacy_model or settings.SPACY_MODEL

    tfidf_score, keyword_analysis = get_tfidf_score(resume_text, job_text)
    sbert_score = get_sbert_score(resume_text, job_text, sbert_model)
    resume_sections = _extract_resume_sections(resume_text)
    section_scores = get_section_sbert_scores(resume_sections, job_text, sbert_model)
    skill_analysis = get_skill_gap_analysis(resume_text, job_text, spacy_model)
    skill_score = skill_analysis["score"]

    final_score = round(min(1.0, max(0.0,
        tfidf_score * settings.TFIDF_WEIGHT +
        sbert_score * settings.SBERT_WEIGHT +
        skill_score * settings.SKILL_WEIGHT
    )), 4)

    return {
        "overall_score": final_score,
        "match_percentage": round(final_score * 100, 1),
        "match_label": _score_to_label(final_score),
        "score_breakdown": {
            "tfidf": {"score": tfidf_score, "weight": settings.TFIDF_WEIGHT},
            "sbert": {"score": sbert_score, "weight": settings.SBERT_WEIGHT},
            "skill": {"score": skill_score, "weight": settings.SKILL_WEIGHT},
        },
        "skill_analysis": skill_analysis,
        "keyword_analysis": keyword_analysis,
        "section_scores": section_scores,
        "suggestions": _generate_suggestions(skill_analysis["missing_skills"], keyword_analysis, final_score, section_scores),
    }