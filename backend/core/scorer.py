"""
Match Scoring Orchestrator — with Explainability (Phase B)
"""
import logging
import re
from typing import Dict, Any, Optional

from core.config import settings
from core.tfidf_scorer import get_tfidf_score
from core.sbert_scorer import get_sbert_score, get_section_sbert_scores
from core.skill_extractor import get_skill_gap_analysis
from core.explainer import generate_full_explanation

logger = logging.getLogger(__name__)


def _extract_resume_sections(resume_text: str) -> Dict[str, str]:
    section_headers = {
        "experience": r"(work\s+experience|experience|employment)",
        "education":  r"(education|academic|qualifications)",
        "skills":     r"(skills|technical\s+skills|competencies)",
        "projects":   r"(projects|personal\s+projects|portfolio)",
        "summary":    r"(summary|objective|profile|about)",
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
    if score >= 0.80:   return "Excellent"
    elif score >= 0.65: return "Good"
    elif score >= 0.50: return "Fair"
    elif score >= 0.35: return "Weak"
    else:               return "Poor"


def _generate_suggestions(
    missing_skills: list,
    keyword_analysis: list,
    overall_score: float,
    section_scores: dict,
    score_drivers: dict,
) -> list:
    suggestions = []

    # Use the biggest gap from explainer as first suggestion
    if score_drivers.get("biggest_gap"):
        suggestions.append(score_drivers["biggest_gap"])

    if missing_skills:
        suggestions.append(
            f"Add these high-value skills to your resume: {', '.join(missing_skills[:5])}."
        )

    missing_kw = [k["term"] for k in keyword_analysis if not k["in_resume"]][:4]
    if missing_kw:
        suggestions.append(f"Include these keywords from the JD: {', '.join(missing_kw)}.")

    weak_sections = [s for s, v in section_scores.items() if v < 0.45]
    if weak_sections:
        suggestions.append(
            f"Rewrite your {weak_sections[0]} section using the language and requirements from the JD."
        )

    if overall_score < 0.5:
        suggestions.append(
            "Overall match is below 50%. Tailor this resume specifically for this role — "
            "use the exact job description language throughout."
        )

    if not suggestions:
        suggestions.append(
            "Strong match! Fine-tune by quantifying your achievements "
            "(numbers, percentages, scale) to stand out further."
        )

    return suggestions[:5]


def compute_match_score(
    resume_text: str,
    job_text: str,
    sbert_model: Optional[str] = None,
    spacy_model: Optional[str] = None,
    stuffing_detected: bool = False,
) -> Dict[str, Any]:
    sbert_model = sbert_model or settings.SBERT_MODEL
    spacy_model = spacy_model or settings.SPACY_MODEL

    logger.info("Starting match score computation...")

    # ── Layer 1: TF-IDF ───────────────────────────────────────────────────────
    tfidf_score, keyword_analysis = get_tfidf_score(resume_text, job_text)

    # ── Layer 2: SBERT ────────────────────────────────────────────────────────
    sbert_score = get_sbert_score(resume_text, job_text, sbert_model)
    resume_sections = _extract_resume_sections(resume_text)
    section_scores = get_section_sbert_scores(resume_sections, job_text, sbert_model)

    # ── Layer 3: Skill extraction ─────────────────────────────────────────────
    skill_analysis = get_skill_gap_analysis(resume_text, job_text, spacy_model)
    skill_score = skill_analysis["score"]

    # ── Weighted final score ──────────────────────────────────────────────────
    final_score = round(min(1.0, max(0.0,
        tfidf_score * settings.TFIDF_WEIGHT +
        sbert_score * settings.SBERT_WEIGHT +
        skill_score * settings.SKILL_WEIGHT
    )), 4)

    match_percentage = round(final_score * 100, 1)
    match_label = _score_to_label(final_score)

    score_breakdown = {
        "tfidf": {"score": tfidf_score, "weight": settings.TFIDF_WEIGHT},
        "sbert": {"score": sbert_score, "weight": settings.SBERT_WEIGHT},
        "skill": {"score": skill_score, "weight": settings.SKILL_WEIGHT},
    }

    # ── Phase B: Full explanation ─────────────────────────────────────────────
    explanation = generate_full_explanation(
        resume_text=resume_text,
        match_percentage=match_percentage,
        match_label=match_label,
        score_breakdown=score_breakdown,
        skill_analysis=skill_analysis,
        section_scores=section_scores,
        keyword_analysis=keyword_analysis,
        stuffing_detected=stuffing_detected,
    )

    suggestions = _generate_suggestions(
        skill_analysis["missing_skills"],
        keyword_analysis,
        final_score,
        section_scores,
        explanation["score_drivers"],
    )

    logger.info(f"Match complete: {match_percentage}% ({match_label})")

    return {
        "overall_score": final_score,
        "match_percentage": match_percentage,
        "match_label": match_label,
        "score_breakdown": score_breakdown,
        "skill_analysis": skill_analysis,
        "keyword_analysis": keyword_analysis,
        "section_scores": section_scores,
        "suggestions": suggestions,
        "explanation": explanation,
    }