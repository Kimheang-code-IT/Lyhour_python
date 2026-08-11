"""Road Geometry Design > Cross Section."""
from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.chart import MatplotlibChartWidget, draw_cross_section
from app.core.theme import theme_tokens
from app.core.ui_style import section_title_style, title_style
from app.data.cross_section import build_cross_section
from app.layouts import BasePage, define_page
from app.widgets.form_controls import make_combo, make_double_spin
from app.widgets.labeled_input import add_labeled_row

BLOCK_SPACING = 24
ROW_HEIGHT = 36

ROAD_CLASS_OPTIONS = (
    "R1/U1",
    "R2/U2",
    "R3/U3",
    "R4/U4",
    "R5/U5",
    "R6/U6",
)


def _section_frame(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("crossSectionFrame")
    frame.setStyleSheet(
        "#crossSectionFrame { background-color: transparent; "
        "border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(12)

    title_label = QLabel(title)
    title_label.setStyleSheet(section_title_style(18))
    layout.addWidget(title_label)
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return frame, layout


def _set_input_height(widget: QWidget) -> None:
    widget.setMinimumHeight(ROW_HEIGHT)
    widget.setMaximumHeight(ROW_HEIGHT)


@define_page("blank", title="Cross Section")
class RGDCrossSectionPage(BasePage):
    """Cross Section: Input + live Design diagram from lane / shoulder / class / speed."""

    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(BLOCK_SPACING)

        title = QLabel("Cross Section")
        title.setStyleSheet(title_style(22))
        content.addWidget(title)

        content.addWidget(self._build_input_block())
        content.addWidget(self._build_design_block(), 1)

        QTimer.singleShot(0, self._refresh_design)

    def _build_input_block(self) -> QFrame:
        frame, section_layout = _section_frame("Input")
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        row = 0
        self.road_class_combo = make_combo(ROAD_CLASS_OPTIONS)
        self.road_class_combo.setCurrentText("R1/U1")
        _set_input_height(self.road_class_combo)
        self.road_class_combo.currentTextChanged.connect(self._refresh_design)
        add_labeled_row(grid, row, "Road classification =", self.road_class_combo, ROW_HEIGHT)
        row += 1

        self.design_speed_spin = make_double_spin()
        self.design_speed_spin.setRange(0.0, 200.0)
        self.design_speed_spin.setDecimals(0)
        self.design_speed_spin.setSuffix(" km/h")
        self.design_speed_spin.setValue(80.0)
        _set_input_height(self.design_speed_spin)
        self.design_speed_spin.valueChanged.connect(self._refresh_design)
        add_labeled_row(grid, row, "Design speed =", self.design_speed_spin, ROW_HEIGHT)
        row += 1

        self.lane_spin = make_double_spin()
        self.lane_spin.setRange(2.5, 20.0)
        self.lane_spin.setDecimals(2)
        self.lane_spin.setSuffix(" m")
        self.lane_spin.setValue(3.50)
        _set_input_height(self.lane_spin)
        self.lane_spin.valueChanged.connect(self._refresh_design)
        add_labeled_row(grid, row, "Lane =", self.lane_spin, ROW_HEIGHT)
        row += 1

        self.shoulder_spin = make_double_spin()
        self.shoulder_spin.setRange(0.5, 20.0)
        self.shoulder_spin.setDecimals(2)
        self.shoulder_spin.setSuffix(" m")
        self.shoulder_spin.setValue(2.50)
        _set_input_height(self.shoulder_spin)
        self.shoulder_spin.valueChanged.connect(self._refresh_design)
        add_labeled_row(grid, row, "Shoulder =", self.shoulder_spin, ROW_HEIGHT)

        grid.setColumnStretch(1, 1)
        section_layout.addWidget(grid_host)
        return frame

    def _build_design_block(self) -> QFrame:
        frame, section_layout = _section_frame("Design")

        self.design_chart = MatplotlibChartWidget(figsize=(10.0, 4.2))
        self.design_chart.setMinimumHeight(320)
        self.design_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        section_layout.addWidget(self.design_chart, 1)
        return frame

    def get_inputs(self) -> dict[str, float | str]:
        return {
            "road_classification": self.road_class_combo.currentText(),
            "design_speed_kmh": float(self.design_speed_spin.value()),
            "lane_m": float(self.lane_spin.value()),
            "shoulder_m": float(self.shoulder_spin.value()),
        }

    def _current_design(self):
        return build_cross_section(
            road_classification=self.road_class_combo.currentText(),
            design_speed_kmh=float(self.design_speed_spin.value()),
            lane_width_m=float(self.lane_spin.value()),
            shoulder_width_m=float(self.shoulder_spin.value()),
        )

    def _refresh_design(self, *_args) -> None:
        if self.design_chart.figure is None:
            return
        design = self._current_design()
        tokens = theme_tokens()
        self.design_chart.figure.clear()
        self.design_chart.figure.patch.set_facecolor(tokens.bg_card)
        ax = self.design_chart.add_subplot(111)
        draw_cross_section(ax, design)
        self.design_chart.figure.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.08)
        self.design_chart.redraw()
