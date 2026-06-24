"""Tests for the CLI interface."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
from typer.testing import CliRunner

from synthid_tool.cli import app
from synthid_tool.models import DetectionResult, RemovalResult

runner = CliRunner()


def test_main_help():
    """Test that the main help shows detect and remove commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "detect" in result.output
    assert "remove" in result.output


def test_detect_help():
    """Test the detect command help text."""
    result = runner.invoke(app, ["detect", "--help"])
    assert result.exit_code == 0
    assert "image_path" in result.output.lower() or "IMAGE_PATH" in result.output


def test_remove_help():
    """Test the remove command help text."""
    result = runner.invoke(app, ["remove", "--help"])
    assert result.exit_code == 0
    assert "input_path" in result.output.lower() or "INPUT_PATH" in result.output
    assert "output_path" in result.output.lower() or "OUTPUT_PATH" in result.output


def test_detect_missing_image():
    """Test detect with a non-existent image path."""
    result = runner.invoke(app, ["detect", "/nonexistent/image.png"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "Error" in result.output


def test_remove_missing_input():
    """Test remove with a non-existent input image path."""
    result = runner.invoke(app, ["remove", "/nonexistent/input.png", "/tmp/out.png"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "Error" in result.output


@patch("synthid_tool.cli.run_detect")
def test_detect_text_output(mock_detect):
    """Test detect command with text output format."""
    mock_detect.return_value = DetectionResult(
        is_watermarked=True,
        confidence=0.87,
        phase_match=0.75,
        details={"method": "spectral"},
    )

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        # Write a minimal valid PNG
        import cv2
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        cv2.imwrite(f.name, img)
        tmp_path = f.name

    try:
        result = runner.invoke(app, ["detect", tmp_path])
        assert result.exit_code == 0
        assert "0.87" in result.output or "0.8700" in result.output
        mock_detect.assert_called_once()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@patch("synthid_tool.cli.run_detect")
def test_detect_json_output(mock_detect):
    """Test detect command with JSON output format."""
    mock_detect.return_value = DetectionResult(
        is_watermarked=False,
        confidence=0.23,
        phase_match=0.15,
        details={},
    )

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        import cv2
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        cv2.imwrite(f.name, img)
        tmp_path = f.name

    try:
        result = runner.invoke(app, ["detect", tmp_path, "--output-format", "json"])
        assert result.exit_code == 0
        # The JSON output should be parseable
        # Rich adds markup, try to find the JSON content
        assert "is_watermarked" in result.output
        assert "false" in result.output.lower()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@patch("synthid_tool.cli.remove_fast")
def test_remove_fast_mode(mock_remove):
    """Test remove command with fast mode."""
    cleaned = np.zeros((64, 64, 3), dtype=np.uint8)
    mock_remove.return_value = RemovalResult(
        success=True,
        cleaned_image=cleaned,
        psnr=35.5,
        ssim=0.95,
        stages_applied=["spectral_subtraction", "post_filter"],
        mode="fast",
    )

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        import cv2
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        cv2.imwrite(f.name, img)
        input_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        output_path = f.name

    try:
        result = runner.invoke(
            app, ["remove", input_path, output_path, "--mode", "fast"]
        )
        assert result.exit_code == 0
        assert "35.5" in result.output or "35.50" in result.output
        assert Path(output_path).exists()
        mock_remove.assert_called_once()
    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


@patch("synthid_tool.cli.remove_full")
def test_remove_full_mode(mock_remove):
    """Test remove command with full mode."""
    cleaned = np.zeros((64, 64, 3), dtype=np.uint8)
    mock_remove.return_value = RemovalResult(
        success=True,
        cleaned_image=cleaned,
        psnr=38.2,
        ssim=0.97,
        stages_applied=["vae_regen", "elastic", "geometric", "resize", "color", "fft", "post"],
        mode="full",
    )

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        import cv2
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        cv2.imwrite(f.name, img)
        input_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        output_path = f.name

    try:
        result = runner.invoke(
            app, ["remove", input_path, output_path, "--mode", "full"]
        )
        assert result.exit_code == 0
        assert "38.2" in result.output or "38.20" in result.output
        assert Path(output_path).exists()
        mock_remove.assert_called_once()
    finally:
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)


def test_remove_invalid_mode():
    """Test remove command with invalid mode."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        import cv2
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        cv2.imwrite(f.name, img)
        input_path = f.name

    try:
        result = runner.invoke(
            app, ["remove", input_path, "/tmp/out.png", "--mode", "invalid"]
        )
        assert result.exit_code == 1
        assert "fast" in result.output.lower() or "full" in result.output.lower()
    finally:
        Path(input_path).unlink(missing_ok=True)
