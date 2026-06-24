"""SynthID watermark removal interface."""

from __future__ import annotations

from typing import Optional

import numpy as np

from synthid_tool.config import (
    DEFAULT_FAST_STRENGTH,
    DEFAULT_FULL_STRENGTH,
    DEFAULT_VAE_MODEL,
)
from synthid_tool.models import RemovalResult


def remove_fast(
    image: np.ndarray,
    codebook_path: Optional[str] = None,
    strength: str = DEFAULT_FAST_STRENGTH,
) -> RemovalResult:
    """Remove SynthID watermark using V3 spectral bypass (fast, no deep learning).

    This mode uses multi-resolution spectral codebook subtraction to remove
    the watermark in the frequency domain. It is fast and does not require
    a GPU or deep learning models.

    Args:
        image: Input RGB image as numpy array (H x W x 3, uint8).
        codebook_path: Optional path to the V3 spectral codebook (.npz).
                       Defaults to artifacts/spectral_codebook_v3.npz.
        strength: Bypass strength. One of 'gentle', 'moderate',
                  'aggressive', 'maximum'. Default: 'aggressive'.

    Returns:
        RemovalResult with cleaned_image, psnr, ssim, stages_applied, and mode.

    Raises:
        FileNotFoundError: If the codebook is not found.
        ValueError: If the image has invalid format.
    """
    from synthid_tool._engine.synthid_bypass import SynthIDBypass
    from synthid_tool.codebook import get_v3_codebook

    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(
            f"Expected HxWx3 RGB uint8 image, got shape {image.shape}"
        )

    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)

    codebook = get_v3_codebook(path=codebook_path)
    bypass = SynthIDBypass()

    engine_result = bypass.bypass_v3(
        image,
        codebook=codebook,
        strength=strength,
        verify=False,
    )

    return RemovalResult(
        success=engine_result.success,
        cleaned_image=engine_result.cleaned_image,
        psnr=engine_result.psnr,
        ssim=engine_result.ssim,
        stages_applied=engine_result.stages_applied,
        mode="fast",
        details=engine_result.details,
    )


def remove_full(
    image: np.ndarray,
    codebook_path: Optional[str] = None,
    strength: str = DEFAULT_FULL_STRENGTH,
    model: Optional[str] = None,
) -> RemovalResult:
    """Remove SynthID watermark using V4 multi-stage pipeline (requires torch).

    This mode uses the full 7-stage pipeline including VAE re-generation,
    elastic deformation, geometric transforms, resize-squeeze, color nudge,
    residual-phase FFT subtraction, and post-processing. Requires torch and
    diffusers to be installed (pip install synthid-tool[full]).

    Args:
        image: Input RGB image as numpy array (H x W x 3, uint8).
        codebook_path: Optional path to the V4 spectral codebook (.npz).
                       Defaults to artifacts/spectral_codebook_v4.npz.
        strength: Bypass strength. One of 'final', 'nuke'.
                  Default: 'final'.
        model: Optional model hint for codebook profile selection
               (e.g. 'gemini-3.1-flash-image-preview'). If None,
               best-matching profile is auto-selected.

    Returns:
        RemovalResult with cleaned_image, psnr, ssim, stages_applied, and mode.

    Raises:
        FileNotFoundError: If the codebook is not found.
        RuntimeError: If torch/diffusers are not installed.
        ValueError: If the image has invalid format.
    """
    from synthid_tool._engine.synthid_bypass_v4 import SynthIDBypassV4
    from synthid_tool.codebook import get_v4_codebook

    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(
            f"Expected HxWx3 RGB uint8 image, got shape {image.shape}"
        )

    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)

    codebook = get_v4_codebook(path=codebook_path)
    bypass = SynthIDBypassV4()

    engine_result = bypass.bypass_v4_final(
        image,
        codebook=codebook,
        strength=strength,
        model=model,
    )

    return RemovalResult(
        success=engine_result.success,
        cleaned_image=engine_result.cleaned_image,
        psnr=engine_result.psnr,
        ssim=engine_result.ssim,
        stages_applied=engine_result.stages_applied,
        mode="full",
        details=engine_result.details,
    )
