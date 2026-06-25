"""Tests for the FastAPI backend."""

from __future__ import annotations

import io
from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app import app
from backend.job_store import JobState, clear_jobs, create_job, update_job
from synthid_tool.models import DetectionResult, RemovalResult


@pytest.fixture(autouse=True)
def _clear_job_store():
    """Clear the job store before each test."""
    clear_jobs()
    yield
    clear_jobs()


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def dummy_png_bytes():
    """Generate a minimal valid PNG image as bytes."""
    img = Image.fromarray(np.zeros((64, 64, 3), dtype=np.uint8))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def _make_detection_result(watermarked=True, confidence=0.85, status=None):
    """Create a mock DetectionResult."""
    if status is None:
        status = "watermarked" if watermarked else "clean"
    return DetectionResult(
        is_watermarked=watermarked,
        confidence=confidence,
        phase_match=0.72,
        status=status,
        details={"method": "robust"},
    )


def _make_removal_result():
    """Create a mock RemovalResult."""
    return RemovalResult(
        success=True,
        cleaned_image=np.zeros((64, 64, 3), dtype=np.uint8),
        psnr=35.2,
        ssim=0.95,
        stages_applied=["spectral_bypass"],
        mode="fast",
    )


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestDetectEndpoint:
    """Tests for POST /api/detect."""

    @patch("backend.routes.detect.run_detection")
    def test_detect_watermark(self, mock_detect, client, dummy_png_bytes):
        mock_detect.return_value = _make_detection_result()

        response = client.post(
            "/api/detect",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_watermarked"] is True
        assert data["status"] == "watermarked"
        assert data["confidence"] == 0.85
        assert data["phase_match"] == 0.72
        assert "details" in data
        mock_detect.assert_called_once()

    @patch("backend.routes.detect.run_detection")
    def test_detect_not_watermarked(self, mock_detect, client, dummy_png_bytes):
        mock_detect.return_value = _make_detection_result(
            watermarked=False, confidence=0.12
        )

        response = client.post(
            "/api/detect",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_watermarked"] is False
        assert data["status"] == "clean"
        assert data["confidence"] == 0.12

    @patch("backend.routes.detect.run_detection")
    def test_detect_uncertain(self, mock_detect, client, dummy_png_bytes):
        mock_detect.return_value = _make_detection_result(
            watermarked=False, confidence=0.25, status="uncertain"
        )

        response = client.post(
            "/api/detect",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_watermarked"] is False
        assert data["status"] == "uncertain"

    def test_detect_no_file(self, client):
        response = client.post("/api/detect")
        assert response.status_code == 422  # Validation error

    @patch("backend.routes.detect.run_detection")
    def test_detect_processing_error(self, mock_detect, client, dummy_png_bytes):
        mock_detect.side_effect = ValueError("Invalid image format")

        response = client.post(
            "/api/detect",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
        )

        assert response.status_code == 400


class TestRemoveSyncEndpoint:
    """Tests for POST /api/remove/sync."""

    @patch("backend.routes.remove.run_removal")
    def test_remove_sync_fast(self, mock_remove, client, dummy_png_bytes):
        mock_remove.return_value = _make_removal_result()

        response = client.post(
            "/api/remove/sync",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
            data={"mode": "fast"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        # Verify the response is a valid PNG
        img = Image.open(io.BytesIO(response.content))
        assert img.format == "PNG"
        mock_remove.assert_called_once()

    @patch("backend.routes.remove.run_removal")
    def test_remove_sync_with_strength(self, mock_remove, client, dummy_png_bytes):
        mock_remove.return_value = _make_removal_result()

        response = client.post(
            "/api/remove/sync",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
            data={"mode": "fast", "strength": "gentle"},
        )

        assert response.status_code == 200
        mock_remove.assert_called_once_with(
            dummy_png_bytes, "fast", "gentle", None
        )

    def test_remove_sync_invalid_mode(self, client, dummy_png_bytes):
        response = client.post(
            "/api/remove/sync",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
            data={"mode": "invalid"},
        )

        assert response.status_code == 400
        assert "mode must be" in response.json()["detail"]

    @patch("backend.routes.remove.run_removal")
    def test_remove_sync_error(self, mock_remove, client, dummy_png_bytes):
        mock_remove.side_effect = ValueError("Invalid image")

        response = client.post(
            "/api/remove/sync",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
            data={"mode": "fast"},
        )

        assert response.status_code == 400

    @patch("backend.routes.remove.run_removal")
    def test_remove_sync_nuke_fast_normalizes_to_maximum(
        self, mock_remove, client, dummy_png_bytes
    ):
        """Test that 'nuke' strength in fast mode is normalized to 'maximum'."""
        mock_remove.return_value = _make_removal_result()

        response = client.post(
            "/api/remove/sync",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
            data={"mode": "fast", "strength": "nuke"},
        )

        assert response.status_code == 200
        mock_remove.assert_called_once_with(
            dummy_png_bytes, "fast", "maximum", None
        )

    @patch("backend.routes.remove.run_removal")
    def test_remove_sync_invalid_strength_normalizes_to_none(
        self, mock_remove, client, dummy_png_bytes
    ):
        """Test that an invalid strength is normalized to None (engine default)."""
        mock_remove.return_value = _make_removal_result()

        response = client.post(
            "/api/remove/sync",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
            data={"mode": "fast", "strength": "banana"},
        )

        assert response.status_code == 200
        mock_remove.assert_called_once_with(
            dummy_png_bytes, "fast", None, None
        )


class TestRemoveAsyncEndpoint:
    """Tests for POST /api/remove (async)."""

    @patch("backend.routes.remove._process_removal")
    def test_remove_async_returns_job_id(self, mock_process, client, dummy_png_bytes):
        # Make the background task a no-op for this test
        mock_process.return_value = None

        response = client.post(
            "/api/remove",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
            data={"mode": "full"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    def test_remove_async_invalid_mode(self, client, dummy_png_bytes):
        response = client.post(
            "/api/remove",
            files={"file": ("test.png", dummy_png_bytes, "image/png")},
            data={"mode": "wrong"},
        )

        assert response.status_code == 400


class TestJobsEndpoint:
    """Tests for GET /api/jobs/{job_id}."""

    def test_get_job_not_found(self, client):
        response = client.get("/api/jobs/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_job_pending(self, client):
        job = create_job(metadata={"mode": "fast"})

        response = client.get(f"/api/jobs/{job.job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job.job_id
        assert data["status"] == "pending"
        assert data["progress"] == 0.0

    def test_get_job_completed(self, client):
        job = create_job()
        update_job(job.job_id, status=JobState.COMPLETED, progress=1.0)

        response = client.get(f"/api/jobs/{job.job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 1.0

    def test_get_job_failed(self, client):
        job = create_job()
        update_job(job.job_id, status=JobState.FAILED, error="Something broke")

        response = client.get(f"/api/jobs/{job.job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] == "Something broke"

    def test_get_result_not_completed(self, client):
        job = create_job()

        response = client.get(f"/api/jobs/{job.job_id}/result")
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"].lower()

    def test_get_result_not_found(self, client):
        response = client.get("/api/jobs/nonexistent/result")
        assert response.status_code == 404
