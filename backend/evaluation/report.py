"""
Evaluation Report Formatter
-----------------------------
Formats evaluation results into a clean, readable report.
Used for the API response and README generation.
"""
from typing import Dict


def format_report(eval_results: Dict) -> Dict:
    """
    Format raw evaluation results into a clean report.
    """
    improvements = eval_results["improvements"]

    # Find the best improvement
    best_metric = max(
        improvements.items(),
        key=lambda x: x[1]["improvement_pct"]
    )

    # Key headline metrics
    ndcg5_tfidf  = improvements.get("ndcg@5", {}).get("tfidf", 0)
    ndcg5_hybrid = improvements.get("ndcg@5", {}).get("hybrid", 0)
    ndcg5_improvement = improvements.get("ndcg@5", {}).get("improvement_pct", 0)

    map_tfidf    = improvements.get("MAP", {}).get("tfidf", 0)
    map_hybrid   = improvements.get("MAP", {}).get("hybrid", 0)
    map_improvement = improvements.get("MAP", {}).get("improvement_pct", 0)

    headline = (
        f"Hybrid system (TF-IDF + SBERT + Skill) achieves NDCG@5 of {ndcg5_hybrid} "
        f"vs {ndcg5_tfidf} for TF-IDF baseline — "
        f"a {ndcg5_improvement}% improvement. "
        f"MAP: {map_hybrid} vs {map_tfidf} ({map_improvement}% improvement)."
    )

    return {
        "headline": headline,
        "summary": {
            "num_queries": eval_results["num_queries"],
            "num_candidates": eval_results["num_candidates"],
            "runtime_seconds": eval_results["runtime_seconds"],
        },
        "key_metrics": {
            "ndcg@5": {
                "tfidf_baseline": ndcg5_tfidf,
                "hybrid_system": ndcg5_hybrid,
                "improvement_pct": ndcg5_improvement,
            },
            "map": {
                "tfidf_baseline": map_tfidf,
                "hybrid_system": map_hybrid,
                "improvement_pct": map_improvement,
            },
        },
        "all_improvements": improvements,
        "per_query_breakdown": eval_results["per_query"],
        "interpretation": {
            "ndcg": "Measures ranking quality — higher means relevant candidates ranked higher",
            "map": "Mean Average Precision — overall retrieval quality across all queries",
            "precision": "Of top-k results, what fraction are relevant candidates?",
            "recall": "Of all relevant candidates, what fraction appear in top-k?",
            "mrr": "How high is the first relevant candidate ranked on average?",
        }
    }