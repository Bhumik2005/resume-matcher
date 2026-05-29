"""
Explainability Engine — Phase B
---------------------------------
Turns raw scores into plain English reasoning.

Every major ATS tool gives you a number.
This tells you WHY.

Outputs:
1. Overall explanation — one paragraph summary
2. Section reasoning — why each section scored the way it did
3. Skill context scoring — is the skill mentioned strongly or weakly?
4. Score driver analysis — what's pulling the score up or down the most
5. Recruiter-style verdict — how a human recruiter would read this resume
"""
import re
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


# ── 1. Skill Context Scorer ───────────────────────────────────────────────────

# Strong action verbs that indicate real experience
_STRONG_VERBS = {
    "built", "developed", "designed", "architected", "led", "managed",
    "deployed", "implemented", "created", "engineered", "launched",
    "optimized", "reduced", "increased", "improved", "automated",
    "scaled", "migrated", "delivered", "shipped", "published",
    "trained", "fine-tuned", "researched", "authored", "owned",
}

# Weak/vague context words
_WEAK_WORDS = {
    "familiar", "exposure", "basic", "learning", "interested",
    "knowledge of", "understanding of", "some experience", "coursework",
    "studied", "introductory", "beginner", "hobby", "personal interest",
    "currently learning", "in progress",
}


def score_skill_context(skill: str, resume_text: str) -> Dict:
    """
    Find the sentence(s) containing a skill and evaluate how strongly
    the candidate actually demonstrates it.

    Returns:
        {
          "skill": str,
          "context_sentence": str,     # the sentence where skill was found
          "strength": "strong" | "moderate" | "weak" | "not_found",
          "strength_score": float,     # 0-1
          "reason": str                # plain English explanation
        }
    """
    text_lower = resume_text.lower()
    skill_lower = skill.lower()

    # Find all sentences containing the skill
    sentences = re.split(r"(?<=[.!?\n])\s*", resume_text)
    matching_sentences = [
        s.strip() for s in sentences
        if skill_lower in s.lower() and len(s.strip()) > 10
    ]

    if not matching_sentences:
        return {
            "skill": skill,
            "context_sentence": None,
            "strength": "not_found",
            "strength_score": 0.0,
            "reason": f"'{skill}' was not found in any meaningful context."
        }

    # Pick the best sentence (longest with most context)
    best_sentence = max(matching_sentences, key=lambda s: len(s))
    sentence_lower = best_sentence.lower()

    # Check for weak indicators first
    weak_found = [w for w in _WEAK_WORDS if w in sentence_lower]
    if weak_found:
        return {
            "skill": skill,
            "context_sentence": best_sentence[:200],
            "strength": "weak",
            "strength_score": 0.2,
            "reason": f"'{skill}' appears in a weak context ('{weak_found[0]}'). This suggests familiarity rather than hands-on experience."
        }

    # Check for strong action verbs
    words_in_sentence = set(sentence_lower.split())
    strong_found = _STRONG_VERBS & words_in_sentence
    if strong_found:
        verb = list(strong_found)[0]
        return {
            "skill": skill,
            "context_sentence": best_sentence[:200],
            "strength": "strong",
            "strength_score": 1.0,
            "reason": f"'{skill}' is backed by a strong action verb ('{verb}'), indicating real hands-on experience."
        }

    # Check for quantified impact (numbers = real work)
    has_numbers = bool(re.search(r"\d+", best_sentence))
    if has_numbers:
        return {
            "skill": skill,
            "context_sentence": best_sentence[:200],
            "strength": "strong",
            "strength_score": 0.85,
            "reason": f"'{skill}' is mentioned alongside quantified results, which is a strong signal of real experience."
        }

    # Moderate — mentioned but no strong signal either way
    return {
        "skill": skill,
        "context_sentence": best_sentence[:200],
        "strength": "moderate",
        "strength_score": 0.55,
        "reason": f"'{skill}' is mentioned but without strong action verbs or measurable impact. Consider strengthening this context."
    }


def analyze_skill_contexts(
    matched_skills: List[str],
    resume_text: str,
    top_n: int = 8,
) -> List[Dict]:
    """
    Run context scoring on the top N matched skills.
    Returns list sorted by strength_score ascending
    (weakest first — most actionable for the user).
    """
    results = []
    for skill in matched_skills[:top_n]:
        results.append(score_skill_context(skill, resume_text))
    return sorted(results, key=lambda x: x["strength_score"])


# ── 2. Score Driver Analysis ──────────────────────────────────────────────────

def get_score_drivers(
    tfidf_score: float,
    sbert_score: float,
    skill_score: float,
    section_scores: Dict[str, float],
    missing_skills: List[str],
    keyword_analysis: List[Dict],
) -> Dict:
    """
    Identify what is helping and hurting the score the most.

    Returns:
        {
          "top_boosters": [...],   # what's helping
          "top_detractors": [...], # what's hurting
          "biggest_gap": str,      # the single most impactful thing to fix
        }
    """
    boosters = []
    detractors = []

    # Layer analysis
    if sbert_score >= 0.65:
        boosters.append(f"Strong semantic alignment — your resume language closely mirrors the job description (SBERT: {round(sbert_score*100)}%)")
    elif sbert_score < 0.40:
        detractors.append(f"Weak semantic match ({round(sbert_score*100)}%) — your resume language is quite different from the job description. Reframe your experience using the JD's terminology.")

    if tfidf_score >= 0.5:
        boosters.append(f"Good keyword coverage — many exact terms from the JD appear in your resume (TF-IDF: {round(tfidf_score*100)}%)")
    elif tfidf_score < 0.25:
        detractors.append(f"Low keyword overlap ({round(tfidf_score*100)}%) — many specific terms from the JD are absent from your resume.")

    if skill_score >= 0.7:
        boosters.append(f"Strong technical skill match — you have {round(skill_score*100)}% of the required skills.")
    elif skill_score < 0.4:
        detractors.append(f"Significant skill gap ({round(skill_score*100)}%) — you're missing {len(missing_skills)} key skills the JD requires.")

    # Section analysis
    weak_sections = [(s, v) for s, v in section_scores.items() if v < 0.45]
    strong_sections = [(s, v) for s, v in section_scores.items() if v >= 0.70]

    for sec, val in strong_sections:
        boosters.append(f"Your {sec} section is a strong match ({round(val*100)}%).")

    for sec, val in weak_sections:
        detractors.append(f"Your {sec} section has low alignment ({round(val*100)}%) — consider rewriting it to better reflect the role.")

    # Missing keywords
    missing_kw = [k["term"] for k in keyword_analysis if not k["in_resume"]][:3]
    if missing_kw:
        detractors.append(f"High-value keywords missing: {', '.join(missing_kw)}.")

    # Biggest single gap
    if missing_skills:
        biggest_gap = f"Adding '{missing_skills[0]}' to your resume would have the highest single impact on your score."
    elif weak_sections:
        sec = weak_sections[0][0]
        biggest_gap = f"Rewriting your {sec} section to mirror the JD language would have the highest impact."
    elif missing_kw:
        biggest_gap = f"Including the keyword '{missing_kw[0]}' would directly improve your ATS ranking."
    else:
        biggest_gap = "Your resume is already well-aligned. Focus on quantifying your achievements more specifically."

    return {
        "top_boosters": boosters[:4],
        "top_detractors": detractors[:4],
        "biggest_gap": biggest_gap,
    }


# ── 3. Section Reasoning ──────────────────────────────────────────────────────

def explain_section_scores(section_scores: Dict[str, float]) -> Dict[str, str]:
    """
    Generate a plain English explanation for each section score.
    """
    explanations = {}

    templates = {
        "experience": {
            "high":   "Your experience section closely mirrors the responsibilities and language in the job description. Recruiters will see strong role alignment.",
            "medium": "Your experience section partially matches the JD. Consider reframing bullet points to use the same action verbs and outcomes the JD emphasizes.",
            "low":    "Your experience section has low overlap with the JD. The role requirements and your described responsibilities read quite differently — significant rewriting is recommended.",
        },
        "skills": {
            "high":   "Your skills section covers most of the technical requirements. This is a strong signal for ATS systems.",
            "medium": "Your skills section covers some required technologies but is missing several key ones from the JD.",
            "low":    "Your skills section has poor coverage of the required technologies. Add the missing skills if you have them.",
        },
        "education": {
            "high":   "Your educational background aligns well with what the role requires.",
            "medium": "Your education partially meets the requirements — relevant coursework or certifications could strengthen this section.",
            "low":    "Your education section has low alignment. This may not be critical depending on the role.",
        },
        "projects": {
            "high":   "Your projects demonstrate directly relevant technical work — this is a strong differentiator.",
            "medium": "Some projects are relevant but could be described more in terms of the skills and outcomes the JD values.",
            "low":    "Your projects section doesn't closely match the JD requirements. Consider adding projects that use the required tech stack.",
        },
        "summary": {
            "high":   "Your professional summary is well-targeted to this role.",
            "medium": "Your summary is generic. Tailoring it specifically to this role and company would improve your match significantly.",
            "low":    "Your summary has little overlap with the JD. A role-specific summary could boost your score noticeably.",
        },
        "general": {
            "high":   "Overall resume content aligns well with the job description.",
            "medium": "Resume content partially matches. More targeted language would improve the score.",
            "low":    "Resume content has low overlap with the JD. Significant tailoring is recommended.",
        },
    }

    for section, score in section_scores.items():
        level = "high" if score >= 0.65 else "medium" if score >= 0.40 else "low"
        template = templates.get(section, templates["general"])
        explanations[section] = template[level]

    return explanations


# ── 4. Seniority Detector ─────────────────────────────────────────────────────

def detect_seniority(resume_text: str) -> Dict:
    """
    Estimate the candidate's seniority level from resume language.
    This is a heuristic — not ML — but surprisingly effective.

    Returns:
        {
          "level": "junior" | "mid" | "senior" | "lead",
          "confidence": float,
          "signals": [...],
          "years_mentioned": int,
        }
    """
    text_lower = resume_text.lower()

    # Extract years of experience mentions
    year_patterns = re.findall(r"(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)", text_lower)
    years_mentioned = max([int(y[0]) for y in year_patterns], default=0)

    # Leadership signals
    leadership_signals = [
        w for w in [
            "led", "managed", "mentored", "directed", "headed",
            "architected", "principal", "staff", "senior", "lead",
            "team lead", "tech lead", "engineering manager"
        ] if w in text_lower
    ]

    # Junior signals
    junior_signals = [
        w for w in [
            "intern", "internship", "fresher", "graduate", "entry level",
            "junior", "associate", "trainee", "student", "bootcamp",
            "currently learning", "seeking first", "recently graduated"
        ] if w in text_lower
    ]

    # Impact signals (senior people quantify things)
    impact_signals = re.findall(r"\d+%|\$\d+|\d+x|\d+\s*million|\d+\s*billion|\d+k\s+users", text_lower)

    # Determine level
    signals = []
    if junior_signals or years_mentioned <= 1:
        level = "junior"
        signals = junior_signals[:3]
    elif leadership_signals and (years_mentioned >= 5 or len(impact_signals) >= 2):
        level = "lead"
        signals = leadership_signals[:3]
    elif years_mentioned >= 5 or len(leadership_signals) >= 2:
        level = "senior"
        signals = leadership_signals[:3]
    else:
        level = "mid"
        signals = [f"{years_mentioned} years mentioned"] if years_mentioned else ["no clear seniority signals"]

    confidence = 0.8 if years_mentioned > 0 else 0.5

    return {
        "level": level,
        "confidence": confidence,
        "signals": signals,
        "years_mentioned": years_mentioned,
        "impact_quantifications": len(impact_signals),
    }


# ── 5. Recruiter Verdict ──────────────────────────────────────────────────────

def generate_recruiter_verdict(
    match_percentage: float,
    match_label: str,
    seniority: Dict,
    skill_score: float,
    missing_skills: List[str],
    stuffing_detected: bool,
) -> str:
    """
    Simulate how a human recruiter would quickly react to this resume.
    One honest paragraph — no sugarcoating.
    """
    level = seniority["level"]
    pct = match_percentage

    if stuffing_detected:
        return (
            f"⚠️ This resume shows signs of keyword optimization that may backfire with human reviewers. "
            f"While the ATS score is {pct}%, the repeated keywords without strong context could raise red flags. "
            f"Focus on demonstrating real impact rather than keyword density."
        )

    if pct >= 80:
        return (
            f"✅ Strong candidate. This {level}-level resume closely matches what the role requires. "
            f"The technical skills and experience language align well with the job description. "
            f"A recruiter would likely move this to the interview stage."
        )
    elif pct >= 65:
        return (
            f"👍 Decent match. This {level}-level resume covers most of the core requirements "
            f"but has some gaps. "
            + (f"Missing skills ({', '.join(missing_skills[:3])}) may be flagged in a technical screen. " if missing_skills else "")
            + "With targeted improvements, this could be a strong application."
        )
    elif pct >= 45:
        return (
            f"⚠️ Partial match. A recruiter would see this {level}-level resume as a stretch for this role. "
            f"The experience and language don't closely mirror the JD. "
            + (f"Key missing skills: {', '.join(missing_skills[:3])}. " if missing_skills else "")
            + "Significant tailoring is needed before applying."
        )
    else:
        return (
            f"❌ Weak match. This resume as written would likely be filtered out by ATS before reaching a recruiter. "
            f"The role requirements and your current resume are significantly misaligned. "
            + (f"You're missing {len(missing_skills)} required skills. " if missing_skills else "")
            + "Either develop the missing skills or target a better-matched role."
        )


# ── 6. Master Explainer ───────────────────────────────────────────────────────

def generate_full_explanation(
    resume_text: str,
    match_percentage: float,
    match_label: str,
    score_breakdown: Dict,
    skill_analysis: Dict,
    section_scores: Dict,
    keyword_analysis: List[Dict],
    stuffing_detected: bool = False,
) -> Dict:
    """
    Master function — generates the complete explanation package.
    Called from scorer.py and attached to the API response.
    """
    tfidf_score = score_breakdown["tfidf"]["score"]
    sbert_score = score_breakdown["sbert"]["score"]
    skill_score = score_breakdown["skill"]["score"]
    missing_skills = skill_analysis["missing_skills"]
    matched_skills = skill_analysis["matched_skills"]

    # Run all explainers
    skill_contexts = analyze_skill_contexts(matched_skills, resume_text, top_n=8)
    score_drivers = get_score_drivers(
        tfidf_score, sbert_score, skill_score,
        section_scores, missing_skills, keyword_analysis
    )
    section_explanations = explain_section_scores(section_scores)
    seniority = detect_seniority(resume_text)
    recruiter_verdict = generate_recruiter_verdict(
        match_percentage, match_label, seniority,
        skill_score, missing_skills, stuffing_detected
    )

    return {
        "recruiter_verdict": recruiter_verdict,
        "seniority": seniority,
        "score_drivers": score_drivers,
        "section_explanations": section_explanations,
        "skill_contexts": skill_contexts,
    }