"""Building Calculator page: form, Calculate + Preview PDF on one row, PDF preview in middle."""
import os
import shutil
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QGridLayout,
    QMessageBox,
    QFileDialog,
    QDoubleSpinBox,
    QSpinBox,
    QStackedWidget,
)
from PyQt6.QtGui import QShowEvent, QImage, QPixmap
from PyQt6.QtCore import Qt

from app.core.components.form_controls import make_spin_no_buttons
from app.services.building_calc import compute

try:
    import fitz  # PyMuPDF
    _HAS_PYMUPDF = True
except ImportError:
    _HAS_PYMUPDF = False


class CalculatorPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = {}
        self._pdf_preview_path = None

        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # Page 0: Calculator form
        form_page = QWidget()
        form_layout = QVBoxLayout(form_page)
        form_layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Building Calculator")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        form_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        form_widget = QWidget()
        form_grid = QGridLayout(form_widget)
        form_grid.setSpacing(12)
        row = 0

        def add_row(label_text: str, widget: QWidget):
            nonlocal row
            form_grid.addWidget(QLabel(label_text), row, 0)
            form_grid.addWidget(widget, row, 1)
            row += 1

        self.length_spin = make_spin_no_buttons(QDoubleSpinBox())
        self.length_spin.setRange(0.001, 999999)
        self.length_spin.setDecimals(3)
        self.length_spin.setSuffix(" m")
        self.length_spin.setValue(10.0)
        self.length_spin.valueChanged.connect(self._on_input_changed)
        add_row("Building length (m):", self.length_spin)

        self.width_spin = make_spin_no_buttons(QDoubleSpinBox())
        self.width_spin.setRange(0.001, 999999)
        self.width_spin.setDecimals(3)
        self.width_spin.setSuffix(" m")
        self.width_spin.setValue(8.0)
        self.width_spin.valueChanged.connect(self._on_input_changed)
        add_row("Building width (m):", self.width_spin)

        self.floors_spin = make_spin_no_buttons(QSpinBox())
        self.floors_spin.setRange(1, 99999)
        self.floors_spin.setValue(2)
        self.floors_spin.valueChanged.connect(self._on_input_changed)
        add_row("Number of floors:", self.floors_spin)

        self.floor_height_spin = make_spin_no_buttons(QDoubleSpinBox())
        self.floor_height_spin.setRange(0.001, 999)
        self.floor_height_spin.setDecimals(3)
        self.floor_height_spin.setSuffix(" m")
        self.floor_height_spin.setValue(3.0)
        self.floor_height_spin.valueChanged.connect(self._on_input_changed)
        add_row("Floor height (m):", self.floor_height_spin)

        self.thickness_spin = make_spin_no_buttons(QDoubleSpinBox())
        self.thickness_spin.setRange(0.001, 99)
        self.thickness_spin.setDecimals(3)
        self.thickness_spin.setSuffix(" m")
        self.thickness_spin.setValue(0.15)
        self.thickness_spin.valueChanged.connect(self._on_input_changed)
        add_row("Concrete thickness (m):", self.thickness_spin)

        self.density_spin = make_spin_no_buttons(QDoubleSpinBox())
        self.density_spin.setRange(1, 99999)
        self.density_spin.setDecimals(0)
        self.density_spin.setSuffix(" kg/m³")
        self.density_spin.setValue(2400.0)
        self.density_spin.valueChanged.connect(self._on_input_changed)
        add_row("Concrete density (kg/m³):", self.density_spin)

        self.cost_spin = make_spin_no_buttons(QDoubleSpinBox())
        self.cost_spin.setRange(0, 999999)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setSuffix(" per m³")
        self.cost_spin.setValue(0)
        self.cost_spin.setSpecialValueText("Optional")
        self.cost_spin.valueChanged.connect(self._on_input_changed)
        add_row("Cost per m³ (optional):", self.cost_spin)

        form_grid.setColumnStretch(1, 1)
        scroll.setWidget(form_widget)
        form_layout.addWidget(scroll, 1)

        # Same row: Calculate + Preview PDF
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        calc_btn = QPushButton("Calculate")
        calc_btn.setMinimumHeight(40)
        calc_btn.setStyleSheet("font-size: 14px;")
        calc_btn.clicked.connect(self._calculate)
        btn_row.addWidget(calc_btn)
        preview_pdf_btn = QPushButton("Preview PDF")
        preview_pdf_btn.setMinimumHeight(40)
        preview_pdf_btn.setStyleSheet("font-size: 14px;")
        preview_pdf_btn.clicked.connect(self._show_pdf_preview)
        btn_row.addWidget(preview_pdf_btn)
        form_layout.addLayout(btn_row)

        self.stack.addWidget(form_page)

        # Page 1: PDF preview (middle column shows rendered PDF)
        self.pdf_preview_page = self._build_pdf_preview_page()
        self.stack.addWidget(self.pdf_preview_page)

    def _build_pdf_preview_page(self) -> QWidget:
        """Build the PDF preview page: scroll area with rendered first page + Back and Download buttons."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        back_btn = QPushButton("← Back to Calculator")
        back_btn.setMinimumHeight(36)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_row.addWidget(back_btn)
        download_pdf_btn = QPushButton("Download this PDF")
        download_pdf_btn.setMinimumHeight(36)
        download_pdf_btn.clicked.connect(self._download_preview_pdf)
        btn_row.addWidget(download_pdf_btn)
        layout.addLayout(btn_row)
        self.pdf_preview_label = QLabel()
        self.pdf_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_preview_label.setMinimumSize(400, 500)
        self.pdf_preview_label.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 8px;")
        self.pdf_preview_label.setScaledContents(False)
        self.pdf_preview_label.setText("Generate PDF then click Preview PDF to see it here.")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setWidget(self.pdf_preview_label)
        layout.addWidget(scroll, 1)
        return page

    def _show_pdf_preview(self):
        """Generate current state to PDF, render first page to image, show in middle column."""
        if self._pdf_preview_path and Path(self._pdf_preview_path).exists():
            try:
                Path(self._pdf_preview_path).unlink()
            except Exception:
                pass
            self._pdf_preview_path = None
        ok, data = self._do_compute()
        if not ok:
            QMessageBox.warning(self, "Preview PDF", "Please fix inputs before previewing.")
            return
        r, inp = data
        self._results = {
            "floor_area": r.floor_area_m2,
            "volume": r.total_volume_m3,
            "mass": r.estimated_mass_kg,
            "cost": r.cost_estimate,
        }
        self._push_to_preview_and_state()
        from app.config.settings import APP_NAME
        from app.services.report_generator import generate_pdf
        image_path = None
        try:
            path = Path(__file__).resolve().parent.parent / "assets" / "image" / "road.jpg"
            if path.is_file():
                image_path = str(path)
        except Exception:
            pass
        try:
            fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            self._pdf_preview_path = pdf_path
            generate_pdf(
                pdf_path,
                title=f"{APP_NAME} – Building Report",
                inputs=self._get_inputs(),
                results=self._results,
                image_path=image_path,
            )
            if _HAS_PYMUPDF:
                doc = fitz.open(pdf_path)
                page = doc[0]
                pix = page.get_pixmap(dpi=120, alpha=False)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                doc.close()
                pm = QPixmap.fromImage(img).scaled(
                    600, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                self.pdf_preview_label.setPixmap(pm)
                self.pdf_preview_label.setText("")
            else:
                self.pdf_preview_label.setText("Install pymupdf to see PDF preview here.\n(Pip: pip install pymupdf)")
            self.stack.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.warning(self, "Preview PDF", f"Could not generate preview.\n{e}")
            if self._pdf_preview_path and Path(self._pdf_preview_path).exists():
                try:
                    Path(self._pdf_preview_path).unlink()
                except Exception:
                    pass
            self._pdf_preview_path = None

    def _download_preview_pdf(self):
        """Save the current preview PDF to a user-chosen path."""
        if not self._pdf_preview_path or not Path(self._pdf_preview_path).exists():
            QMessageBox.warning(self, "Download PDF", "No PDF to download. Generate a preview first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF As", "", "PDF (*.pdf);;All Files (*)")
        if not path:
            return
        if not path.endswith(".pdf"):
            path += ".pdf"
        try:
            shutil.copy2(self._pdf_preview_path, path)
            QMessageBox.information(self, "Download PDF", f"Saved: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Download PDF", f"Could not save file.\n{e}")

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self._on_input_changed()

    def _get_inputs(self):
        return {
            "length_m": self.length_spin.value(),
            "width_m": self.width_spin.value(),
            "num_floors": self.floors_spin.value(),
            "floor_height_m": self.floor_height_spin.value(),
            "concrete_thickness_m": self.thickness_spin.value(),
            "concrete_density_kg_m3": self.density_spin.value(),
            "cost_per_m3": self.cost_spin.value() if self.cost_spin.value() > 0 else None,
        }

    def _do_compute(self):
        inp = self._get_inputs()
        try:
            r = compute(
                length_m=inp["length_m"],
                width_m=inp["width_m"],
                num_floors=inp["num_floors"],
                floor_height_m=inp["floor_height_m"],
                concrete_thickness_m=inp["concrete_thickness_m"],
                concrete_density_kg_m3=inp["concrete_density_kg_m3"],
                cost_per_m3=inp["cost_per_m3"],
            )
            return True, (r, inp)
        except Exception as e:
            return False, str(e)

    def _calculate(self):
        ok, data = self._do_compute()
        if ok:
            r, inp = data
            self._results = {
                "floor_area": r.floor_area_m2,
                "volume": r.total_volume_m3,
                "mass": r.estimated_mass_kg,
                "cost": r.cost_estimate,
            }
            self._push_to_preview_and_state()
        else:
            QMessageBox.warning(self, "Invalid input", f"Please enter valid values.\n{data}")

    def _on_input_changed(self):
        ok, data = self._do_compute()
        if ok:
            r, inp = data
            self._results = {
                "floor_area": r.floor_area_m2,
                "volume": r.total_volume_m3,
                "mass": r.estimated_mass_kg,
                "cost": r.cost_estimate,
            }
            self._push_to_preview_and_state()

    def set_inputs(self, inp: dict):
        if not inp:
            return
        self.length_spin.blockSignals(True)
        self.width_spin.blockSignals(True)
        self.floors_spin.blockSignals(True)
        self.floor_height_spin.blockSignals(True)
        self.thickness_spin.blockSignals(True)
        self.density_spin.blockSignals(True)
        self.cost_spin.blockSignals(True)
        try:
            self.length_spin.setValue(float(inp.get("length_m", 10)))
            self.width_spin.setValue(float(inp.get("width_m", 8)))
            self.floors_spin.setValue(int(inp.get("num_floors", 2)))
            self.floor_height_spin.setValue(float(inp.get("floor_height_m", 3)))
            self.thickness_spin.setValue(float(inp.get("concrete_thickness_m", 0.15)))
            self.density_spin.setValue(float(inp.get("concrete_density_kg_m3", 2400)))
            self.cost_spin.setValue(float(inp.get("cost_per_m3") or 0))
        finally:
            self.length_spin.blockSignals(False)
            self.width_spin.blockSignals(False)
            self.floors_spin.blockSignals(False)
            self.floor_height_spin.blockSignals(False)
            self.thickness_spin.blockSignals(False)
            self.density_spin.blockSignals(False)
            self.cost_spin.blockSignals(False)
        self._on_input_changed()

    def _push_to_preview_and_state(self):
        mw = self.window()
        if not hasattr(mw, "preview_panel"):
            return
        mw.preview_panel.set_results(self._results)
        if hasattr(mw, "calc_state"):
            mw.calc_state["inputs"] = self._get_inputs()
            mw.calc_state["results"] = self._results.copy()
