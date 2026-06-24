"""Backend configuration."""

from __future__ import annotations

import os
from pathlib import Path

# Server settings
HOST = os.environ.get("SYNTHID_HOST", "0.0.0.0")
PORT = int(os.environ.get("SYNTHID_PORT", "8000"))

# Project root (one level up from backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Artifacts directory
ARTIFACTS_DIR = Path(
    os.environ.get("SYNTHID_ARTIFACTS_DIR", str(PROJECT_ROOT / "artifacts"))
)

# Upload limits
MAX_UPLOAD_SIZE = int(os.environ.get("SYNTHID_MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))  # 50 MB

# Allowed image extensions
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

# Temporary directory for job results
RESULTS_DIR = Path(os.environ.get("SYNTHID_RESULTS_DIR", str(PROJECT_ROOT / ".results")))
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
