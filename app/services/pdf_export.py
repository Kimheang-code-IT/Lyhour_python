"""PDF export service: thin wrapper around report generator."""
from pathlib import Path
from typing import Any

from app.services.report_generator import generate_pdf


def export_pdf(
    path: str | Path,
    *,
    title: str = "Building Report",
    inputs: dict[str, Any],
    results: dict[str, Any],
    image_path: str | Path | None = None,
) -> None:
    """Write a PDF report to path. Uses features.pdf.report_generator.generate_pdf."""
    generate_pdf(
        output_path=path,
        title=title,
        inputs=inputs,
        results=results,
        image_path=image_path,
    )
