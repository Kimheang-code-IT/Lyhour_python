"""ReportLab-based PDF report: title, date, tables, embedded image."""
import io
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image


def generate_pdf(
    output_path: str | Path | io.BytesIO,
    *,
    title: str = "Building Report",
    inputs: dict[str, Any],
    results: dict[str, Any],
    image_path: str | Path | None = None,
    logo_path: str | Path | None = None,
) -> None:
    """Write a PDF report to output_path (file path or BytesIO)."""
    doc = SimpleDocTemplate(
        str(output_path) if not isinstance(output_path, io.BytesIO) else output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    # Add logo at the top if provided
    if logo_path and Path(logo_path).exists():
        try:
            img = Image(str(logo_path), width=6*cm, height=2.5*cm)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 10))
        except Exception:
            pass

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Spacer(1, 24))

    input_rows = [["Parameter", "Value"]]
    for k, v in inputs.items():
        if isinstance(v, float):
            input_rows.append([k.replace("_", " ").title(), f"{v:,.2f}"])
        else:
            input_rows.append([k.replace("_", " ").title(), str(v)])
    t1 = Table(input_rows, colWidths=[10 * cm, 6 * cm])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#222")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#444")),
    ]))
    story.append(t1)
    story.append(Spacer(1, 20))

    # Display labels and unit suffix for outputs (radius values get " m")
    OUTPUT_LABELS = {
        "Min Radius": "Minimum radius R_min",
        "Min Radius from table": "Minimum radius from table",
        "Min radius on grade R_min_ongrade": "Minimum radius on grade R_min_ongrade",
        "Verification": "Verification",
    }
    RADIUS_KEYS = {"Minimum Radius", "Minimum Radius from table", "Minimum radius on grade R_min_ongrade"}

    result_rows = [["Output", "Value"]]
    for k, v in results.items():
        label = OUTPUT_LABELS.get(k, k.replace("_", " ").title())
        if v is None:
            result_rows.append([label, "—"])
        elif isinstance(v, float):
            value_str = f"{v:,.2f} m" if k in RADIUS_KEYS else f"{v:,.2f}"
            result_rows.append([label, value_str])
        else:
            result_rows.append([label, str(v)])
    t2 = Table(result_rows, colWidths=[10 * cm, 6 * cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#222")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#444")),
    ]))
    story.append(t2)
    story.append(Spacer(1, 20))



    doc.build(story)
