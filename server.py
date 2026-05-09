"""
ODIN-HEADHUNTER API Server
FastAPI app with CORS + lifecycle hooks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.endpoints import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup handled in main.py — nothing async needed here
    yield

app = FastAPI(
    title="ODIN Memory API",
    description="4-layer persistent memory system for ODIN AI companion",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock this down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/memory")


@app.get("/")
async def root():
    return {
        "service": "ODIN-MEMORY",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
