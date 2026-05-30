import re
import logging
from typing import Set, Dict

logger = logging.getLogger(__name__)

SKILL_VOCABULARY: Set[str] = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "scala", "kotlin", "swift", "r", "matlab", "julia", "ruby", "php",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "xgboost",
    "lightgbm", "catboost", "hugging face", "transformers", "langchain",
    "openai", "llm", "gpt", "bert", "sbert", "sentence-transformers",
    "spacy", "nltk", "gensim", "fasttext", "word2vec",
    "mlflow", "wandb", "dvc", "kubeflow", "airflow", "prefect", "ray",
    "dask", "spark", "pyspark",
    "sql", "postgresql", "mysql", "sqlite", "mongodb", "redis",
    "elasticsearch", "cassandra", "bigquery", "snowflake", "redshift",
    "databricks", "pandas", "numpy", "scipy", "polars",
    "aws", "gcp", "azure", "s3", "ec2", "lambda", "sagemaker",
    "google cloud", "vertex ai", "azure ml",
    "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
    "github actions", "circleci", "gitlab ci", "ci/cd",
    "linux", "bash", "shell scripting",
    "fastapi", "flask", "django", "rest api", "graphql", "grpc",
    "microservices", "celery", "rabbitmq", "kafka",
    "react", "vue", "angular", "html", "css", "tailwind",
    "matplotlib", "seaborn", "plotly", "tableau", "power bi",
    "git", "github", "gitlab", "bitbucket",
    "machine learning", "deep learning", "nlp", "computer vision",
    "reinforcement learning", "supervised learning", "unsupervised learning",
    "time series", "anomaly detection", "recommendation systems",
    "a/b testing", "statistics", "probability",
    "data engineering", "etl", "feature engineering", "model deployment",
    "model monitoring", "explainability", "xai",
    "agile", "scrum", "kanban", "jira", "confluence",
}

_VOCAB_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in sorted(SKILL_VOCABULARY, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

_nlp_cache = {}

def _get_nlp(model_name: str = "en_core_web_sm"):
    if model_name not in _nlp_cache:
        import spacy
        _nlp_cache[model_name] = spacy.load(model_name)
    return _nlp_cache[model_name]

def extract_skills_vocabulary(text: str) -> Set[str]:
    return {m.lower() for m in _VOCAB_PATTERN.findall(text)}

def extract_skills_spacy(text: str, model_name: str = "en_core_web_sm") -> Set[str]:
    try:
        nlp = _get_nlp(model_name)
        doc = nlp(text[:100_000])
        skills = set()
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT", "GPE", "LANGUAGE"):
                term = ent.text.lower().strip()
                if 2 <= len(term.split()) <= 4 and len(term) >= 3:
                    skills.add(term)
        for chunk in doc.noun_chunks:
            if chunk.root.pos_ in ("NOUN", "PROPN") and not chunk.root.is_stop:
                term = chunk.text.lower().strip()
                if 1 <= len(term.split()) <= 4 and len(term) >= 3:
                    skills.add(term)
        return skills
    except Exception as e:
        logger.warning(f"spaCy extraction failed: {e}")
        return set()

def extract_skills(text: str, model_name: str = "en_core_web_sm") -> Set[str]:
    return extract_skills_vocabulary(text) | extract_skills_spacy(text, model_name)

def get_skill_gap_analysis(resume_text: str, job_text: str, model_name: str = "en_core_web_sm") -> Dict:
    resume_skills = extract_skills(resume_text, model_name)
    jd_skills = extract_skills(job_text, model_name)
    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    extra = resume_skills - jd_skills
    score = len(matched) / len(jd_skills) if jd_skills else 0.0
    return {
        "score": round(score, 4),
        "resume_skills": sorted(resume_skills & SKILL_VOCABULARY),
        "jd_skills": sorted(jd_skills & SKILL_VOCABULARY),
        "matched_skills": sorted(matched & SKILL_VOCABULARY),
        "missing_skills": sorted(missing & SKILL_VOCABULARY),
        "extra_skills": sorted(extra & SKILL_VOCABULARY),
    }