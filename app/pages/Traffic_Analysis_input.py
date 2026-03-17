"""Traffic Analysis > Input: Read Data (Excel) and Direct Input sections."""
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
    QScrollArea,
    QDoubleSpinBox,
    QComboBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QShowEvent

from app.widgets.labeled_input import add_labeled_row
from app.widgets.button import secondary_button

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

# Options for dropdowns
TRAFFIC_COUNT_HOURS = ["6h", "8h", "12h", "24h"]
DESIGN_SPEED_OPTIONS = [f"{v} km/h" for v in (30, 40, 50, 60, 70, 80, 90, 100, 110, 120)]
LOS_OPTIONS = ["A", "B", "C", "D", "E", "F"]

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


from PyQt6.QtWidgets import QRadioButton, QVBoxLayout, QHBoxLayout, QWidget
def section_with_radio(
    title: str, parent: QWidget, header_widget: QWidget | None = None
) -> tuple[QWidget, QRadioButton, QFrame, QGridLayout]:
    """Return (section_widget, radio, frame, grid). Radio is outside frame for show/hide logic."""
    section_widget = QWidget(parent)
    section_layout = QVBoxLayout(section_widget)
    section_layout.setContentsMargins(0, 0, 0, 0)
    section_layout.setSpacing(4)

    # Title row with radio, title, (optional) button
    title_row = QHBoxLayout()
    radio = QRadioButton()
    radio.setChecked(True)
    radio.setStyleSheet("QRadioButton { margin-right: 8px; }")
    if _HAS_FLUENT and SubtitleLabel is not None:
        title_lbl = SubtitleLabel(title)
    else:
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
    title_row.addWidget(radio)
    title_row.addWidget(title_lbl)
    title_row.addStretch()
    if header_widget is not None:
        title_row.addWidget(header_widget)
    section_layout.addLayout(title_row)

    # The input card frame
    frame = QFrame(section_widget)
    frame.setObjectName("trafficSectionFrame")
    frame.setStyleSheet(
        "#trafficSectionFrame { background-color: transparent; border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(16, 12, 16, 16)
    outer.setSpacing(10)
    grid = QGridLayout()
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(10)
    grid.setContentsMargins(0, 0, 0, 0)
    outer.addLayout(grid)
    section_layout.addWidget(frame)
    return section_widget, radio, frame, grid


class TrafficAnalysisInputPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        if _HAS_FLUENT and SubtitleLabel is not None:
            page_title = SubtitleLabel("Traffic Analysis Input")
        else:
            page_title = QLabel("Traffic Analysis Input")
            page_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(page_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 8, 0, 0)
        scroll_layout.setSpacing(20)

        # ---------- Read Data (title and Read Excel button on same line) ----------
        read_excel_btn = secondary_button("Read Excel", min_height=36)
        read_excel_btn.clicked.connect(self._on_read_excel)

        # Section with radio logic for Read Data
        read_section, read_radio, read_frame, read_grid = section_with_radio("Read Data", scroll_content, header_widget=read_excel_btn)
        def toggle_read_frame(checked):
            read_frame.setVisible(checked)
        read_radio.toggled.connect(toggle_read_frame)
        read_frame.setVisible(True)

        self.read_r = _make_double_spin()
        self.read_r.setRange(0, 100)
        self.read_r.setDecimals(2)
        self.read_r.setSuffix(" %")
        self.read_r.setValue(3.0)
        add_labeled_row(read_grid, 0, "Traffic Growth Rate R =", self.read_r, ROW_HEIGHT)

        self.read_count_hour = _make_combo(TRAFFIC_COUNT_HOURS)
        add_labeled_row(read_grid, 1, "Traffic Count Hour =", self.read_count_hour, ROW_HEIGHT)

        self.read_design_speed = _make_combo(DESIGN_SPEED_OPTIONS)
        self.read_design_speed.setCurrentIndex(DESIGN_SPEED_OPTIONS.index("80 km/h"))
        add_labeled_row(read_grid, 2, "Design Speed V =", self.read_design_speed, ROW_HEIGHT)

        self.read_los = _make_combo(LOS_OPTIONS)
        add_labeled_row(read_grid, 3, "Level of Service LOS =", self.read_los, ROW_HEIGHT)

        scroll_layout.addWidget(read_section)

        # ---------- Direct Input ----------

        # Section with radio logic for Direct Input
        direct_section, direct_radio, direct_frame, direct_grid = section_with_radio("Direct Input", scroll_content)
        def toggle_direct_frame(checked):
            direct_frame.setVisible(checked)
        direct_radio.toggled.connect(toggle_direct_frame)
        direct_frame.setVisible(True)

        self.direct_r = _make_double_spin()
        self.direct_r.setRange(0, 100)
        self.direct_r.setDecimals(2)
        self.direct_r.setSuffix(" %")
        self.direct_r.setValue(3.0)
        add_labeled_row(direct_grid, 0, "Traffic Growth Rate R =", self.direct_r, ROW_HEIGHT)

        self.direct_count_hour = _make_combo(TRAFFIC_COUNT_HOURS)
        add_labeled_row(direct_grid, 1, "Traffic Count Hour =", self.direct_count_hour, ROW_HEIGHT)

        self.direct_design_speed = _make_combo(DESIGN_SPEED_OPTIONS)
        self.direct_design_speed.setCurrentIndex(DESIGN_SPEED_OPTIONS.index("80 km/h"))
        add_labeled_row(direct_grid, 2, "Design Speed V =", self.direct_design_speed, ROW_HEIGHT)

        self.direct_los = _make_combo(LOS_OPTIONS)
        add_labeled_row(direct_grid, 3, "Level of Service LOS =", self.direct_los, ROW_HEIGHT)

        self.direct_aadt = _make_double_spin()
        self.direct_aadt.setRange(0, 9999999)
        self.direct_aadt.setDecimals(0)
        add_labeled_row(direct_grid, 4, "Average Annual Daily Traffic AADT =", self.direct_aadt, ROW_HEIGHT)

        self.direct_pcu = _make_double_spin()
        self.direct_pcu.setRange(0, 100)
        self.direct_pcu.setDecimals(2)
        add_labeled_row(direct_grid, 5, "Passenger Car Unit PCU =", self.direct_pcu, ROW_HEIGHT)

        scroll_layout.addWidget(direct_section)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Configure preview panel (image + quick result schema with placeholders)
        self._setup_preview()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        # Ensure preview is configured whenever this page becomes visible
        self._setup_preview()

    def _setup_preview(self) -> None:
        mw = self.window()
        if not hasattr(mw, "preview_panel"):
            return

        # Set traffic analysis illustration as preview image
        mw.preview_panel.set_preview_from_asset("photo_2026-02-26_16-33-25.jpg")

        # Configure quick results schema for traffic analysis (UI only, no calculations yet)
        if hasattr(mw.preview_panel, "set_traffic_input_schema"):
            mw.preview_panel.set_traffic_input_schema()
        # Empty dict → all fields show with "—"
        mw.preview_panel.set_results({})

    def _on_read_excel(self):
        """Placeholder: open file dialog for Excel and populate Read Data fields."""
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Read Excel", "", "Excel (*.xlsx *.xls);;All Files (*)"
        )
        if path:
            # TODO: load Excel and set self.read_r, self.read_count_hour, etc.
            pass
