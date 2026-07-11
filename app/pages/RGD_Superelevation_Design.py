"""Superelevation Design."""
from __future__ import annotations

from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.layouts import BasePage, define_page
from app.core.ui_style import section_title_style, title_style
from app.data.superelevation_profile import (
    compute_superelevation_profile,
    draw_superelevation_profile,
)
from app.widgets.chart_ui import MatplotlibChartWidget
from app.widgets.form_controls import make_combo, make_double_spin
from app.widgets.labeled_input import add_labeled_row
from app.widgets.button import secondary_button
from app.widgets.scroll_utils import configure_hidden_scrollbars

VEHICLE_SPEED_OPTIONS = [f"{v} km/h" for v in (25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130)]
ROAD_CLASSIFICATION_OPTIONS = ["Class I", "Class II", "Class III", "Rural", "Urban"]

ROW_HEIGHT = 36
BLOCK_SPACING = 24
SECTION_TITLE_STYLE = section_title_style(18)


@define_page("blank", title="Superelevation Design")
class RGDSuperelevationDesignPage(BasePage):
    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._page_title = QLabel("Superelevation Design")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        content.addLayout(title_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        configure_hidden_scrollbars(scroll)

        scroll_content = QWidget()
        page_layout = QVBoxLayout(scroll_content)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(BLOCK_SPACING)

        input_widget = QFrame()
        input_widget.setObjectName("inputSectionFrame")
        input_widget.setStyleSheet(
            "#inputSectionFrame { background-color: transparent; border: 1px solid #3e3e40; border-radius: 6px; }"
        )
        input_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(16, 12, 16, 16)
        input_layout.setSpacing(12)

        self.input_title = QLabel("Input")
        self.input_title.setStyleSheet(SECTION_TITLE_STYLE)
        input_layout.addWidget(self.input_title)

        fields_host = QWidget()
        form_grid = QGridLayout(fields_host)
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(14)
        form_grid.setContentsMargins(0, 0, 0, 0)

        row = 0

        self.vehicle_speed_combo = make_combo(VEHICLE_SPEED_OPTIONS)
        self.vehicle_speed_combo.setCurrentIndex(VEHICLE_SPEED_OPTIONS.index("80 km/h"))
        self.vehicle_speed_combo.currentTextChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Vehicle speed V =", self.vehicle_speed_combo, ROW_HEIGHT)
        row += 1

        self.e1_spin = make_double_spin()
        self.e1_spin.setRange(-10, 10)
        self.e1_spin.setDecimals(2)
        self.e1_spin.setSuffix(" %")
        self.e1_spin.setValue(2.5)
        self.e1_spin.valueChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Gross fall e1 =", self.e1_spin, ROW_HEIGHT)
        row += 1

        self.e_max_spin = make_double_spin()
        self.e_max_spin.setRange(2.5, 20)
        self.e_max_spin.setDecimals(2)
        self.e_max_spin.setSuffix(" %")
        self.e_max_spin.setValue(5.0)
        self.e_max_spin.valueChanged.connect(self._on_input_changed)
        add_labeled_row(
            form_grid, row, "Pavement Superelevation (e_max) =", self.e_max_spin, ROW_HEIGHT
        )
        row += 1

        self.road_class_combo = make_combo(ROAD_CLASSIFICATION_OPTIONS)
        self.road_class_combo.currentTextChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Road Classification =", self.road_class_combo, ROW_HEIGHT)
        row += 1

        self.lane_width_spin = make_double_spin()
        self.lane_width_spin.setRange(2.5, 5.0)
        self.lane_width_spin.setDecimals(2)
        self.lane_width_spin.setSuffix(" m")
        self.lane_width_spin.setValue(3.5)
        self.lane_width_spin.valueChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Lane width WR =", self.lane_width_spin, ROW_HEIGHT)
        row += 1

        self.relative_gradient_spin = make_double_spin()
        self.relative_gradient_spin.setRange(0.01, 5.0)
        self.relative_gradient_spin.setDecimals(3)
        self.relative_gradient_spin.setSuffix(" %")
        self.relative_gradient_spin.setValue(0.30)
        self.relative_gradient_spin.setToolTip("Rate of change for edge rotation")
        self.relative_gradient_spin.valueChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Relative gradient =", self.relative_gradient_spin, ROW_HEIGHT)
        row += 1

        self.curve_length_spin = make_double_spin()
        self.curve_length_spin.setRange(0.0, 10_000.0)
        self.curve_length_spin.setDecimals(2)
        self.curve_length_spin.setSuffix(" m")
        self.curve_length_spin.setValue(106.74)
        self.curve_length_spin.valueChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Curve length Lc =", self.curve_length_spin, ROW_HEIGHT)
        row += 1

        self.start_station_spin = make_double_spin()
        self.start_station_spin.setRange(0.0, 1_000_000.0)
        self.start_station_spin.setDecimals(2)
        self.start_station_spin.setSuffix(" m")
        self.start_station_spin.setValue(16_200.0)
        self.start_station_spin.setToolTip("Start station in metres, shown as 16+200 on the graph")
        self.start_station_spin.valueChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Start station =", self.start_station_spin, ROW_HEIGHT)

        form_grid.setColumnStretch(1, 1)
        input_layout.addWidget(fields_host)
        page_layout.addWidget(input_widget)

        analysis_widget = QFrame()
        analysis_widget.setObjectName("analysisSectionFrame")
        analysis_widget.setStyleSheet(
            "#analysisSectionFrame { background-color: transparent; border: 1px solid #3e3e40; border-radius: 6px; }"
        )
        analysis_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        analysis_layout = QVBoxLayout(analysis_widget)
        analysis_layout.setContentsMargins(16, 12, 16, 16)
        analysis_layout.setSpacing(12)

        self.analysis_title = QLabel("Analysis")
        self.analysis_title.setStyleSheet(SECTION_TITLE_STYLE)
        analysis_layout.addWidget(self.analysis_title)

        self.analysis_summary_label = QLabel("")
        self.analysis_summary_label.setWordWrap(True)
        self.analysis_summary_label.setStyleSheet("color: #cccccc; font-size: 13px; padding: 4px 0;")
        analysis_layout.addWidget(self.analysis_summary_label)

        self.analysis_chart = MatplotlibChartWidget(figsize=(9.0, 4.5))
        self.analysis_chart.setMinimumHeight(360)
        analysis_layout.addWidget(self.analysis_chart, 1)

        page_layout.addWidget(analysis_widget, 1)
        scroll.setWidget(scroll_content)
        content.addWidget(scroll, 1)
        self._on_input_changed()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._setup_quick_panel()
        self._refresh_analysis()
        self._sync_quick_panel_button()

    def activate_page(self) -> None:
        self._setup_quick_panel()
        self._refresh_analysis()
        self._sync_quick_panel_button()

    def _toggle_quick_panel(self) -> None:
        mw = self.window()
        if hasattr(mw, "toggle_quick_panel"):
            self.sync_quick_panel_button(mw.toggle_quick_panel())

    def sync_quick_panel_button(self, visible: bool | None = None) -> None:
        if visible is None:
            mw = self.window()
            visible = hasattr(mw, "is_quick_panel_visible") and mw.is_quick_panel_visible()
        self.quick_panel_btn.setText("Hide Quick Result" if visible else "Show Quick Result")

    def _sync_quick_panel_button(self) -> None:
        self.sync_quick_panel_button()

    def _setup_quick_panel(self) -> None:
        mw = self.window()
        if not hasattr(mw, "quick_panel"):
            return
        if hasattr(mw.quick_panel, "set_superelevation_schema"):
            mw.quick_panel.set_superelevation_schema()
        mw.quick_panel.set_results(self._results())

    def _profile(self):
        return compute_superelevation_profile(
            e1_percent=float(self.e1_spin.value()),
            e_max_percent=float(self.e_max_spin.value()),
            lane_width_m=float(self.lane_width_spin.value()),
            relative_gradient_percent=float(self.relative_gradient_spin.value()),
            curve_length_m=float(self.curve_length_spin.value()),
            start_station_m=float(self.start_station_spin.value()),
        )

    def _results(self) -> dict[str, float]:
        profile = self._profile()
        if profile is None:
            return {}
        return {
            "Transition Length Le": profile.transition_length_m,
            "Tro": profile.tro_m,
            "Sro": profile.sro_m,
            "Curve length": profile.curve_length_m,
        }

    def _on_input_changed(self, *_args) -> None:
        self._refresh_analysis()
        self._setup_quick_panel()

    def _refresh_analysis(self) -> None:
        if not hasattr(self, "analysis_chart"):
            return

        profile = self._profile()
        if profile is None:
            self.analysis_summary_label.setText("Please enter valid superelevation values.")
            if self.analysis_chart.figure is not None:
                self.analysis_chart.clear()
            return

        self.analysis_summary_label.setText(
            "Le = {:.2f} m   |   Tro = {:.2f} m   |   Sro = {:.2f} m   |   "
            "Curve length = {:.2f} m".format(
                profile.transition_length_m,
                profile.tro_m,
                profile.sro_m,
                profile.curve_length_m,
            )
        )

        if self.analysis_chart.figure is None:
            return

        self.analysis_chart.figure.clear()
        ax = self.analysis_chart.add_subplot(111)
        draw_superelevation_profile(ax, profile)
        fig = self.analysis_chart.figure
        fig.subplots_adjust(bottom=0.18, left=0.11, right=0.78, top=0.94)
        self.analysis_chart.canvas.draw()
