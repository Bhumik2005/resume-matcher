"""
ML Evaluation Metrics
----------------------
Implements standard IR (Information Retrieval) metrics used to
evaluate ranking and matching systems.

Metrics:
  - Precision@k    : of top-k results, how many are relevant?
  - Recall@k       : of all relevant items, how many are in top-k?
  - NDCG@k         : Normalized Discounted Cumulative Gain — rewards
                     relevant items ranked higher
  - MRR            : Mean Reciprocal Rank — how high is the first
                     relevant result?
  - F1@k           : harmonic mean of precision and recall
  - Average Precision: area under precision-recall curve

These are the same metrics used by Google, LinkedIn, and every
serious ML ranking system.
"""
import numpy as np
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def precision_at_k(relevant: List[int], retrieved: List[int], k: int) -> float:
    """
    Precision@k — what fraction of top-k results are relevant?

    Args:
        relevant:  list of relevant item IDs (ground truth)
        retrieved: list of retrieved item IDs ordered by score
        k:         cutoff

    Returns:
        float in [0, 1]

    Example:
        relevant  = [1, 2, 3]
        retrieved = [1, 4, 2, 5, 3]
        P@3 = 2/3 = 0.667  (items 1 and 2 are relevant in top 3)
    """
    if k == 0:
        return 0.0
    top_k = retrieved[:k]
    relevant_set = set(relevant)
    hits = sum(1 for item in top_k if item in relevant_set)
    return hits / k


def recall_at_k(relevant: List[int], retrieved: List[int], k: int) -> float:
    """
    Recall@k — what fraction of relevant items appear in top-k?

    Example:
        relevant  = [1, 2, 3]
        retrieved = [1, 4, 2, 5, 3]
        R@3 = 2/3 = 0.667  (items 1 and 2 found in top 3, item 3 missed)
    """
    if not relevant:
        return 0.0
    top_k = set(retrieved[:k])
    relevant_set = set(relevant)
    hits = len(top_k & relevant_set)
    return hits / len(relevant_set)


def f1_at_k(relevant: List[int], retrieved: List[int], k: int) -> float:
    """F1@k — harmonic mean of precision and recall at k."""
    p = precision_at_k(relevant, retrieved, k)
    r = recall_at_k(relevant, retrieved, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def dcg_at_k(relevance_scores: List[float], k: int) -> float:
    """
    Discounted Cumulative Gain@k.

    Rewards relevant items ranked higher — the discount is log2(rank+1).
    Higher ranks (position 1, 2) contribute more than lower ranks.

    Args:
        relevance_scores: relevance score for each retrieved item (in rank order)
        k:                cutoff

    Returns:
        DCG score (higher is better)
    """
    scores = relevance_scores[:k]
    return sum(
        rel / np.log2(rank + 2)  # rank+2 because rank is 0-indexed
        for rank, rel in enumerate(scores)
    )


def ndcg_at_k(relevance_scores: List[float], k: int) -> float:
    """
    Normalized DCG@k — DCG divided by ideal DCG.

    Normalizes to [0, 1] so scores are comparable across queries.
    1.0 = perfect ranking, 0.0 = worst possible ranking.

    Args:
        relevance_scores: relevance score for each retrieved item (rank order)
        k:                cutoff

    Returns:
        float in [0, 1]
    """
    actual_dcg = dcg_at_k(relevance_scores, k)
    # Ideal DCG = DCG of perfectly sorted relevance scores
    ideal_scores = sorted(relevance_scores, reverse=True)
    ideal_dcg = dcg_at_k(ideal_scores, k)
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg


def mean_reciprocal_rank(
    relevant_sets: List[List[int]],
    retrieved_lists: List[List[int]],
) -> float:
    """
    Mean Reciprocal Rank (MRR) — average of 1/rank of first relevant result.

    Used when you care about finding at least one relevant item quickly.
    MRR = 1.0 means the first result is always relevant.
    MRR = 0.5 means the first relevant result is on average at rank 2.

    Args:
        relevant_sets:   list of relevant item sets (one per query)
        retrieved_lists: list of retrieved item lists (one per query)
    """
    reciprocal_ranks = []
    for relevant, retrieved in zip(relevant_sets, retrieved_lists):
        relevant_set = set(relevant)
        rr = 0.0
        for rank, item in enumerate(retrieved, start=1):
            if item in relevant_set:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)
    return float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0


def average_precision(relevant: List[int], retrieved: List[int]) -> float:
    """
    Average Precision (AP) — area under the precision-recall curve.
    Mean of AP across queries = MAP (Mean Average Precision).
    """
    if not relevant:
        return 0.0
    relevant_set = set(relevant)
    hits = 0
    precision_sum = 0.0
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant_set:
            hits += 1
            precision_sum += hits / rank
    if hits == 0:
        return 0.0
    return precision_sum / len(relevant_set)


def compute_all_metrics(
    relevance_scores: List[float],
    relevant_ids: List[int],
    retrieved_ids: List[int],
    k_values: List[int] = [1, 3, 5, 10],
) -> Dict:
    """
    Compute all metrics at once for a single query.

    Args:
        relevance_scores: relevance score per retrieved item (0-1 scale)
        relevant_ids:     ground truth relevant item IDs
        retrieved_ids:    retrieved item IDs in rank order
        k_values:         list of k cutoffs to evaluate at

    Returns:
        Dict of all metrics
    """
    results = {}
    for k in k_values:
        results[f"precision@{k}"] = round(precision_at_k(relevant_ids, retrieved_ids, k), 4)
        results[f"recall@{k}"]    = round(recall_at_k(relevant_ids, retrieved_ids, k), 4)
        results[f"f1@{k}"]        = round(f1_at_k(relevant_ids, retrieved_ids, k), 4)
        results[f"ndcg@{k}"]      = round(ndcg_at_k(relevance_scores, k), 4)

    results["average_precision"] = round(average_precision(relevant_ids, retrieved_ids), 4)
    return results