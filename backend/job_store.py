"""In-memory job store for async processing.

This module implements a simple dict-based job store for tracking
background processing jobs. The interface is designed to be easily
swappable with Redis, a database, or a task queue backend later.

NOTE (MVP limitation): This store is intentionally in-memory for the MVP.
All job metadata is lost on process restart, and result files in .results/
become orphaned. For production use, replace this with a Redis-backed or
database-backed implementation that persists job state and implements TTL
cleanup of result files. The public API (create_job, update_job, get_job)
is designed so that swap can happen without changing routes.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class JobState(str, Enum):
    """Possible states for a processing job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """Represents a processing job."""

    job_id: str
    status: JobState = JobState.PENDING
    progress: float = 0.0
    result_path: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


# In-memory store
_jobs: Dict[str, Job] = {}


def create_job(metadata: Optional[Dict[str, Any]] = None) -> Job:
    """Create a new job and return it.

    Args:
        metadata: Optional metadata about the job (mode, strength, etc.)

    Returns:
        The newly created Job instance.
    """
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, metadata=metadata or {})
    _jobs[job_id] = job
    return job


def update_job(
    job_id: str,
    status: Optional[JobState] = None,
    progress: Optional[float] = None,
    result_path: Optional[str] = None,
    error: Optional[str] = None,
) -> Optional[Job]:
    """Update an existing job.

    Args:
        job_id: The job identifier.
        status: New status to set.
        progress: New progress value (0.0 to 1.0).
        result_path: Path to the result image file.
        error: Error message if the job failed.

    Returns:
        The updated Job, or None if not found.
    """
    job = _jobs.get(job_id)
    if job is None:
        return None

    if status is not None:
        job.status = status
    if progress is not None:
        job.progress = progress
    if result_path is not None:
        job.result_path = result_path
    if error is not None:
        job.error = error
    job.updated_at = time.time()
    return job


def get_job(job_id: str) -> Optional[Job]:
    """Get a job by ID.

    Args:
        job_id: The job identifier.

    Returns:
        The Job instance, or None if not found.
    """
    return _jobs.get(job_id)


def clear_jobs() -> None:
    """Clear all jobs (useful for testing)."""
    _jobs.clear()
