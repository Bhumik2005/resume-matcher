import uuid
import logging
from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
from core.config import settings
from core.pdf_extractor import extract_text_from_pdf
from core.scorer import compute_match_score
from models.schemas import MatchResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()
MAX_BYTES = settings.MAX_PDF_SIZE_MB * 1024 * 1024

@router.post("/match", response_model=MatchResponse)
async def match_resume(
    resume: Annotated[UploadFile, File()],
    job_description: Annotated[str, Form()],
):
    if resume.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await resume.read()

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    if len(pdf_bytes) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"PDF exceeds {settings.MAX_PDF_SIZE_MB}MB limit.")
    if len(job_description.strip()) < 50:
        raise HTTPException(status_code=400, detail="Job description too short. Paste the full JD.")

    try:
        resume_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to process PDF.")

    try:
        result = compute_match_score(resume_text, job_description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    result["analysis_id"] = str(uuid.uuid4())
    return MatchResponse(**result)