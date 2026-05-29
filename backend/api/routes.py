"""
API Routes — with full security pipeline + Qdrant vector storage
"""
import uuid
import logging
from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from celery.result import AsyncResult

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
    logger.info(
        f"Security report: confidence={security_report['text_confidence']['level']}, "
        f"stuffing={security_report['stuffing_analysis']['is_stuffed']}, "
        f"injection={security_report['injection_detected']}"
    )

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

    # ── Attach analysis ID ────────────────────────────────────────────────────
    analysis_id = str(uuid.uuid4())
    result["analysis_id"] = analysis_id

    # ── Store embeddings in Qdrant ────────────────────────────────────────────
    try:
        from core.vector_store import store_resume, store_job
        store_resume(
            resume_text=resume_text,
            metadata={
                "match_percentage": result["match_percentage"],
                "match_label": result["match_label"],
                "matched_skills": result["skill_analysis"]["matched_skills"],
                "missing_skills": result["skill_analysis"]["missing_skills"],
                "seniority": result["explanation"]["seniority"]["level"],
                "word_count": len(resume_text.split()),
                "stuffing_detected": security_report["stuffing_analysis"]["is_stuffed"],
            },
            resume_id=analysis_id,
        )
        store_job(
            job_text=clean_jd,
            metadata={
                "analysis_id": analysis_id,
                "jd_skills": result["skill_analysis"]["jd_skills"],
            },
        )
        logger.info(f"Embeddings stored in Qdrant: {analysis_id}")
    except Exception as e:
        logger.warning(f"Qdrant storage failed (non-blocking): {e}")

    # ── Attach security report ────────────────────────────────────────────────
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


@router.get(
    "/match/{analysis_id}",
    summary="Retrieve past analysis",
)
async def get_analysis(analysis_id: str):
    raise HTTPException(
        status_code=501,
        detail="History retrieval coming in Phase 5 (PostgreSQL).",
    )


@router.get(
    "/search",
    summary="Semantic resume search",
)
@limiter.limit("20/minute")
async def search_resumes(
    request: Request,
    query: str,
    top_k: int = 5,
):
    """
    Search stored resumes semantically using a job description or free text query.
    Returns the most similar resumes from Qdrant vector database.
    """
    if len(query.strip()) < 20:
        raise HTTPException(status_code=400, detail="Query too short — need at least 20 characters.")
    try:
        from core.vector_store import search_similar_resumes
        results = search_similar_resumes(query, top_k=top_k)
        return {
            "query": query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
@router.post(
    "/match/async",
    summary="Submit resume analysis as async task",
)
@limiter.limit("10/minute")
async def match_resume_async(
    request: Request,
    resume: Annotated[UploadFile, File()],
    job_description: Annotated[str, Form()],
):
    """
    Async version of /match.
    Returns a task_id immediately.
    Client polls GET /task/{task_id} for results.
    """
    if resume.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await resume.read()

    if len(pdf_bytes) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"PDF exceeds {settings.MAX_PDF_SIZE_MB}MB.")

    if len(job_description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description too short.")

    # Sanitize
    clean_jd, _ = sanitize_for_llm(job_description)
    clean_jd = sanitize_text(clean_jd)

    # Extract PDF
    try:
        resume_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to process PDF.")

    # Security checks
    security_report = run_security_checks(pdf_bytes, resume_text, clean_jd)

    # Submit to Celery — returns immediately
    analysis_id = str(uuid.uuid4())
    from workers.tasks import analyse_resume_task
    task = analyse_resume_task.apply_async(
        kwargs={
            "resume_text": resume_text,
            "job_text": clean_jd,
            "analysis_id": analysis_id,
            "stuffing_detected": security_report["stuffing_analysis"]["is_stuffed"],
        },
        task_id=analysis_id,
    )

    return {
        "task_id": task.id,
        "analysis_id": analysis_id,
        "status": "queued",
        "message": "Analysis queued. Poll /api/v1/task/{task_id} for results.",
        "security_warnings": security_report["warnings"],
    }


@router.get(
    "/task/{task_id}",
    summary="Poll async task status and result",
)
async def get_task_result(task_id: str):
    """
    Poll this endpoint after submitting an async analysis.

    Returns:
      - status: PENDING | PROGRESS | SUCCESS | FAILURE
      - result: full analysis result (when SUCCESS)
      - progress: current step description (when PROGRESS)
    """
    from workers.celery_app import celery_app
    task = AsyncResult(task_id, app=celery_app)

    if task.state == "PENDING":
        return {"task_id": task_id, "status": "PENDING", "message": "Task is queued..."}

    elif task.state == "PROGRESS":
        return {
            "task_id": task_id,
            "status": "PROGRESS",
            "message": task.info.get("step", "Processing..."),
        }

    elif task.state == "SUCCESS":
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": task.result,
        }

    elif task.state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "message": str(task.info),
        }

    return {"task_id": task_id, "status": task.state}


@router.post(
    "/batch",
    summary="Batch analyse multiple resumes against one JD",
)
@limiter.limit("5/minute")
async def batch_analyse(
    request: Request,
    job_description: Annotated[str, Form()],
    resumes: Annotated[list[UploadFile], File()],
):
    """
    Upload multiple PDF resumes and rank them all against one JD.
    Returns a batch_id — poll /task/{batch_id} for ranked results.
    """
    if len(resumes) > 20:
        raise HTTPException(status_code=400, detail="Max 20 resumes per batch.")

    if len(job_description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description too short.")

    clean_jd, _ = sanitize_for_llm(job_description)
    clean_jd = sanitize_text(clean_jd)

    resume_texts = []
    for resume in resumes:
        pdf_bytes = await resume.read()
        try:
            text = extract_text_from_pdf(pdf_bytes)
            resume_texts.append(text)
        except Exception as e:
            logger.warning(f"Skipping unreadable PDF: {e}")

    if not resume_texts:
        raise HTTPException(status_code=400, detail="No readable PDFs found.")

    batch_id = str(uuid.uuid4())
    from workers.tasks import batch_analyse_task
    task = batch_analyse_task.apply_async(
        kwargs={
            "resume_texts": resume_texts,
            "job_text": clean_jd,
            "batch_id": batch_id,
        },
        task_id=batch_id,
    )

    return {
        "batch_id": batch_id,
        "status": "queued",
        "resume_count": len(resume_texts),
        "message": f"Batch of {len(resume_texts)} resumes queued. Poll /api/v1/task/{batch_id} for ranked results.",
    }
@router.get(
    "/evaluate",
    summary="Run evaluation benchmark",
)
async def run_evaluation():
    """
    Run the full evaluation pipeline comparing:
    - TF-IDF baseline
    - Hybrid system (TF-IDF + SBERT + Skill)

    Returns NDCG, Precision, Recall, MAP metrics.
    This proves the ML system actually works better than baseline.
    """
    try:
        from evaluation.evaluator import run_full_evaluation
        from evaluation.report import format_report
        results = run_full_evaluation()
        report = format_report(results)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")