"""Command-line interface for synthid_tool."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from synthid_tool import detect as run_detect
from synthid_tool import remove_fast, remove_full

app = typer.Typer(
    name="synthid",
    help="Detect and remove SynthID watermarks from AI-generated images.",
    add_completion=False,
)
console = Console()


@app.command()
def detect(
    image_path: str = typer.Argument(
        ..., help="Path to the image file to analyze."
    ),
    codebook: Optional[str] = typer.Option(
        None, "--codebook", "-c", help="Path to a custom detection codebook (.pkl)."
    ),
    output_format: str = typer.Option(
        "text", "--output-format", "-f", help="Output format: text or json."
    ),
) -> None:
    """Detect SynthID watermark in an image."""
    path = Path(image_path)
    if not path.exists():
        console.print(f"[red]Error:[/red] Image not found: {image_path}")
        raise typer.Exit(code=1)

    with console.status("[bold blue]Analyzing image...[/bold blue]"):
        start = time.time()
        result = run_detect(str(path), codebook_path=codebook)
        elapsed = time.time() - start

    if output_format == "json":
        data = {
            "is_watermarked": result.is_watermarked,
            "status": result.status,
            "confidence": result.confidence,
            "phase_match": result.phase_match,
            "details": result.details,
        }
        console.print_json(json.dumps(data))
    else:
        # Three-way status -> colour + label.
        status_styles = {
            "clean": ("green", "CLEAN"),
            "uncertain": ("yellow", "UNCERTAIN"),
            "watermarked": ("red", "WATERMARKED"),
        }
        conf_color, status_label = status_styles.get(
            result.status, ("green", result.status.upper())
        )

        lines = [
            f"Status:      [{conf_color}]{status_label}[/{conf_color}]",
            f"Confidence:  [{conf_color}]{result.confidence:.4f}[/{conf_color}]",
            f"Phase Match: {result.phase_match:.4f}",
            f"Time:        {elapsed:.2f}s",
        ]
        console.print(Panel("\n".join(lines), title="Detection Result"))


@app.command()
def remove(
    input_path: str = typer.Argument(
        ..., help="Path to the watermarked input image."
    ),
    output_path: str = typer.Argument(
        ..., help="Path to save the cleaned output image."
    ),
    mode: str = typer.Option(
        "fast", "--mode", "-m", help="Removal mode: fast (V3 spectral) or full (V4 pipeline)."
    ),
    strength: Optional[str] = typer.Option(
        None, "--strength", "-s", help="Bypass strength. Fast: gentle/moderate/aggressive/maximum. Full: final/nuke."
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model hint for full mode codebook profile selection."
    ),
    codebook: Optional[str] = typer.Option(
        None, "--codebook", "-c", help="Path to a custom codebook (.npz)."
    ),
) -> None:
    """Remove SynthID watermark from an image."""
    import cv2

    # Validate input
    in_path = Path(input_path)
    if not in_path.exists():
        console.print(f"[red]Error:[/red] Input image not found: {input_path}")
        raise typer.Exit(code=1)

    if mode not in ("fast", "full"):
        console.print(f"[red]Error:[/red] Mode must be 'fast' or 'full', got '{mode}'")
        raise typer.Exit(code=1)

    # Load image
    img_bgr = cv2.imread(str(in_path))
    if img_bgr is None:
        console.print(f"[red]Error:[/red] Could not read image: {input_path}")
        raise typer.Exit(code=1)
    image = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Set default strength if not specified
    if strength is None:
        strength = "aggressive" if mode == "fast" else "final"

    with console.status(f"[bold blue]Removing watermark ({mode} mode)...[/bold blue]"):
        start = time.time()
        if mode == "fast":
            result = remove_fast(image, codebook_path=codebook, strength=strength)
        else:
            result = remove_full(
                image, codebook_path=codebook, strength=strength, model=model
            )
        elapsed = time.time() - start

    # Save output
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_bgr = cv2.cvtColor(result.cleaned_image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(out_path), out_bgr)

    # Print summary
    status_color = "green" if result.success else "red"
    lines = [
        f"Status:   [{status_color}]{'Success' if result.success else 'Failed'}[/{status_color}]",
        f"Mode:     {result.mode}",
        f"PSNR:     {result.psnr:.2f} dB",
        f"SSIM:     {result.ssim:.4f}",
        f"Stages:   {', '.join(result.stages_applied) if result.stages_applied else 'N/A'}",
        f"Time:     {elapsed:.2f}s",
        f"Output:   {output_path}",
    ]
    console.print(Panel("\n".join(lines), title="Removal Result"))


if __name__ == "__main__":
    app()
