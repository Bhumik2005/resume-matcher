from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000", "http://localhost:5173"]
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/resume_matcher"
    SBERT_MODEL: str = "all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    TFIDF_WEIGHT: float = 0.30
    SBERT_WEIGHT: float = 0.50
    SKILL_WEIGHT: float = 0.20
    MAX_PDF_SIZE_MB: int = 10
    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    # PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/resume_matcher"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()