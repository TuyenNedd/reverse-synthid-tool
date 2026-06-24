"""Job status and result endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend import job_store

router = APIRouter()


class JobStatusResponse(BaseModel):
    """Response schema for job status endpoint."""

    job_id: str
    status: str
    progress: float
    error: Optional[str] = None


@router.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a processing job.

    Returns the current status (pending/processing/completed/failed),
    progress (0.0-1.0), and any error message.
    """
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        progress=job.progress,
        error=job.error,
    )


@router.get("/api/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """Download the result image for a completed job.

    Returns the cleaned PNG image file. Only available when job
    status is 'completed'.
    """
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != job_store.JobState.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed (status: {job.status.value})",
        )

    if not job.result_path or not Path(job.result_path).exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    return FileResponse(
        job.result_path,
        media_type="image/png",
        filename=f"{job_id}_cleaned.png",
    )
