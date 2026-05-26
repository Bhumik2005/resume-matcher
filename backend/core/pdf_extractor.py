import re
import io
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

def extract_text_pdfplumber(pdf_bytes: bytes) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
        return ""

def extract_text_pymupdf(pdf_bytes: bytes) -> str:
    try:
        import fitz
        text_parts = []
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")
        return ""

def clean_text(text: str) -> str:
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    plumber_text = extract_text_pdfplumber(pdf_bytes)
    pymupdf_text = extract_text_pymupdf(pdf_bytes)
    raw_text = plumber_text if len(plumber_text) >= len(pymupdf_text) else pymupdf_text
    if not raw_text.strip():
        raise ValueError("Could not extract text. Please upload a text-based PDF.")
    return clean_text(raw_text)

def extract_text_from_file(file_path: Union[str, Path]) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return extract_text_from_pdf(path.read_bytes())