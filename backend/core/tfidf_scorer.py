import re
import logging
from typing import Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def get_tfidf_score(resume_text: str, job_text: str) -> Tuple[float, list]:
    resume_clean = preprocess(resume_text)
    job_clean = preprocess(job_text)

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        stop_words="english",
        min_df=1,
        sublinear_tf=True,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([resume_clean, job_clean])
    except ValueError as e:
        logger.error(f"TF-IDF failed: {e}")
        return 0.0, []

    score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])

    feature_names = vectorizer.get_feature_names_out()
    job_vector = tfidf_matrix[1].toarray()[0]
    resume_vector = tfidf_matrix[0].toarray()[0]

    top_indices = np.argsort(job_vector)[::-1][:30]
    top_keywords = []
    for idx in top_indices:
        term = feature_names[idx]
        top_keywords.append({
            "term": term,
            "jd_weight": round(float(job_vector[idx]), 4),
            "in_resume": bool(resume_vector[idx] > 0),
        })
        if len(top_keywords) == 20:
            break

    return round(score, 4), top_keywords