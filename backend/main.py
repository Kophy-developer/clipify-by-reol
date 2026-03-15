"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import ingest, status, results, retry
from utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup if needed


app = FastAPI(
    title="Clipify by Reol",
    description="AI-powered 45–60s vertical clips with subtitles and auto-publish",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(status.router, prefix="/status", tags=["status"])
app.include_router(results.router, prefix="/results", tags=["results"])
app.include_router(retry.router, prefix="/retry", tags=["retry"])


@app.get("/")
async def root():
    return {"service": "Clipify by Reol", "docs": "/docs"}
