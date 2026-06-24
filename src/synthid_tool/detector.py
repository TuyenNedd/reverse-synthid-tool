"""SynthID watermark detection interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import numpy as np

from synthid_tool.config import ROBUST_CODEBOOK_PATH
from synthid_tool.models import DetectionResult


def detect(
    image: Union[str, Path, np.ndarray],
    codebook_path: Optional[str] = None,
) -> DetectionResult:
    """Detect SynthID watermark in an image.

    Args:
        image: Either a file path (str or Path) to an image, or a numpy
               array in RGB uint8 format (H x W x 3).
        codebook_path: Optional path to a .pkl detection codebook.
                       Defaults to artifacts/codebook/robust_codebook.pkl.

    Returns:
        DetectionResult with is_watermarked, confidence, phase_match, and details.

    Raises:
        FileNotFoundError: If the codebook or image file is not found.
        ValueError: If the image cannot be loaded or has invalid format.
    """
    from synthid_tool._engine.robust_extractor import RobustSynthIDExtractor

    # Resolve codebook path
    cb_path = Path(codebook_path) if codebook_path else ROBUST_CODEBOOK_PATH
    if not cb_path.exists():
        raise FileNotFoundError(
            f"Detection codebook not found at {cb_path}. "
            "Set SYNTHID_ARTIFACTS_DIR or provide an explicit codebook_path."
        )

    extractor = RobustSynthIDExtractor()
    extractor.load_codebook(str(cb_path))

    # Handle path vs array input
    if isinstance(image, (str, Path)):
        image_path = Path(image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        engine_result = extractor.detect(str(image_path))
    elif isinstance(image, np.ndarray):
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(
                f"Expected HxWx3 RGB image array, got shape {image.shape}"
            )
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        engine_result = extractor.detect_array(image)
    else:
        raise TypeError(
            f"Expected str, Path, or numpy array, got {type(image)}"
        )

    return DetectionResult(
        is_watermarked=engine_result.is_watermarked,
        confidence=engine_result.confidence,
        phase_match=engine_result.phase_match,
        details=engine_result.details,
    )
