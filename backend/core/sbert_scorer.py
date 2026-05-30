import logging
import re
from typing import List
import numpy as np

logger = logging.getLogger(__name__)
_model_cache = {}

def _get_model(model_name: str):
    if model_name not in _model_cache:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SBERT model: {model_name}")
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]

def _split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = [s.strip() for s in sentences if len(s.split()) >= 5]
    return sentences if sentences else [text]

def _mean_pool(embeddings: np.ndarray) -> np.ndarray:
    return np.mean(embeddings, axis=0)

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def get_sbert_score(resume_text: str, job_text: str, model_name: str = "all-MiniLM-L6-v2") -> float:
    model = _get_model(model_name)
    resume_sentences = _split_into_sentences(resume_text)
    job_sentences = _split_into_sentences(job_text)
    resume_emb = model.encode(resume_sentences, show_progress_bar=False, batch_size=32)
    job_emb = model.encode(job_sentences, show_progress_bar=False, batch_size=32)
    score = _cosine_sim(_mean_pool(resume_emb), _mean_pool(job_emb))
    normalised = max(0.0, min(1.0, (score - 0.3) / 0.6))
    return round(normalised, 4)

def get_section_sbert_scores(resume_sections: dict, job_text: str, model_name: str = "all-MiniLM-L6-v2") -> dict:
    scores = {}
    for section_name, section_text in resume_sections.items():
        if section_text and len(section_text.split()) > 10:
            scores[section_name] = get_sbert_score(section_text, job_text, model_name)
        else:
            scores[section_name] = 0.0
    return scores