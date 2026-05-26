from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routes import router
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Resume Matcher API starting up...")
    yield
    print("🛑 Shutting down...")

app = FastAPI(
    title="Resume Matcher API",
    description="AI-powered resume vs job description matching",
    version="1.0.0",
    lifespan=lifespan,
)

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
    return {"status": "healthy", "version": "1.0.0"}