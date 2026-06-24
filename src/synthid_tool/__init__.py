"""synthid_tool - Detect and remove SynthID watermarks from AI-generated images."""

from synthid_tool.detector import detect
from synthid_tool.models import DetectionResult, RemovalResult
from synthid_tool.remover import remove_fast, remove_full

__all__ = [
    "detect",
    "remove_fast",
    "remove_full",
    "DetectionResult",
    "RemovalResult",
]

__version__ = "0.1.0"
