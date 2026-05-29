from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routes import router
from core.config import settings
from core.vector_store import init_collections

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Resume Matcher API starting up...")
    print("🔌 Initialising Qdrant collections...")
    try:
        init_collections()
        print("✅ Qdrant collections ready")
    except Exception as e:
        print(f"⚠️  Qdrant not available: {e} — vector features disabled")
    yield
    print("🛑 Shutting down...")

app = FastAPI(
    title="Resume Matcher API",
    description="AI-powered semantic talent intelligence platform",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    from core.vector_store import get_collection_stats
    try:
        stats = get_collection_stats()
        qdrant_status = "connected"
    except Exception:
        stats = {}
        qdrant_status = "unavailable"
    return {
        "status": "healthy",
        "version": "2.0.0",
        "qdrant": qdrant_status,
        "collections": stats,
    }