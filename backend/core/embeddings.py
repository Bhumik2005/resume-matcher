"""
Embedding Generation & Caching
--------------------------------
Centralizes all embedding generation so we never
compute the same embedding twice.

Used by:
- vector_store.py (storing embeddings in Qdrant)
- sbert_scorer.py (scoring)
"""
import hashlib
import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

# In-memory cache: hash → embedding
# Persisted version lives in Qdrant
_embedding_cache: dict = {}
_model_cache: dict = {}


def _get_model(model_name: str = "all-MiniLM-L6-v2"):
    if model_name not in _model_cache:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SBERT model: {model_name}")
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]


def _hash_text(text: str) -> str:
    """SHA256 hash of text — used as cache key."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def get_embedding(
    text: str,
    model_name: str = "all-MiniLM-L6-v2",
) -> np.ndarray:
    """
    Generate a single document embedding with in-memory caching.
    For short texts (skills), encodes directly.
    For long texts (resumes), uses sentence-level mean pooling.
    """
    cache_key = f"{model_name}:{_hash_text(text)}"

    if cache_key in _embedding_cache:
        logger.debug("Embedding cache hit")
        return _embedding_cache[cache_key]

    model = _get_model(model_name)

    # Short text (skill terms, phrases) — encode directly
    if len(text.split()) <= 8:
        doc_embedding = model.encode(text, show_progress_bar=False)
    else:
        # Long text (resumes, JDs) — sentence-level mean pooling
        import re
        sentences = re.split(r"(?<=[.!?\n])\s*", text)
        sentences = [s.strip() for s in sentences if len(s.split()) >= 5]
        if not sentences:
            sentences = [text]
        embeddings = model.encode(sentences, show_progress_bar=False, batch_size=32)
        doc_embedding = np.mean(embeddings, axis=0)

    # Normalize to unit vector
    norm = np.linalg.norm(doc_embedding)
    if norm > 0:
        doc_embedding = doc_embedding / norm

    _embedding_cache[cache_key] = doc_embedding
    return doc_embedding


def get_embeddings_batch(
    texts: List[str],
    model_name: str = "all-MiniLM-L6-v2",
) -> List[np.ndarray]:
    """Batch embedding generation — more efficient than one at a time."""
    return [get_embedding(t, model_name) for t in texts]


def get_embedding_dimension(model_name: str = "all-MiniLM-L6-v2") -> int:
    """Return the embedding dimension for a given model."""
    dimensions = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "BAAI/bge-large-en": 1024,
    }
    return dimensions.get(model_name, 384)