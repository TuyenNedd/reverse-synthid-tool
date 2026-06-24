"""Detection endpoint."""

from __future__ import annotations

import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE
from backend.services import run_detection

router = APIRouter()


class DetectionResponse(BaseModel):
    """Response schema for detection endpoint."""

    is_watermarked: bool
    confidence: float
    phase_match: float
    details: dict = {}


@router.post("/api/detect", response_model=DetectionResponse)
async def detect_watermark(file: UploadFile = File(...)):
    """Detect SynthID watermark in an uploaded image.

    Accepts a multipart file upload and returns detection results
    as JSON with is_watermarked, confidence, phase_match, and details.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum upload size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
        )

    try:
        result = run_detection(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {e}")

    return DetectionResponse(
        is_watermarked=result.is_watermarked,
        confidence=result.confidence,
        phase_match=result.phase_match,
        details=result.details,
    )
