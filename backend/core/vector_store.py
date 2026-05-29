"""
Qdrant Vector Store
--------------------
Handles all interactions with the Qdrant vector database.

Collections:
  - resumes     : resume embeddings + metadata
  - job_descriptions : JD embeddings + metadata

Key operations:
  - store_resume()         : save resume embedding
  - store_job()            : save JD embedding
  - search_similar_resumes(): find semantically similar resumes
  - search_similar_jobs()  : find semantically similar jobs
  - get_resume()           : retrieve by ID
"""
import logging
import uuid
from typing import List, Optional, Dict, Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    ScoredPoint,
)

from core.embeddings import get_embedding, get_embedding_dimension
from core.config import settings

logger = logging.getLogger(__name__)

# Collection names
RESUMES_COLLECTION     = "resumes"
JOBS_COLLECTION        = "job_descriptions"
DIMENSION              = get_embedding_dimension(settings.SBERT_MODEL)

# Module-level client cache
_client: Optional[QdrantClient] = None


def get_client() -> QdrantClient:
    """Get or create the Qdrant client (singleton)."""
    global _client
    if _client is None:
        _client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        logger.info(f"Qdrant client connected: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    return _client


def init_collections() -> None:
    """
    Create Qdrant collections if they don't exist.
    Called once on API startup.
    """
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    for collection_name in [RESUMES_COLLECTION, JOBS_COLLECTION]:
        if collection_name not in existing:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
        else:
            logger.info(f"Qdrant collection already exists: {collection_name}")


def store_resume(
    resume_text: str,
    metadata: Dict[str, Any],
    resume_id: Optional[str] = None,
) -> str:
    """
    Generate embedding for resume text and store in Qdrant.

    Args:
        resume_text: Cleaned resume text
        metadata:    Dict of metadata to store alongside vector
                     (skills, score, label, word_count, etc.)
        resume_id:   Optional UUID — generated if not provided

    Returns:
        resume_id (str)
    """
    if resume_id is None:
        resume_id = str(uuid.uuid4())

    embedding = get_embedding(resume_text, settings.SBERT_MODEL)

    client = get_client()
    client.upsert(
        collection_name=RESUMES_COLLECTION,
        points=[
            PointStruct(
                id=resume_id,
                vector=embedding.tolist(),
                payload={
                    **metadata,
                    "resume_id": resume_id,
                    # Never store raw resume text — PII risk
                    "text_snippet": resume_text[:200],
                }
            )
        ]
    )

    logger.info(f"Stored resume embedding: {resume_id}")
    return resume_id


def store_job(
    job_text: str,
    metadata: Dict[str, Any],
    job_id: Optional[str] = None,
) -> str:
    """Store job description embedding in Qdrant."""
    if job_id is None:
        job_id = str(uuid.uuid4())

    embedding = get_embedding(job_text, settings.SBERT_MODEL)

    client = get_client()
    client.upsert(
        collection_name=JOBS_COLLECTION,
        points=[
            PointStruct(
                id=job_id,
                vector=embedding.tolist(),
                payload={
                    **metadata,
                    "job_id": job_id,
                    "text_snippet": job_text[:200],
                }
            )
        ]
    )

    logger.info(f"Stored job embedding: {job_id}")
    return job_id


def search_similar_resumes(
    query_text: str,
    top_k: int = 5,
    score_threshold: float = 0.5,
    filters: Optional[Dict] = None,
) -> List[Dict]:
    """
    Find the most semantically similar resumes to a query.

    Args:
        query_text:      Text to search against (e.g. a job description)
        top_k:           Number of results to return
        score_threshold: Minimum cosine similarity (0-1)
        filters:         Optional metadata filters

    Returns:
        List of dicts with resume_id, score, and metadata
    """
    query_embedding = get_embedding(query_text, settings.SBERT_MODEL)
    client = get_client()

    qdrant_filter = None
    if filters:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filters.items()
        ]
        qdrant_filter = Filter(must=conditions)

    results = client.search(
        collection_name=RESUMES_COLLECTION,
        query_vector=query_embedding.tolist(),
        limit=top_k,
        score_threshold=score_threshold,
        query_filter=qdrant_filter,
        with_payload=True,
    )

    return [
        {
            "resume_id": r.payload.get("resume_id"),
            "score": round(r.score, 4),
            "match_percentage": round(r.score * 100, 1),
            "metadata": r.payload,
        }
        for r in results
    ]


def search_similar_jobs(
    query_text: str,
    top_k: int = 5,
    score_threshold: float = 0.5,
) -> List[Dict]:
    """Find job descriptions semantically similar to a resume or query."""
    query_embedding = get_embedding(query_text, settings.SBERT_MODEL)
    client = get_client()

    results = client.search(
        collection_name=JOBS_COLLECTION,
        query_vector=query_embedding.tolist(),
        limit=top_k,
        score_threshold=score_threshold,
        with_payload=True,
    )

    return [
        {
            "job_id": r.payload.get("job_id"),
            "score": round(r.score, 4),
            "match_percentage": round(r.score * 100, 1),
            "metadata": r.payload,
        }
        for r in results
    ]


def get_collection_stats() -> Dict:
    """Return stats about both collections — used in health check."""
    client = get_client()
    stats = {}
    for name in [RESUMES_COLLECTION, JOBS_COLLECTION]:
        try:
            info = client.get_collection(name)
            stats[name] = {
                "status": str(info.status.value),
                "points_count": info.points_count or 0,
                "indexed_vectors_count": info.indexed_vectors_count or 0,
            }
        except Exception as e:
            stats[name] = {"error": str(e)}
    return stats