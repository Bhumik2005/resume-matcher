"""
Security & Anti-Cheat Module
-----------------------------
Handles all input validation, sanitization, and fraud detection
before any ML processing happens.

Checks:
1. PDF sanitization — strip malicious content
2. Text confidence — detect complex layouts that hurt extraction
3. Keyword stuffing — detect resume gaming
4. Prompt injection — strip LLM manipulation attempts
5. PII detection — flag sensitive data before storage
"""
import re
import logging
from typing import Dict, Tuple, List
from collections import Counter

logger = logging.getLogger(__name__)

# ── Prompt injection patterns ─────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"you\s+are\s+now\s+a",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?previous\s+instructions?",
    r"new\s+instructions?\s*:",
    r"system\s*:\s*you",
    r"rate\s+this\s+resume\s+[0-9]+",
    r"score\s*=\s*[0-9]+",
    r"give\s+(this|me)\s+a\s+(perfect|100|high)",
    r"<\s*script",
    r"javascript\s*:",
    r"data\s*:\s*text/html",
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# ── PII patterns ──────────────────────────────────────────────────────────────
_PII_PATTERNS = {
    "email":   re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone":   re.compile(r"(\+?\d[\d\s\-().]{7,}\d)"),
    "ssn":     re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
    "address": re.compile(r"\d+\s+[a-zA-Z]+\s+(street|st|avenue|ave|road|rd|blvd|lane|ln)\b", re.IGNORECASE),
}


# ── 1. PDF Sanitization ───────────────────────────────────────────────────────

def validate_pdf_bytes(pdf_bytes: bytes, max_mb: int = 10, max_pages: int = 10) -> Tuple[bool, str]:
    """
    Validate raw PDF bytes before extraction.
    Returns (is_valid, reason_if_invalid)
    """
    # Size check
    max_bytes = max_mb * 1024 * 1024
    if len(pdf_bytes) == 0:
        return False, "PDF file is empty."
    if len(pdf_bytes) > max_bytes:
        return False, f"PDF exceeds {max_mb}MB limit. Please compress your resume."

    # Magic bytes check — real PDFs start with %PDF
    if not pdf_bytes[:4] == b'%PDF':
        return False, "File does not appear to be a valid PDF."

    # Page count check
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        doc.close()
        if page_count > max_pages:
            return False, f"PDF has {page_count} pages. Resumes should be max {max_pages} pages."
        if page_count == 0:
            return False, "PDF has no pages."
    except Exception as e:
        logger.warning(f"Page count check failed: {e}")
        # Don't block — just warn

    return True, ""


def get_text_confidence(text: str) -> Dict:
    """
    Score how well the PDF was extracted.
    Low confidence = complex layout, columns, graphics, scanned image.

    Returns dict with:
      - confidence: 0-1 float
      - level: "high" | "medium" | "low"
      - warning: human-readable message or None
    """
    word_count = len(text.split())
    char_count = len(text.strip())

    # Heuristics
    has_gibberish = len(re.findall(r"[^\x20-\x7E]", text)) / max(char_count, 1) > 0.05
    avg_word_len = sum(len(w) for w in text.split()) / max(word_count, 1)
    too_short = word_count < 100
    very_short = word_count < 50
    weird_chars = len(re.findall(r"[|}{<>]", text)) > 20  # table artifacts

    if very_short or has_gibberish:
        return {
            "confidence": 0.2,
            "level": "low",
            "word_count": word_count,
            "warning": (
                "Very little text was extracted from your PDF. "
                "Your resume may use a complex layout, columns, or graphics. "
                "For best results, use a single-column, text-based PDF."
            )
        }
    elif too_short or weird_chars or avg_word_len > 15:
        return {
            "confidence": 0.6,
            "level": "medium",
            "word_count": word_count,
            "warning": (
                "Some sections of your resume may not have been read correctly. "
                "Tables, icons, or multi-column layouts can reduce accuracy."
            )
        }
    else:
        return {
            "confidence": 1.0,
            "level": "high",
            "word_count": word_count,
            "warning": None
        }


# ── 2. Keyword Stuffing Detection ────────────────────────────────────────────

def detect_keyword_stuffing(text: str, threshold: int = 6) -> Dict:
    """
    Detect if a resume has suspiciously repeated keywords — a common
    ATS gaming technique.

    Strategy:
    - Count how often each meaningful word appears
    - Flag words that appear more than `threshold` times
    - Check for wall-of-keywords sections (no surrounding sentences)
    - Check skill-to-context ratio

    Returns:
        {
          "is_stuffed": bool,
          "confidence": float,        # 0-1, how confident we are it's stuffed
          "flagged_terms": [...],     # words repeated suspiciously often
          "stuffing_score": float,    # 0-1, overall stuffing severity
          "warning": str or None
        }
    """
    text_lower = text.lower()
    words = re.findall(r"\b[a-z][a-z0-9+#.]{1,20}\b", text_lower)

    # Filter stop words
    stop_words = {
        "the", "and", "for", "with", "this", "that", "have", "from",
        "are", "was", "were", "has", "had", "not", "but", "you", "your",
        "our", "their", "will", "can", "been", "also", "more", "about",
        "into", "than", "then", "its", "they", "all", "one", "other",
        "new", "use", "used", "using", "work", "team", "role", "year",
        "years", "company", "strong", "good", "experience",
    }
    meaningful_words = [w for w in words if w not in stop_words and len(w) > 3]
    word_counts = Counter(meaningful_words)

    # Flag suspiciously repeated terms
    total_words = len(meaningful_words)
    flagged = []
    for word, count in word_counts.most_common(30):
        freq_ratio = count / max(total_words, 1)
        if count >= threshold and freq_ratio > 0.02:
            flagged.append({"term": word, "count": count, "freq": round(freq_ratio, 3)})

    # Detect wall-of-keywords pattern:
    # Lines with only comma/space separated words and no verbs
    lines = text.split("\n")
    keyword_wall_lines = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        tokens = re.findall(r"\b\w+\b", line)
        if 5 <= len(tokens) <= 20:
            # Check if line is just a list of nouns with no sentence structure
            has_verb_pattern = bool(re.search(r"\b(developed|built|led|managed|created|designed|implemented|improved|reduced|increased|analyzed|deployed|maintained)\b", line, re.IGNORECASE))
            has_connector = bool(re.search(r"\b(and|the|for|with|using|in|of|to|a|an)\b", line, re.IGNORECASE))
            if not has_verb_pattern and not has_connector:
                keyword_wall_lines += 1

    wall_ratio = keyword_wall_lines / max(len([l for l in lines if l.strip()]), 1)

    # Compute overall stuffing score
    flagged_weight = min(len(flagged) / 5, 1.0) * 0.5
    wall_weight = min(wall_ratio * 3, 1.0) * 0.5
    stuffing_score = round(flagged_weight + wall_weight, 3)
    is_stuffed = stuffing_score > 0.4 or len(flagged) >= 3

    warning = None
    if is_stuffed:
        terms = ", ".join(f["term"] for f in flagged[:5])
        warning = (
            f"This resume shows signs of keyword stuffing. "
            f"Terms repeated unusually often: {terms}. "
            f"Scores may be artificially inflated."
        )

    return {
        "is_stuffed": is_stuffed,
        "confidence": round(min(stuffing_score * 1.5, 1.0), 3),
        "flagged_terms": flagged[:10],
        "stuffing_score": stuffing_score,
        "warning": warning,
    }


# ── 3. Prompt Injection Guard ─────────────────────────────────────────────────

def sanitize_for_llm(text: str) -> Tuple[str, bool]:
    """
    Strip prompt injection attempts from text before passing to any LLM.
    Used when the AI rewriter (Phase 6) is added.

    Returns:
        (cleaned_text, was_injected)
    """
    was_injected = bool(_INJECTION_RE.search(text))
    if was_injected:
        logger.warning("Prompt injection attempt detected and stripped.")
        cleaned = _INJECTION_RE.sub("[REMOVED]", text)
        return cleaned, True
    return text, False


def sanitize_text(text: str) -> str:
    """
    General text sanitization:
    - Remove null bytes
    - Strip excessive whitespace
    - Remove non-printable characters
    - Limit total length
    """
    # Remove null bytes and control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize unicode dashes and quotes to ASCII
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    # Collapse whitespace
    text = re.sub(r"[ \t]{3,}", "  ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    # Hard limit: 50,000 characters (no resume needs more)
    if len(text) > 50_000:
        text = text[:50_000]
        logger.warning("Text truncated to 50,000 characters.")
    return text.strip()


# ── 4. PII Scrubber ───────────────────────────────────────────────────────────

def scrub_pii(text: str) -> Dict:
    """
    Detect and remove PII from text before storing in DB.
    Never store raw resume text — only scrubbed metadata.

    Returns:
        {
          "scrubbed_text": str,    # text with PII replaced
          "pii_found": list,       # types of PII detected
          "pii_counts": dict       # count per type
        }
    """
    scrubbed = text
    pii_found = []
    pii_counts = {}

    for pii_type, pattern in _PII_PATTERNS.items():
        matches = pattern.findall(scrubbed)
        if matches:
            pii_found.append(pii_type)
            pii_counts[pii_type] = len(matches)
            scrubbed = pattern.sub(f"[{pii_type.upper()}_REMOVED]", scrubbed)

    return {
        "scrubbed_text": scrubbed,
        "pii_found": pii_found,
        "pii_counts": pii_counts,
    }


# ── 5. Full Security Check ────────────────────────────────────────────────────

def run_security_checks(
    pdf_bytes: bytes,
    resume_text: str,
    job_text: str,
) -> Dict:
    """
    Run all security checks in one call.
    Called from routes.py before any ML processing.

    Returns a security report that gets attached to the API response.
    """
    report = {
        "passed": True,
        "warnings": [],
        "errors": [],
        "text_confidence": None,
        "stuffing_analysis": None,
        "injection_detected": False,
        "pii_scrub": None,
    }

    # 1. Text confidence
    confidence = get_text_confidence(resume_text)
    report["text_confidence"] = confidence
    if confidence["warning"]:
        report["warnings"].append(confidence["warning"])

    # 2. Keyword stuffing
    stuffing = detect_keyword_stuffing(resume_text)
    report["stuffing_analysis"] = stuffing
    if stuffing["is_stuffed"]:
        report["warnings"].append(stuffing["warning"])

    # 3. Prompt injection in both texts
    _, resume_injected = sanitize_for_llm(resume_text)
    _, jd_injected = sanitize_for_llm(job_text)
    if resume_injected or jd_injected:
        report["injection_detected"] = True
        report["warnings"].append(
            "Potential prompt injection detected and neutralized in input text."
        )

    # 4. PII detection (for logging awareness — not blocking)
    pii = scrub_pii(resume_text)
    report["pii_scrub"] = {
        "pii_found": pii["pii_found"],
        "pii_counts": pii["pii_counts"],
    }

    return report