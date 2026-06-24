"""Central configuration for synthid_tool."""

from __future__ import annotations

import os
from pathlib import Path

# Default artifacts directory: relative to the package root (../../artifacts)
_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_DIR.parent.parent

# Allow override via environment variable
ARTIFACTS_DIR = Path(
    os.environ.get("SYNTHID_ARTIFACTS_DIR", str(_PROJECT_ROOT / "artifacts"))
)

# Default paths to codebook files
ROBUST_CODEBOOK_PATH = ARTIFACTS_DIR / "codebook" / "robust_codebook.pkl"
V3_CODEBOOK_PATH = ARTIFACTS_DIR / "spectral_codebook_v3.npz"
V4_CODEBOOK_PATH = ARTIFACTS_DIR / "spectral_codebook_v4.npz"

# Default model for VAE regeneration (V4 full mode)
DEFAULT_VAE_MODEL = os.environ.get(
    "SYNTHID_DEFAULT_MODEL", "stabilityai/sd-vae-ft-mse"
)

# Default strength settings
DEFAULT_FAST_STRENGTH = "aggressive"
DEFAULT_FULL_STRENGTH = "final"
