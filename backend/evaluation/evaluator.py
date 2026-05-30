"""
Evaluation Pipeline
--------------------
Runs the full benchmark evaluation:

1. For each query in benchmark_data:
   a. Score all candidate resumes against the JD
   b. Rank candidates by score
   c. Compare ranking to ground truth relevance labels
   d. Compute NDCG, Precision, Recall, MRR

2. Compare two systems:
   a. TF-IDF only (baseline)
   b. Full hybrid (TF-IDF + SBERT + Skill) — our system

3. Generate evaluation report
"""
import logging
import time
from typing import Dict, List, Any

from evaluation.benchmark_data import get_benchmark_queries
from evaluation.metrics import (
    compute_all_metrics,
    mean_reciprocal_rank,
    ndcg_at_k,
)
from core.tfidf_scorer import get_tfidf_score
from core.sbert_scorer import get_sbert_score
from core.skill_extractor import get_skill_gap_analysis
from core.config import settings

logger = logging.getLogger(__name__)


def score_with_tfidf_only(resume_text: str, job_text: str) -> float:
    """Baseline: TF-IDF only scoring."""
    score, _ = get_tfidf_score(resume_text, job_text)
    return score


def score_with_hybrid(resume_text: str, job_text: str) -> float:
    """Our full hybrid system: TF-IDF + SBERT + Skill."""
    tfidf_score, _ = get_tfidf_score(resume_text, job_text)
    sbert_score = get_sbert_score(resume_text, job_text, settings.SBERT_MODEL)
    skill_analysis = get_skill_gap_analysis(resume_text, job_text)
    skill_score = skill_analysis["score"]

    return (
        tfidf_score * settings.TFIDF_WEIGHT +
        sbert_score * settings.SBERT_WEIGHT +
        skill_score * settings.SKILL_WEIGHT
    )


def evaluate_single_query(
    query: Dict,
    scoring_fn,
) -> Dict:
    """
    Evaluate one query against all its candidates.

    Returns dict with:
      - scores: raw scores per candidate
      - ranking: candidates sorted by score
      - metrics: precision, recall, ndcg, mrr
    """
    job_text = query["job_description"]
    candidates = query["candidates"]

    # Score all candidates
    scored = []
    for candidate in candidates:
        score = scoring_fn(candidate["resume"], job_text)
        scored.append({
            "id": candidate["id"],
            "relevance": candidate["relevance"],
            "score": round(score, 4),
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Build inputs for metrics
    retrieved_ids = [c["id"] for c in scored]
    relevance_scores = [c["relevance"] / 3.0 for c in scored]  # normalize to 0-1
    relevant_ids = [c["id"] for c in candidates if c["relevance"] >= 2]  # relevant = score 2 or 3

    metrics = compute_all_metrics(
        relevance_scores=relevance_scores,
        relevant_ids=relevant_ids,
        retrieved_ids=retrieved_ids,
        k_values=[1, 3, 5],
    )

    return {
        "query_id": query["query_id"],
        "ranking": scored,
        "metrics": metrics,
    }


def run_full_evaluation() -> Dict:
    """
    Run complete evaluation comparing TF-IDF baseline vs hybrid system.

    Returns:
        {
          "tfidf_baseline": {...metrics...},
          "hybrid_system":  {...metrics...},
          "improvement":    {...percentage improvements...},
          "per_query":      {...per-query breakdowns...},
          "runtime_seconds": float,
        }
    """
    logger.info("Starting full evaluation pipeline...")
    start_time = time.time()

    queries = get_benchmark_queries()
    k_values = [1, 3, 5]

    tfidf_results = []
    hybrid_results = []
    per_query = []

    for query in queries:
        logger.info(f"Evaluating query {query['query_id']}...")

        # TF-IDF baseline
        tfidf_result = evaluate_single_query(query, score_with_tfidf_only)
        tfidf_results.append(tfidf_result)

        # Hybrid system
        hybrid_result = evaluate_single_query(query, score_with_hybrid)
        hybrid_results.append(hybrid_result)

        per_query.append({
            "query_id": query["query_id"],
            "tfidf": tfidf_result["metrics"],
            "hybrid": hybrid_result["metrics"],
            "tfidf_ranking": tfidf_result["ranking"],
            "hybrid_ranking": hybrid_result["ranking"],
        })

    # Aggregate metrics across all queries
    def aggregate_metrics(results, k_values):
        all_metrics = [r["metrics"] for r in results]
        aggregated = {}
        for k in k_values:
            for metric in ["precision", "recall", "f1", "ndcg"]:
                key = f"{metric}@{k}"
                values = [m[key] for m in all_metrics]
                aggregated[key] = round(sum(values) / len(values), 4)
        ap_values = [m["average_precision"] for m in all_metrics]
        aggregated["MAP"] = round(sum(ap_values) / len(ap_values), 4)
        return aggregated

    tfidf_agg = aggregate_metrics(tfidf_results, k_values)
    hybrid_agg = aggregate_metrics(hybrid_results, k_values)

    # Compute improvements
    improvements = {}
    for key in tfidf_agg:
        baseline = tfidf_agg[key]
        ours = hybrid_agg[key]
        if baseline > 0:
            pct_improvement = round(((ours - baseline) / baseline) * 100, 1)
        else:
            pct_improvement = 0.0
        improvements[key] = {
            "tfidf": baseline,
            "hybrid": ours,
            "improvement_pct": pct_improvement,
        }

    runtime = round(time.time() - start_time, 2)
    logger.info(f"Evaluation complete in {runtime}s")

    return {
        "tfidf_baseline": tfidf_agg,
        "hybrid_system": hybrid_agg,
        "improvements": improvements,
        "per_query": per_query,
        "runtime_seconds": runtime,
        "num_queries": len(queries),
        "num_candidates": sum(len(q["candidates"]) for q in queries),
    }