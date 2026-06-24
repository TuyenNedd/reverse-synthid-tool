"""Codebook loading utilities for synthid_tool."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from synthid_tool.config import V3_CODEBOOK_PATH, V4_CODEBOOK_PATH

# Module-level caches for lazy-loaded codebooks, protected by a lock
# to avoid races when multiple threads hit get_v3/v4_codebook concurrently
# (e.g. under gunicorn --threads or asyncio.to_thread).
_cache_lock = threading.Lock()
_v3_codebook = None
_v4_codebook = None


def get_v3_codebook(path: Optional[str] = None):
    """Load and cache the V3 spectral codebook.

    Args:
        path: Optional path to the .npz codebook file.
              Defaults to artifacts/spectral_codebook_v3.npz.

    Returns:
        A SpectralCodebook instance.
    """
    global _v3_codebook

    # Fast path: already loaded (no lock needed for read of immutable ref)
    if _v3_codebook is not None and path is None:
        return _v3_codebook

    from synthid_tool._engine.synthid_bypass import SpectralCodebook

    codebook_path = Path(path) if path else V3_CODEBOOK_PATH
    if not codebook_path.exists():
        raise FileNotFoundError(
            f"V3 codebook not found at {codebook_path}. "
            "Set SYNTHID_ARTIFACTS_DIR or provide an explicit path."
        )

    if path is None:
        with _cache_lock:
            # Double-check inside lock to avoid redundant loads
            if _v3_codebook is None:
                cb = SpectralCodebook()
                cb.load(str(codebook_path))
                _v3_codebook = cb
            return _v3_codebook
    else:
        cb = SpectralCodebook()
        cb.load(str(codebook_path))
        return cb


def get_v4_codebook(path: Optional[str] = None):
    """Load and cache the V4 spectral codebook.

    Args:
        path: Optional path to the .npz codebook file.
              Defaults to artifacts/spectral_codebook_v4.npz.

    Returns:
        A SpectralCodebookV4 instance.
    """
    global _v4_codebook

    # Fast path: already loaded (no lock needed for read of immutable ref)
    if _v4_codebook is not None and path is None:
        return _v4_codebook

    from synthid_tool._engine.synthid_bypass_v4 import SpectralCodebookV4

    codebook_path = Path(path) if path else V4_CODEBOOK_PATH
    if not codebook_path.exists():
        raise FileNotFoundError(
            f"V4 codebook not found at {codebook_path}. "
            "Set SYNTHID_ARTIFACTS_DIR or provide an explicit path."
        )

    if path is None:
        with _cache_lock:
            # Double-check inside lock to avoid redundant loads
            if _v4_codebook is None:
                cb = SpectralCodebookV4()
                cb.load(str(codebook_path))
                _v4_codebook = cb
            return _v4_codebook
    else:
        cb = SpectralCodebookV4()
        cb.load(str(codebook_path))
        return cb
