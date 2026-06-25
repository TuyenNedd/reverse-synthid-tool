"""Shared data models for synthid_tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np


class ProcessingMode(Enum):
    """Processing mode for watermark removal."""

    FAST = "fast"
    FULL = "full"


class DetectionStatus(str, Enum):
    """Three-way watermark classification.

    - ``CLEAN``: phase/confidence clearly in the non-watermarked range.
    - ``UNCERTAIN``: signal is elevated above the clean baseline but below the
      confident-watermark threshold (the "gray zone").
    - ``WATERMARKED``: confident watermark detection.
    """

    CLEAN = "clean"
    UNCERTAIN = "uncertain"
    WATERMARKED = "watermarked"


@dataclass
class DetectionResult:
    """Result of watermark detection.

    ``is_watermarked`` is kept for backward compatibility and is True only for
    the confident ``WATERMARKED`` case. Use ``status`` for the full three-way
    classification (clean / uncertain / watermarked).
    """

    is_watermarked: bool
    confidence: float
    phase_match: float
    status: str = DetectionStatus.CLEAN.value
    details: Dict = field(default_factory=dict)


@dataclass
class RemovalResult:
    """Result of watermark removal."""

    success: bool
    cleaned_image: np.ndarray
    psnr: float
    ssim: float
    stages_applied: List[str] = field(default_factory=list)
    mode: str = "fast"
    details: Dict = field(default_factory=dict)


@dataclass
class JobStatus:
    """Status of a processing job (for future queue-based scaling)."""

    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float = 0.0
    result: Optional[RemovalResult] = None
    error: Optional[str] = None
