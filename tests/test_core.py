"""Core unit tests for synthid_tool package."""

import numpy as np
import pytest

from synthid_tool import DetectionResult, RemovalResult, detect, remove_fast, remove_full
from synthid_tool.models import ProcessingMode


class TestImports:
    """Test that all public API symbols are importable."""

    def test_import_detect(self):
        from synthid_tool import detect
        assert callable(detect)

    def test_import_remove_fast(self):
        from synthid_tool import remove_fast
        assert callable(remove_fast)

    def test_import_remove_full(self):
        from synthid_tool import remove_full
        assert callable(remove_full)

    def test_import_detection_result(self):
        from synthid_tool import DetectionResult
        assert DetectionResult is not None

    def test_import_removal_result(self):
        from synthid_tool import RemovalResult
        assert RemovalResult is not None

    def test_import_processing_mode(self):
        assert ProcessingMode.FAST.value == "fast"
        assert ProcessingMode.FULL.value == "full"


class TestDetectionResult:
    """Test DetectionResult dataclass."""

    def test_creation(self):
        result = DetectionResult(
            is_watermarked=True,
            confidence=0.95,
            phase_match=0.92,
            status="watermarked",
            details={"best_set": "dark"},
        )
        assert result.is_watermarked is True
        assert result.confidence == 0.95
        assert result.phase_match == 0.92
        assert result.status == "watermarked"
        assert result.details == {"best_set": "dark"}

    def test_defaults(self):
        result = DetectionResult(
            is_watermarked=False,
            confidence=0.1,
            phase_match=0.45,
        )
        assert result.details == {}
        # Status defaults to clean for backward-compatible construction.
        assert result.status == "clean"


class TestRemovalResult:
    """Test RemovalResult dataclass."""

    def test_creation(self):
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        result = RemovalResult(
            success=True,
            cleaned_image=img,
            psnr=35.0,
            ssim=0.95,
            stages_applied=["pass_0(aggressive)"],
            mode="fast",
        )
        assert result.success is True
        assert result.cleaned_image.shape == (64, 64, 3)
        assert result.psnr == 35.0
        assert result.ssim == 0.95
        assert result.mode == "fast"

    def test_defaults(self):
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        result = RemovalResult(
            success=True,
            cleaned_image=img,
            psnr=35.0,
            ssim=0.95,
        )
        assert result.stages_applied == []
        assert result.mode == "fast"
        assert result.details == {}


class TestDetect:
    """Test the detect() function."""

    def test_detect_returns_detection_result(self):
        """detect() on a synthetic image should return a DetectionResult."""
        # Create a small synthetic image (random noise - not watermarked)
        rng = np.random.default_rng(42)
        image = rng.integers(0, 255, size=(128, 128, 3), dtype=np.uint8)
        result = detect(image)
        assert isinstance(result, DetectionResult)
        assert isinstance(result.is_watermarked, bool)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.phase_match, float)
        # New 3-way classification field.
        assert result.status in ("clean", "uncertain", "watermarked")
        # is_watermarked stays consistent with the confident status only.
        assert result.is_watermarked == (result.status == "watermarked")

    def test_detect_non_square_image(self):
        """detect() should handle non-square (landscape/portrait) images.

        Aspect-ratio-preserving detection must not crash and must return a
        valid result for non-square inputs.
        """
        rng = np.random.default_rng(7)
        landscape = rng.integers(0, 255, size=(96, 160, 3), dtype=np.uint8)
        portrait = rng.integers(0, 255, size=(160, 96, 3), dtype=np.uint8)
        for image in (landscape, portrait):
            result = detect(image)
            assert isinstance(result, DetectionResult)
            assert 0.0 <= result.confidence <= 1.0
            assert result.status in ("clean", "uncertain", "watermarked")

    def test_detect_invalid_shape(self):
        """detect() should raise ValueError for non-RGB arrays."""
        image = np.zeros((64, 64), dtype=np.uint8)  # grayscale
        with pytest.raises(ValueError):
            detect(image)

    def test_detect_file_not_found(self):
        """detect() should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            detect("/nonexistent/path/to/image.png")


class TestRemoveFast:
    """Test the remove_fast() function."""

    def test_remove_fast_returns_removal_result(self):
        """remove_fast() on a synthetic image should return a RemovalResult."""
        # Create a small synthetic image
        rng = np.random.default_rng(42)
        image = rng.integers(50, 200, size=(128, 128, 3), dtype=np.uint8)
        result = remove_fast(image)
        assert isinstance(result, RemovalResult)
        assert result.mode == "fast"
        assert isinstance(result.cleaned_image, np.ndarray)
        assert result.cleaned_image.shape == image.shape
        assert result.cleaned_image.dtype == np.uint8
        assert isinstance(result.psnr, float)
        assert isinstance(result.ssim, float)
        assert isinstance(result.stages_applied, list)
        assert len(result.stages_applied) > 0

    def test_remove_fast_invalid_shape(self):
        """remove_fast() should raise ValueError for non-RGB arrays."""
        image = np.zeros((64, 64), dtype=np.uint8)
        with pytest.raises(ValueError):
            remove_fast(image)

    def test_remove_fast_strength_options(self):
        """remove_fast() should accept various strength options."""
        rng = np.random.default_rng(42)
        image = rng.integers(50, 200, size=(64, 64, 3), dtype=np.uint8)
        for strength in ("gentle", "moderate", "aggressive"):
            result = remove_fast(image, strength=strength)
            assert isinstance(result, RemovalResult)
            assert result.mode == "fast"


class TestRemoveFull:
    """Test the remove_full() function (without actual VAE - checks interface)."""

    def test_remove_full_invalid_shape(self):
        """remove_full() should raise ValueError for non-RGB arrays."""
        image = np.zeros((64, 64), dtype=np.uint8)
        with pytest.raises(ValueError):
            remove_full(image)



class TestLetterboxResize:
    """Test the aspect-ratio-preserving letterbox resize in the engine."""

    def test_square_image_matches_plain_resize(self):
        """For square inputs, letterbox must equal a plain square resize."""
        import cv2

        from synthid_tool._engine.robust_extractor import RobustSynthIDExtractor

        rng = np.random.default_rng(1)
        img = rng.integers(0, 255, size=(100, 100, 3), dtype=np.uint8)
        target = 512
        letterboxed = RobustSynthIDExtractor._letterbox_to_square(img, target)
        plain = cv2.resize(img, (target, target))
        assert letterboxed.shape == (target, target, 3)
        np.testing.assert_array_equal(letterboxed, plain)

    def test_non_square_preserves_aspect_ratio(self):
        """A landscape image should be scaled (not squished) and padded."""
        from synthid_tool._engine.robust_extractor import RobustSynthIDExtractor

        rng = np.random.default_rng(2)
        img = rng.integers(0, 255, size=(90, 180, 3), dtype=np.uint8)
        target = 512
        out = RobustSynthIDExtractor._letterbox_to_square(img, target)
        assert out.shape == (target, target, 3)
        # Longer side (width) maps to the full target; height is padded.
        # The padded rows (top/bottom) should be a constant neutral fill.
        top_row = out[0]
        assert np.all(top_row == top_row[0])


class TestClassifyPhaseMatch:
    """Test the 3-way phase-match classification bands."""

    def test_clean_band(self):
        from synthid_tool._engine.robust_extractor import classify_phase_match

        assert classify_phase_match(0.50) == "clean"
        assert classify_phase_match(0.0) == "clean"

    def test_uncertain_band(self):
        from synthid_tool._engine.robust_extractor import classify_phase_match

        # The reported bug value 0.6093 must land in the gray zone.
        assert classify_phase_match(0.6093) == "uncertain"
        assert classify_phase_match(0.60) == "uncertain"
        assert classify_phase_match(0.77) == "uncertain"

    def test_watermarked_band(self):
        from synthid_tool._engine.robust_extractor import classify_phase_match

        assert classify_phase_match(0.78) == "watermarked"
        assert classify_phase_match(0.95) == "watermarked"
