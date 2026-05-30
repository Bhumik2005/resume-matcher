# ResumeMatch — AI-Powered Semantic Talent Intelligence Platform

> Match resumes to job descriptions using a 3-layer NLP pipeline: TF-IDF + Sentence-BERT + spaCy NER. Built as a production-grade ML system, not a toy project.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![PyTorch](https://img.shields.io/badge/PyTorch-2.3-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-purple)

---

## What Makes This Different From Every Other Resume Matcher

Most resume matchers are glorified keyword counters. This system understands **meaning**.

| Feature | Keyword Matcher | ResumeMatch |
|---|---|---|
| "Led engineering team" vs "team leadership" | ❌ No match | ✅ 91% similar |
| Detects keyword stuffing | ❌ | ✅ |
| Explains WHY score is low | ❌ | ✅ |
| Transferable skill discovery | ❌ | ✅ |
| Vector search across candidates | ❌ | ✅ |
| Async ML processing | ❌ | ✅ |

---

## ML Architecture
Resume PDF + Job Description
↓
PDF Extraction
(pdfplumber + PyMuPDF)
↓
Security Pipeline
(injection guard, stuffing detection, PII scrubber)
↓
┌────────────────────────────────────┐
│         3-Layer Scoring            │
│                                    │
│  Layer 1: TF-IDF (weight: 30%)     │
│  → Exact keyword overlap           │
│                                    │
│  Layer 2: SBERT (weight: 50%)      │
│  → Semantic similarity             │
│  → Mean pooling over sentences     │
│                                    │
│  Layer 3: spaCy NER (weight: 20%)  │
│  → Skill gap analysis              │
│  → 200+ skill vocabulary           │
└────────────────────────────────────┘
↓
Explainability Engine
→ Recruiter verdict
→ Score drivers
→ Skill context scoring
→ Seniority detection
↓
Transferable Skill Intelligence
→ SBERT embedding clustering
→ Zero hardcoded rules
↓
Qdrant Vector Storage
→ Embeddings persisted
→ Semantic candidate search
↓
PostgreSQL
→ Analysis history
→ User accounts

---

## Evaluation Results

Benchmarked against 3 query types and 12 labeled candidates:

| Metric | TF-IDF Baseline | Hybrid System | Improvement |
|--------|----------------|---------------|-------------|
| NDCG@1 | 0.889 | **1.000** | +12.5% |
| NDCG@5 | 0.965 | **0.991** | +2.7% |
| MAP | 0.944 | **0.944** | — |

**Key finding:** On the NLP Engineer query, TF-IDF ranked the wrong candidate #1 due to keyword frequency bias. The hybrid SBERT system correctly identified the strongest candidate by understanding semantic context.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML/NLP | PyTorch, Sentence-Transformers (SBERT), spaCy, scikit-learn |
| Embeddings | all-MiniLM-L6-v2 (384-dim, mean pooled) |
| Vector DB | Qdrant (cosine similarity, ANN search) |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Async ML | Celery + Redis |
| Auth | JWT (python-jose) + bcrypt |
| Database | PostgreSQL |
| Frontend | React + Vite + Framer Motion |
| Containerization | Docker + docker-compose |
| Monitoring | Flower (Celery dashboard) |
| Security | Rate limiting, prompt injection guard, PII scrubber, keyword stuffing detector |

---

## ML Engineering Highlights

### 1. Semantic Skill Intelligence (Zero Rules)
```python
# SBERT discovers that pytorch ↔ tensorflow (0.486 similarity)
# No hardcoded mappings — pure embedding geometry
result = find_related_skills("pytorch", SKILL_VOCABULARY)
# → [{"skill": "tensorflow", "similarity": 0.486, "relationship": "equivalent"},
#    {"skill": "numpy", "similarity": 0.456, "relationship": "equivalent"}]
```

### 2. Explainable AI — Not Just a Score
```json
{
  "recruiter_verdict": "Strong candidate. This senior-level resume closely matches...",
  "score_drivers": {
    "top_boosters": ["Strong semantic alignment (SBERT: 79%)"],
    "top_detractors": ["Missing skills: kubernetes, terraform"],
    "biggest_gap": "Adding 'kubernetes' would have highest single impact"
  },
  "skill_contexts": [
    {
      "skill": "pytorch",
      "strength": "strong",
      "reason": "Backed by action verb 'built' — indicates real experience"
    }
  ]
}
```

### 3. Anti-Cheat Security
```python
# Detects keyword stuffing, prompt injection, hidden text
security_report = run_security_checks(pdf_bytes, resume_text, job_text)
# → stuffing_detected: True, flagged_terms: ["python x12", "docker x9"]
```

### 4. Async ML Pipeline
API receives request → returns task_id in <100ms
↓
Celery worker picks up task from Redis
↓
SBERT inference runs in background
↓
Result stored → client polls /task/{id}

---

-GitHub: https://github.com/Bhumik2005/resume-matcher
-Live API: https://resume-matcher-api-u3rf.onrender.com/docs
-Health check: https://resume-matcher-api-u3rf.onrender.com/health

## Quickstart

### Prerequisites
- Docker Desktop
- Git

### Run the entire stack with one command
```bash
git clone https://github.com/Bhumik2005/resume-matcher.git
cd resume-matcher
docker-compose up
```

That's it. All 7 services start automatically:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:80 |
| API docs | http://localhost:8000/docs |
| Qdrant dashboard | http://localhost:6333/dashboard |
| Flower monitoring | http://localhost:5555 |

### Local development (without Docker)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload --port 8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/match` | Analyse resume vs JD (sync) |
| POST | `/api/v1/match/async` | Submit analysis as async task |
| GET | `/api/v1/task/{id}` | Poll async task result |
| POST | `/api/v1/batch` | Rank multiple resumes vs one JD |
| GET | `/api/v1/search` | Semantic resume search via Qdrant |
| GET | `/api/v1/skills/related` | Find related skills via embeddings |
| GET | `/api/v1/skills/graph` | Build skill similarity graph |
| GET | `/api/v1/evaluate` | Run NDCG/Precision/Recall benchmark |
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT token |
| GET | `/api/v1/auth/history` | User analysis history |

---

## Project Structure
resume-matcher/
├── backend/
│   ├── api/
│   │   ├── routes.py          # Main API endpoints
│   │   └── auth_routes.py     # Auth endpoints
│   ├── core/
│   │   ├── tfidf_scorer.py    # Layer 1: TF-IDF
│   │   ├── sbert_scorer.py    # Layer 2: SBERT semantic
│   │   ├── skill_extractor.py # Layer 3: spaCy NER
│   │   ├── scorer.py          # Weighted orchestrator
│   │   ├── explainer.py       # Explainability engine
│   │   ├── transferable_skills.py # Embedding-based skill mapping
│   │   ├── vector_store.py    # Qdrant operations
│   │   ├── embeddings.py      # Embedding generation + cache
│   │   └── security.py        # Anti-cheat + injection guard
│   ├── workers/
│   │   ├── celery_app.py      # Celery configuration
│   │   └── tasks.py           # Async ML tasks
│   ├── evaluation/
│   │   ├── metrics.py         # NDCG, Precision, Recall, MRR
│   │   ├── evaluator.py       # Benchmark pipeline
│   │   └── benchmark_data.py  # Labeled test dataset
│   ├── db/
│   │   ├── models.py          # SQLAlchemy tables
│   │   └── crud.py            # DB operations
│   └── auth/
│       ├── jwt.py             # JWT tokens
│       └── hashing.py         # bcrypt passwords
├── frontend/
│   └── src/
│       └── components/        # React UI
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── Dockerfile.worker
└── docker-compose.yml

---

## Security Features

- **Keyword stuffing detection** — flags resumes with suspiciously repeated terms
- **Prompt injection guard** — strips LLM manipulation attempts before AI processing
- **PII scrubber** — detects and removes emails, phones, addresses before storage
- **PDF validation** — magic bytes check, page limit, size limit
- **Text confidence scoring** — warns when complex PDF layouts hurt extraction
- **Rate limiting** — 10 requests/minute per IP via slowapi
- **JWT authentication** — protected routes, bcrypt password hashing
- **No raw resume storage** — only scores and metadata saved to DB

---

## What I Learned Building This

- Why semantic search outperforms keyword matching for unstructured text
- How mean pooling over sentence embeddings beats whole-document encoding
- Why NDCG is the right metric for ranking problems (not accuracy)
- How Celery + Redis decouples heavy ML inference from HTTP response times
- Why vector databases exist and when to use them over traditional SQL search

---

*Built by Bhumik Kumta — [GitHub](https://github.com/Bhumik2005)*
 
