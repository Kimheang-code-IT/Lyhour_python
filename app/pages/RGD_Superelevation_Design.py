"""Road Geometry Design > Superelevation Design. UI: vehicle speed, e1, e_max, road classification, lane width."""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
    QScrollArea,
    QDoubleSpinBox,
    QComboBox,
    QSizePolicy,
)
from PyQt6.QtGui import QShowEvent

from app.widgets.labeled_input import add_labeled_row

try:
    from qfluentwidgets import (
        ComboBox as FluentComboBox,
        DoubleSpinBox as FluentDoubleSpinBox,
        SubtitleLabel,
    )
    _HAS_FLUENT = True
except Exception:
    FluentComboBox = None  # type: ignore[assignment]
    FluentDoubleSpinBox = None  # type: ignore[assignment]
    SubtitleLabel = None  # type: ignore[assignment]
    _HAS_FLUENT = False

VEHICLE_SPEED_OPTIONS = [f"{v} km/h" for v in (25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130)]
ROAD_CLASSIFICATION_OPTIONS = ["Class I", "Class II", "Class III", "Rural", "Urban"]

ROW_HEIGHT = 36


def _make_double_spin() -> QDoubleSpinBox:
    """Numeric input without increment/decrement icons."""
    if _HAS_FLUENT and FluentDoubleSpinBox is not None:
        w = FluentDoubleSpinBox()
        w.setSymbolVisible(False)
    else:
        w = QDoubleSpinBox()
        w.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    return w


def _make_combo(items: list[str]):
    """Dropdown with Fluent style when available."""
    if _HAS_FLUENT and FluentComboBox is not None:
        cb = FluentComboBox()
    else:
        cb = QComboBox()
    cb.addItems(items)
    return cb


class RGDSuperelevationDesignPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        if _HAS_FLUENT and SubtitleLabel is not None:
            page_title = SubtitleLabel("Superelevation Design")
        else:
            page_title = QLabel("Superelevation Design")
            page_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(page_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        form_widget = QFrame()
        form_widget.setObjectName("inputSectionFrame")
        form_widget.setStyleSheet(
            "#inputSectionFrame { background-color: transparent; border: 1px solid #3e3e40; border-radius: 6px; }"
        )
        form_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        form_grid = QGridLayout(form_widget)
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(14)
        form_grid.setContentsMargins(16, 12, 16, 16)

        row = 0

        # Vehicle speed
        self.vehicle_speed_combo = _make_combo(VEHICLE_SPEED_OPTIONS)
        self.vehicle_speed_combo.setCurrentIndex(VEHICLE_SPEED_OPTIONS.index("80 km/h"))
        add_labeled_row(form_grid, row, "Vehicle speed V =", self.vehicle_speed_combo, ROW_HEIGHT)
        row += 1

        # Gross fall e1
        self.e1_spin = _make_double_spin()
        self.e1_spin.setRange(-10, 10)
        self.e1_spin.setDecimals(2)
        self.e1_spin.setSuffix(" %")
        self.e1_spin.setValue(2.5)
        add_labeled_row(form_grid, row, "Gross fall e1 =", self.e1_spin, ROW_HEIGHT)
        row += 1

        # Pavement Superelevation (e_max)
        self.e_max_spin = _make_double_spin()
        self.e_max_spin.setRange(2.5, 20)
        self.e_max_spin.setDecimals(2)
        self.e_max_spin.setSuffix(" %")
        self.e_max_spin.setValue(5.0)
        add_labeled_row(
            form_grid, row, "Pavement Superelevation (e_max) =", self.e_max_spin, ROW_HEIGHT
        )
        row += 1

        # Road Classification (dropdown)
        self.road_class_combo = _make_combo(ROAD_CLASSIFICATION_OPTIONS)
        add_labeled_row(form_grid, row, "Road Classification =", self.road_class_combo, ROW_HEIGHT)
        row += 1

        # Lane width WR
        self.lane_width_spin = _make_double_spin()
        self.lane_width_spin.setRange(2.5, 5.0)
        self.lane_width_spin.setDecimals(2)
        self.lane_width_spin.setSuffix(" m")
        self.lane_width_spin.setValue(3.5)
        add_labeled_row(form_grid, row, "Lane width WR =", self.lane_width_spin, ROW_HEIGHT)

        form_grid.setColumnStretch(1, 1)
        scroll.setWidget(form_widget)
        layout.addWidget(scroll, 1)

        # Configure preview panel with superelevation schema
        self._setup_preview()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        # Ensure preview is configured whenever this page becomes visible
        self._setup_preview()

    def _setup_preview(self) -> None:
        mw = self.window()
        if not hasattr(mw, "preview_panel"):
            return

        # Configure quick results schema for superelevation design
        if hasattr(mw.preview_panel, "set_superelevation_schema"):
            mw.preview_panel.set_superelevation_schema()
        # Empty dict → all fields show with "—"
        mw.preview_panel.set_results({})
