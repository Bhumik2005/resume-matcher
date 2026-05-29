"""
Celery Tasks — Async ML Pipeline
----------------------------------
Each task is a unit of ML work that runs in the background.

Tasks:
  1. analyse_resume_task   — full ML pipeline (main task)
  2. generate_embedding_task — just embedding generation
  3. batch_analyse_task    — analyse multiple resumes against one JD
"""
import logging
import uuid
from typing import Dict, Any

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="workers.tasks.analyse_resume",
    max_retries=2,
    default_retry_delay=5,
)
def analyse_resume_task(
    self,
    resume_text: str,
    job_text: str,
    analysis_id: str,
    stuffing_detected: bool = False,
) -> Dict[str, Any]:
    """
    Main async ML task — runs the full scoring pipeline.

    Args:
        resume_text:       Cleaned resume text
        job_text:          Cleaned job description text
        analysis_id:       UUID for this analysis
        stuffing_detected: Whether keyword stuffing was detected

    Returns:
        Full result dict (same as synchronous scorer output)
    """
    try:
        logger.info(f"Starting async analysis: {analysis_id}")

        # Update task state so client knows we're working
        self.update_state(
            state="PROGRESS",
            meta={"step": "Running ML pipeline...", "analysis_id": analysis_id}
        )

        # ── Run ML pipeline ───────────────────────────────────────────────
        from core.scorer import compute_match_score
        result = compute_match_score(
            resume_text,
            job_text,
            stuffing_detected=stuffing_detected,
        )

        self.update_state(
            state="PROGRESS",
            meta={"step": "Storing embeddings...", "analysis_id": analysis_id}
        )

        # ── Store in Qdrant ───────────────────────────────────────────────
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
                    "stuffing_detected": stuffing_detected,
                },
                resume_id=analysis_id,
            )
            store_job(
                job_text=job_text,
                metadata={
                    "analysis_id": analysis_id,
                    "jd_skills": result["skill_analysis"]["jd_skills"],
                },
            )
        except Exception as e:
            logger.warning(f"Qdrant storage failed (non-blocking): {e}")

        result["analysis_id"] = analysis_id
        logger.info(f"Async analysis complete: {analysis_id} — {result['match_percentage']}%")
        return result

    except Exception as e:
        logger.exception(f"Task failed: {analysis_id}")
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="workers.tasks.generate_embedding",
    max_retries=2,
)
def generate_embedding_task(
    self,
    text: str,
    text_id: str,
    text_type: str = "resume",
) -> Dict[str, Any]:
    """
    Lightweight task — just generate and store an embedding.
    Used for pre-indexing resumes without full analysis.

    Args:
        text:      Text to embed
        text_id:   UUID for this text
        text_type: "resume" or "job"
    """
    try:
        from core.embeddings import get_embedding
        from core.vector_store import store_resume, store_job

        embedding = get_embedding(text)

        if text_type == "resume":
            store_resume(
                resume_text=text,
                metadata={"text_type": "resume", "pre_indexed": True},
                resume_id=text_id,
            )
        else:
            store_job(
                job_text=text,
                metadata={"text_type": "job", "pre_indexed": True},
                job_id=text_id,
            )

        return {
            "text_id": text_id,
            "text_type": text_type,
            "embedding_dim": len(embedding),
            "status": "stored",
        }

    except Exception as e:
        logger.exception(f"Embedding task failed: {text_id}")
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="workers.tasks.batch_analyse",
    max_retries=1,
)
def batch_analyse_task(
    self,
    resume_texts: list,
    job_text: str,
    batch_id: str,
) -> Dict[str, Any]:
    """
    Analyse multiple resumes against one job description.
    Returns ranked list of results.

    Used for: recruiter feature — upload 10 resumes, rank them all.
    """
    try:
        from core.scorer import compute_match_score

        results = []
        total = len(resume_texts)

        for i, resume_text in enumerate(resume_texts):
            self.update_state(
                state="PROGRESS",
                meta={
                    "step": f"Analysing resume {i+1} of {total}...",
                    "batch_id": batch_id,
                    "progress": round((i / total) * 100),
                }
            )

            analysis_id = str(uuid.uuid4())
            result = compute_match_score(resume_text, job_text)
            result["analysis_id"] = analysis_id
            results.append({
                "analysis_id": analysis_id,
                "match_percentage": result["match_percentage"],
                "match_label": result["match_label"],
                "matched_skills": result["skill_analysis"]["matched_skills"],
                "missing_skills": result["skill_analysis"]["missing_skills"],
                "seniority": result["explanation"]["seniority"]["level"],
                "recruiter_verdict": result["explanation"]["recruiter_verdict"],
            })

        # Sort by match percentage descending
        results.sort(key=lambda x: x["match_percentage"], reverse=True)

        return {
            "batch_id": batch_id,
            "total": total,
            "results": results,
        }

    except Exception as e:
        logger.exception(f"Batch analysis failed: {batch_id}")
        raise self.retry(exc=e)