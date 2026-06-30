"""PDF preview service: temp PDF creation and render to QPixmap; QThreadPool for no UI freeze."""
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QThreadPool, QRunnable, QTimer

from app.services.report_generator import generate_pdf

try:
    import fitz  # PyMuPDF
    _HAS_PYMUPDF = True
except ImportError:
    _HAS_PYMUPDF = False


def create_temp_pdf(
    inputs: dict[str, Any],
    results: dict[str, Any],
    *,
    title: str = "Building Report",
    image_path: str | Path | None = None,
) -> str:
    """Create a temporary PDF file; returns path. Caller must unlink when done."""
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    from pathlib import Path
    logo_path = Path(__file__).parent.parent / "assets" / "image" / "KIEC_logo.png"
    generate_pdf(
        pdf_path,
        title=title,
        inputs=inputs,
        results=results,
        image_path=image_path,
        logo_path=logo_path,
    )
    return pdf_path


def create_preview_pixmap(
    pdf_path: str | Path,
    max_width: int = 600,
    max_height: int = 800,
) -> QPixmap | None:
    """Render first page of PDF to QPixmap. Returns None if PyMuPDF not available or error."""
    if not _HAS_PYMUPDF:
        return None
    try:
        doc = fitz.open(str(pdf_path))
        p0 = doc[0]
        pix = p0.get_pixmap(dpi=120, alpha=False)
        img = QImage(
            pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888
        )
        doc.close()
        return QPixmap.fromImage(img).scaled(
            max_width, max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    except Exception:
        return None


def has_pymupdf() -> bool:
    return _HAS_PYMUPDF


def create_temp_pdf_async(
    inputs: dict[str, Any],
    results: dict[str, Any],
    on_done: Callable[[str], None],
    *,
    title: str = "Building Report",
    image_path: str | Path | None = None,
) -> None:
    """Create temp PDF in QThreadPool; call on_done(pdf_path) on main thread when done."""
    from pathlib import Path
    logo_path = Path(__file__).parent.parent / "assets" / "image" / "KIEC_logo.png"
    class _Task(QRunnable):
        def run(self):
            try:
                path = create_temp_pdf(
                    inputs, results, title=title, image_path=image_path, logo_path=logo_path
                )
                QTimer.singleShot(0, lambda: on_done(path))
            except Exception as e:
                QTimer.singleShot(0, lambda: on_done(""))
    QThreadPool.globalInstance().start(_Task())
