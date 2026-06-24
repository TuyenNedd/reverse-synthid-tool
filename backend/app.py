"""FastAPI application for SynthID watermark detection and removal."""

from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import HOST, PORT
from backend.routes import detect, jobs, remove


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Pre-loads codebooks on startup so the first request is fast.
    """
    # Pre-load codebooks into memory on startup
    try:
        from synthid_tool.codebook import get_v3_codebook

        get_v3_codebook()
        print("V3 codebook pre-loaded successfully")
    except FileNotFoundError:
        print("Warning: V3 codebook not found, will attempt to load on first request")
    except Exception as e:
        print(f"Warning: Failed to pre-load V3 codebook: {e}")

    yield

    # Cleanup on shutdown (if needed in the future)


app = FastAPI(
    title="SynthID Tool",
    description="Detect and remove SynthID watermarks from AI-generated images",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(detect.router)
app.include_router(remove.router)
app.include_router(jobs.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


def start_server():
    """Entry point for the synthid-server command."""
    uvicorn.run(
        "backend.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    start_server()
