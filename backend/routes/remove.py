"""Removal endpoints (sync and async)."""

from __future__ import annotations

import asyncio
import io
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image
from pydantic import BaseModel

from backend import job_store
from backend.config import MAX_UPLOAD_SIZE, RESULTS_DIR
from backend.job_store import JobState
from backend.services import run_removal

router = APIRouter()

# Valid strengths per mode. Used to normalize user input before passing to engine.
_VALID_STRENGTHS_FAST = {"gentle", "moderate", "aggressive", "maximum"}
_VALID_STRENGTHS_FULL = {"final", "nuke"}


def _normalize_strength(mode: str, strength: Optional[str]) -> Optional[str]:
    """Normalize strength value for the given mode.

    Maps 'nuke' to 'maximum' for fast mode (V3 does not recognize 'nuke').
    Returns None for unrecognized values so the engine uses its default.
    """
    if strength is None:
        return None
    s = strength.lower().strip()
    if mode == "fast":
        if s == "nuke":
            s = "maximum"
        return s if s in _VALID_STRENGTHS_FAST else None
    else:
        # Full mode (V4) accepts 'final' and 'nuke'
        if s == "maximum" or s == "aggressive":
            s = "nuke"
        return s if s in _VALID_STRENGTHS_FULL else None


class AsyncRemoveResponse(BaseModel):
    """Response schema for async removal endpoint."""

    job_id: str
    status: str


@router.post("/api/remove", response_model=AsyncRemoveResponse)
async def remove_watermark_async(
    file: UploadFile = File(...),
    mode: str = Form("fast"),
    strength: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
):
    """Remove watermark asynchronously.

    Creates a background job and returns a job_id immediately.
    Client polls GET /api/jobs/{job_id} for status, then downloads
    the result from GET /api/jobs/{job_id}/result.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum upload size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
        )

    if mode not in ("fast", "full"):
        raise HTTPException(
            status_code=400, detail="mode must be 'fast' or 'full'"
        )

    # Normalize strength for the selected mode
    normalized_strength = _normalize_strength(mode, strength)

    # Create job
    job = job_store.create_job(
        metadata={"mode": mode, "strength": normalized_strength, "model": model}
    )

    # Run removal in background task (use get_running_loop for Python 3.10+ compat)
    loop = asyncio.get_running_loop()
    loop.create_task(
        _process_removal(job.job_id, contents, mode, normalized_strength, model)
    )

    return AsyncRemoveResponse(job_id=job.job_id, status=job.status.value)


async def _process_removal(
    job_id: str,
    image_bytes: bytes,
    mode: str,
    strength: Optional[str],
    model: Optional[str],
):
    """Background task to process watermark removal."""
    job_store.update_job(job_id, status=JobState.PROCESSING, progress=0.1)

    try:
        result = await asyncio.to_thread(
            run_removal, image_bytes, mode, strength, model
        )

        # Save result image to disk
        result_path = str(RESULTS_DIR / f"{job_id}.png")
        img = Image.fromarray(result.cleaned_image)
        img.save(result_path, format="PNG")

        job_store.update_job(
            job_id,
            status=JobState.COMPLETED,
            progress=1.0,
            result_path=result_path,
        )
    except Exception as e:
        job_store.update_job(
            job_id,
            status=JobState.FAILED,
            error=str(e),
        )


@router.post("/api/remove/sync")
async def remove_watermark_sync(
    file: UploadFile = File(...),
    mode: str = Form("fast"),
    strength: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
):
    """Remove watermark synchronously and return the cleaned image.

    Returns the cleaned image directly as a PNG file download.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum upload size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
        )

    if mode not in ("fast", "full"):
        raise HTTPException(
            status_code=400, detail="mode must be 'fast' or 'full'"
        )

    # Normalize strength for the selected mode
    normalized_strength = _normalize_strength(mode, strength)

    try:
        result = await asyncio.to_thread(
            run_removal, contents, mode, normalized_strength, model
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Removal failed: {e}")

    # Encode result as PNG
    img = Image.fromarray(result.cleaned_image)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=cleaned.png"},
    )
