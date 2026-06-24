"""Business logic layer for the backend.

This module contains the core processing functions that bridge the
API routes to the synthid_tool library. Designed so that these functions
can later be replaced by task queue submissions (Celery/RQ) without
changing the API routes.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from PIL import Image
import io

from synthid_tool import detect, remove_fast, remove_full
from synthid_tool.models import DetectionResult, RemovalResult


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """Load image bytes into a numpy RGB array.

    Args:
        image_bytes: Raw image file bytes (PNG, JPEG, etc.)

    Returns:
        Numpy array in HxWx3 uint8 RGB format.

    Raises:
        ValueError: If the image cannot be decoded.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
        return np.array(img, dtype=np.uint8)
    except Exception as e:
        raise ValueError(f"Failed to decode image: {e}") from e


def run_detection(image_bytes: bytes) -> DetectionResult:
    """Run watermark detection on image bytes.

    Args:
        image_bytes: Raw image file content.

    Returns:
        DetectionResult with is_watermarked, confidence, phase_match, details.
    """
    image_array = load_image_from_bytes(image_bytes)
    return detect(image_array)


def run_removal(
    image_bytes: bytes,
    mode: str = "fast",
    strength: Optional[str] = None,
    model: Optional[str] = None,
) -> RemovalResult:
    """Run watermark removal on image bytes.

    Args:
        image_bytes: Raw image file content.
        mode: Processing mode - 'fast' (V3 spectral) or 'full' (V4 pipeline).
        strength: Strength setting. For fast: gentle/moderate/aggressive/maximum.
                  For full: final/nuke. If None, uses defaults.
        model: Model hint for full mode. If None, auto-selects.

    Returns:
        RemovalResult with cleaned_image, psnr, ssim, stages_applied, mode.
    """
    image_array = load_image_from_bytes(image_bytes)

    if mode == "full":
        kwargs = {}
        if strength:
            kwargs["strength"] = strength
        if model:
            kwargs["model"] = model
        return remove_full(image_array, **kwargs)
    else:
        kwargs = {}
        if strength:
            kwargs["strength"] = strength
        return remove_fast(image_array, **kwargs)
