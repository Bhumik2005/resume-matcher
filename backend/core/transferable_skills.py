"""
Transferable Skill Intelligence
---------------------------------
Uses SBERT embeddings to discover semantic relationships between skills.

Key insight: Skills that are semantically close in embedding space
are transferable — a candidate with one likely has aptitude for the other.

No hardcoded rules. Pure ML.

Example discoveries:
  "statistical analysis" ↔ "data science" (0.82 similarity)
  "project coordination" ↔ "operations management" (0.79 similarity)
  "customer retention"   ↔ "marketing strategy" (0.71 similarity)
  "rest api"             ↔ "microservices" (0.88 similarity)
  "pytorch"              ↔ "tensorflow" (0.91 similarity)

Applications:
  1. Skill gap softening — missing skill X but have similar skill Y
  2. Career path suggestions — "you have these skills, consider these roles"
  3. Candidate ranking — give partial credit for transferable skills
  4. Resume suggestions — "mention X because you have Y"
"""
import logging
import numpy as np
from typing import List, Dict, Tuple, Set
from functools import lru_cache

from core.embeddings import get_embedding
from core.skill_extractor import SKILL_VOCABULARY
from core.config import settings

logger = logging.getLogger(__name__)

# Similarity threshold — skills above this are considered transferable
TRANSFERABLE_THRESHOLD = 0.30

# Cache for skill embeddings — computed once, reused forever
_skill_embedding_cache: Dict[str, np.ndarray] = {}


def _get_skill_embedding(skill: str) -> np.ndarray:
    """Get embedding for a single skill term with caching."""
    if skill not in _skill_embedding_cache:
        _skill_embedding_cache[skill] = get_embedding(skill, settings.SBERT_MODEL)
    return _skill_embedding_cache[skill]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two unit vectors."""
    # Embeddings are already normalized in get_embedding()
    return float(np.dot(a, b))


def find_related_skills(
    skill: str,
    candidate_skills: List[str],
    top_k: int = 5,
    threshold: float = TRANSFERABLE_THRESHOLD,
) -> List[Dict]:
    """Find skills semantically related to a given skill."""
    if not candidate_skills:
        return []

    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.SBERT_MODEL)

        # Encode skill and all candidates in one batch
        all_terms = [skill.lower()] + [c.lower() for c in candidate_skills]
        embeddings = model.encode(all_terms, show_progress_bar=False, batch_size=64)

        skill_emb = embeddings[0]
        results = []

        for i, candidate in enumerate(candidate_skills):
            if candidate.lower() == skill.lower():
                continue
            candidate_emb = embeddings[i + 1]

            # Proper cosine similarity
            norm_a = np.linalg.norm(skill_emb)
            norm_b = np.linalg.norm(candidate_emb)
            if norm_a == 0 or norm_b == 0:
                continue
            similarity = float(np.dot(skill_emb, candidate_emb) / (norm_a * norm_b))

            if similarity >= threshold:
                results.append({
                    "skill": candidate,
                    "similarity": round(similarity, 3),
                    "relationship": _classify_relationship(similarity),
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    except Exception as e:
        logger.error(f"find_related_skills failed: {e}")
        return []

def _classify_relationship(similarity: float) -> str:
    """Classify the strength of skill relationship."""
    if similarity >= 0.45:
        return "equivalent"
    elif similarity >= 0.38:
        return "strongly_related"
    elif similarity >= 0.33:
        return "related"
    else:
        return "transferable"    # adjacent domain


def analyze_transferable_skills(
    resume_skills: List[str],
    missing_skills: List[str],
    threshold: float = TRANSFERABLE_THRESHOLD,
) -> Dict:
    """
    For each missing skill, check if the candidate has a transferable skill.

    This is the core feature — instead of just saying "you're missing X",
    we say "you're missing X but you have Y which is 83% similar".

    Args:
        resume_skills:  Skills found in the resume
        missing_skills: Skills required by JD but not in resume

    Returns:
        {
          "fully_covered":     [...],  # missing skills with strong transfer
          "partially_covered": [...],  # missing skills with weak transfer
          "no_transfer":       [...],  # missing skills with nothing related
          "transfer_map":      {...},  # detailed mapping
          "effective_gap":     float,  # adjusted gap after transfers
        }
    """
    fully_covered = []
    partially_covered = []
    no_transfer = []
    transfer_map = {}

    for missing_skill in missing_skills:
        related = find_related_skills(
            missing_skill,
            resume_skills,
            top_k=3,
            threshold=threshold,
        )

        if related:
            best_match = related[0]
            transfer_map[missing_skill] = related

            if best_match["similarity"] >= 0.80:
                fully_covered.append({
                    "missing_skill": missing_skill,
                    "covered_by": best_match["skill"],
                    "similarity": best_match["similarity"],
                    "relationship": best_match["relationship"],
                    "message": f"You have '{best_match['skill']}' which covers '{missing_skill}' ({round(best_match['similarity']*100)}% similar)",
                })
            else:
                partially_covered.append({
                    "missing_skill": missing_skill,
                    "covered_by": best_match["skill"],
                    "similarity": best_match["similarity"],
                    "relationship": best_match["relationship"],
                    "message": f"'{best_match['skill']}' partially covers '{missing_skill}' ({round(best_match['similarity']*100)}% similar) — mention this connection in your cover letter",
                })
        else:
            no_transfer.append({
                "missing_skill": missing_skill,
                "message": f"No transferable skill found for '{missing_skill}' — this is a genuine gap to address",
            })

    # Adjusted gap score
    total_missing = len(missing_skills)
    if total_missing > 0:
        covered_weight = len(fully_covered) * 1.0 + len(partially_covered) * 0.5
        effective_gap = round(1.0 - (covered_weight / total_missing), 3)
    else:
        effective_gap = 0.0

    return {
        "fully_covered": fully_covered,
        "partially_covered": partially_covered,
        "no_transfer": no_transfer,
        "transfer_map": {k: v for k, v in transfer_map.items()},
        "effective_gap": effective_gap,
        "summary": {
            "total_missing": total_missing,
            "fully_covered_count": len(fully_covered),
            "partially_covered_count": len(partially_covered),
            "genuine_gaps_count": len(no_transfer),
        }
    }


def build_skill_graph(
    skills: List[str],
    threshold: float = TRANSFERABLE_THRESHOLD,
) -> Dict:
    """
    Build a full skill similarity graph for a set of skills.
    Each skill is connected to all others above the threshold.

    Used for:
    - Visualizing skill relationships in the frontend
    - Career path suggestions
    - Skill clustering

    Args:
        skills: List of skills to build graph for
        threshold: Minimum similarity for an edge

    Returns:
        {
          "nodes": [{"id": str, "skill": str}],
          "edges": [{"source": str, "target": str, "similarity": float}],
          "clusters": {...}
        }
    """
    nodes = [{"id": skill, "skill": skill} for skill in skills]
    edges = []

    for i, skill_a in enumerate(skills):
        for skill_b in skills[i+1:]:
            emb_a = _get_skill_embedding(skill_a.lower())
            emb_b = _get_skill_embedding(skill_b.lower())
            similarity = _cosine_similarity(emb_a, emb_b)

            if similarity >= threshold:
                edges.append({
                    "source": skill_a,
                    "target": skill_b,
                    "similarity": round(similarity, 3),
                    "relationship": _classify_relationship(similarity),
                })

    edges.sort(key=lambda x: x["similarity"], reverse=True)

    return {
        "nodes": nodes,
        "edges": edges,
        "edge_count": len(edges),
        "avg_similarity": round(
            sum(e["similarity"] for e in edges) / len(edges), 3
        ) if edges else 0.0,
    }


def get_career_suggestions(
    resume_skills: List[str],
    top_k: int = 5,
) -> List[Dict]:
    """
    Based on resume skills, suggest what other skills the candidate
    would find easiest to learn next — highest semantic proximity.

    This is the career path feature:
    "You have PyTorch — you'd find TensorFlow easy to pick up (91% similar)"

    Args:
        resume_skills: Skills the candidate already has
        top_k:         Number of suggestions per skill

    Returns:
        List of skill suggestions with reasoning
    """
    # Skills in vocabulary not already in resume
    all_vocab_skills = list(SKILL_VOCABULARY)
    missing_from_vocab = [s for s in all_vocab_skills if s not in resume_skills]

    suggestions = []
    seen = set()

    for resume_skill in resume_skills[:10]:  # limit to top 10 resume skills
        related = find_related_skills(
            resume_skill,
            missing_from_vocab,
            top_k=3,
            threshold=0.30,
        )
        for rel in related:
            if rel["skill"] not in seen:
                seen.add(rel["skill"])
                suggestions.append({
                    "suggested_skill": rel["skill"],
                    "because_you_have": resume_skill,
                    "similarity": rel["similarity"],
                    "relationship": rel["relationship"],
                    "reason": f"You already know '{resume_skill}' — '{rel['skill']}' is {round(rel['similarity']*100)}% semantically similar and would be fast to learn.",
                })

    suggestions.sort(key=lambda x: x["similarity"], reverse=True)
    return suggestions[:top_k]