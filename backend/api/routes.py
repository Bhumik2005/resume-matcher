"""
API Routes — with full security pipeline
"""
import uuid
import logging
from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings
from core.pdf_extractor import extract_text_from_pdf
from core.scorer import compute_match_score
from core.security import (
    run_security_checks,
    sanitize_text,
    sanitize_for_llm,
)
from models.schemas import MatchResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiter — 10 requests per minute per IP
limiter = Limiter(key_func=get_remote_address)
MAX_BYTES = settings.MAX_PDF_SIZE_MB * 1024 * 1024


@router.post(
    "/match",
    response_model=MatchResponse,
    summary="Analyse resume vs job description",
)
@limiter.limit("10/minute")
async def match_resume(
    request: Request,
    resume: Annotated[UploadFile, File()],
    job_description: Annotated[str, Form()],
):
    # ── Basic validation ──────────────────────────────────────────────────────
    if resume.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await resume.read()

    if len(pdf_bytes) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"PDF exceeds {settings.MAX_PDF_SIZE_MB}MB.")

    if len(job_description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description too short.")

    # ── Sanitize JD input ─────────────────────────────────────────────────────
    clean_jd, jd_injected = sanitize_for_llm(job_description)
    clean_jd = sanitize_text(clean_jd)

    # ── Extract PDF text ──────────────────────────────────────────────────────
    try:
        resume_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("PDF extraction failed")
        raise HTTPException(status_code=500, detail="Failed to process PDF.")

    # ── Run full security checks ──────────────────────────────────────────────
    security_report = run_security_checks(pdf_bytes, resume_text, clean_jd)
    logger.info(f"Security report: confidence={security_report['text_confidence']['level']}, "
                f"stuffing={security_report['stuffing_analysis']['is_stuffed']}, "
                f"injection={security_report['injection_detected']}")

    # ── Block only on hard failures ───────────────────────────────────────────
    # Low confidence text — warn but don't block
    # Stuffing detected — warn but don't block (we flag it in response)
    # Injection — sanitized above, continue

    # ── Run ML pipeline ───────────────────────────────────────────────────────
    try:
        result = compute_match_score(
            resume_text,
            clean_jd,
            stuffing_detected=security_report["stuffing_analysis"]["is_stuffed"],
        )
    except Exception as e:
        logger.exception("Scoring pipeline failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # ── Attach metadata ───────────────────────────────────────────────────────
    result["analysis_id"] = str(uuid.uuid4())
    result["security"] = {
        "text_confidence": security_report["text_confidence"]["level"],
        "text_confidence_score": security_report["text_confidence"]["confidence"],
        "word_count": security_report["text_confidence"]["word_count"],
        "stuffing_detected": security_report["stuffing_analysis"]["is_stuffed"],
        "stuffing_score": security_report["stuffing_analysis"]["stuffing_score"],
        "flagged_terms": security_report["stuffing_analysis"]["flagged_terms"],
        "injection_detected": security_report["injection_detected"],
        "pii_types_found": security_report["pii_scrub"]["pii_found"],
        "warnings": security_report["warnings"],
    }

    return MatchResponse(**result)


@router.get("/match/{analysis_id}", summary="Retrieve past analysis")
async def get_analysis(analysis_id: str):
    raise HTTPException(
        status_code=501,
        detail="History retrieval coming in Phase D (PostgreSQL)."
    )