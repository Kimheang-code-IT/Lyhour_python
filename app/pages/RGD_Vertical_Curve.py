"""Road Geometry Design > Vertical Curve."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QShowEvent
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import SegmentedWidget

from app.chart import MatplotlibChartWidget
from app.chart.vertical_curve import draw_vertical_curve
from app.core.theme import theme_tokens
from app.core.ui_style import section_title_style, title_style
from app.data.vertical_curve import (
    CURVE_TYPE_OPTIONS,
    DESIGN_SPEEDS,
    SIGHT_CRITERION_OPTIONS,
    STANDARD_OPTIONS,
    classify_curve,
    compute_vertical_curve,
    format_station,
)
from app.layouts import BasePage, define_page
from app.widgets.button import primary_button, secondary_button
from app.widgets.form_controls import make_combo, make_double_spin, make_radio
from app.widgets.labeled_input import add_labeled_row
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content

ROW_HEIGHT = 36
BLOCK_SPACING = 16
LEFT_WIDTH = 390
SECTION_TITLE_STYLE = section_title_style(16)


def _section_frame(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("verticalCurveSection")
    frame.setStyleSheet(
        "#verticalCurveSection { background-color: transparent; "
        "border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 10, 14, 12)
    layout.setSpacing(10)
    title_label = QLabel(title)
    title_label.setStyleSheet(SECTION_TITLE_STYLE)
    layout.addWidget(title_label)
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return frame, layout


def _set_height(widget: QWidget) -> None:
    widget.setMinimumHeight(ROW_HEIGHT)
    widget.setMaximumHeight(ROW_HEIGHT)


@define_page("blank", title="Vertical Curve")
class RGDVerticalCurvePage(BasePage):
    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(12)
        self._ready = False
        self._syncing = False
        self._result = None

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._page_title = QLabel("Vertical Curve")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        content.addLayout(title_row)

        body = QHBoxLayout()
        body.setSpacing(BLOCK_SPACING)
        body.addWidget(self._build_input_column(), 0)
        body.addWidget(self._build_result_column(), 1)
        content.addLayout(body, 1)

        self._ready = True
        self._refresh()

    def _build_input_column(self) -> QWidget:
        host = QWidget()
        host.setMinimumWidth(LEFT_WIDTH)
        host.setMaximumWidth(LEFT_WIDTH + 40)
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        inner = QWidget()
        fit_scroll_content(inner)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)
        layout.addWidget(self._build_design_card())
        layout.addWidget(self._build_grade_card())
        layout.addWidget(self._build_pvi_card())
        layout.addWidget(self._build_length_card())
        self.calculate_btn = primary_button("Calculate Geometry", min_height=40, icon="fa5s.bolt")
        self.calculate_btn.clicked.connect(self._refresh)
        layout.addWidget(self.calculate_btn)
        layout.addStretch(0)
        scroll.setWidget(inner)
        configure_page_scroll(scroll)
        outer.addWidget(scroll, 1)
        return host

    def _spin(self, *, value: float, decimals: int = 2, minimum: float = -1e6, maximum: float = 1e6, suffix: str = ""):
        spin = make_double_spin()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setValue(value)
        if suffix:
            spin.setSuffix(suffix)
        _set_height(spin)
        spin.valueChanged.connect(self._on_changed)
        return spin

    def _combo(self, items: tuple[str, ...] | list[str], current: str):
        combo = make_combo(list(items))
        _set_height(combo)
        idx = combo.findText(current)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.currentTextChanged.connect(self._on_changed)
        return combo

    def _build_design_card(self) -> QFrame:
        frame, layout = _section_frame("Design Parameters")
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)

        self.curve_type_combo = self._combo(CURVE_TYPE_OPTIONS, "Crest")
        self.curve_type_combo.currentTextChanged.disconnect(self._on_changed)
        self.curve_type_combo.currentTextChanged.connect(self._on_curve_type_changed)

        self.speed_combo = self._combo([str(v) for v in DESIGN_SPEEDS], "80")
        self.sight_combo = self._combo(SIGHT_CRITERION_OPTIONS, "Stopping SD")
        self.standard_combo = self._combo(STANDARD_OPTIONS, "AASHTO 2018")

        add_labeled_row(grid, 0, "Curve type =", self.curve_type_combo, ROW_HEIGHT)
        add_labeled_row(grid, 1, "Design speed (km/h) =", self.speed_combo, ROW_HEIGHT)
        add_labeled_row(grid, 2, "Sight distance criterion =", self.sight_combo, ROW_HEIGHT)
        add_labeled_row(grid, 3, "Standard =", self.standard_combo, ROW_HEIGHT)
        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        return frame

    def _build_grade_card(self) -> QFrame:
        frame, layout = _section_frame("Grade Data")
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        self.g1_spin = self._spin(value=3.00, decimals=2, minimum=-20.0, maximum=20.0, suffix=" %")
        self.g2_spin = self._spin(value=-1.50, decimals=2, minimum=-20.0, maximum=20.0, suffix=" %")
        self.a_label = QLabel("—")
        self.a_label.setStyleSheet(f"color: {theme_tokens().accent}; font-weight: 700;")
        add_labeled_row(grid, 0, "Grade 1, g₁ =", self.g1_spin, ROW_HEIGHT)
        add_labeled_row(grid, 1, "Grade 2, g₂ =", self.g2_spin, ROW_HEIGHT)
        add_labeled_row(grid, 2, "Alg. Diff. A =", self.a_label, ROW_HEIGHT)
        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        return frame

    def _build_pvi_card(self) -> QFrame:
        frame, layout = _section_frame("PVI Location")
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        self.pvi_sta_spin = self._spin(value=1250.0, decimals=2, minimum=0.0, maximum=1_000_000.0, suffix=" m")
        self.pvi_elev_spin = self._spin(value=118.50, decimals=2, minimum=-500.0, maximum=5000.0, suffix=" m")
        add_labeled_row(grid, 0, "PVI station =", self.pvi_sta_spin, ROW_HEIGHT)
        add_labeled_row(grid, 1, "PVI elevation =", self.pvi_elev_spin, ROW_HEIGHT)
        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        return frame

    def _build_length_card(self) -> QFrame:
        frame, layout = _section_frame("Curve Length")
        self.length_mode_l = make_radio("Define by design length L (m)", checked=True)
        self.length_mode_k = make_radio("Target K-factor")
        self._length_mode_group = QButtonGroup(self)
        self._length_mode_group.addButton(self.length_mode_l)
        self._length_mode_group.addButton(self.length_mode_k)
        self.length_mode_l.toggled.connect(self._on_length_mode_changed)
        layout.addWidget(self.length_mode_l)
        layout.addWidget(self.length_mode_k)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        self.length_spin = self._spin(value=120.0, decimals=2, minimum=1.0, maximum=5000.0, suffix=" m")
        self.k_spin = self._spin(value=26.0, decimals=2, minimum=0.1, maximum=2000.0)
        add_labeled_row(grid, 0, "Design length L =", self.length_spin, ROW_HEIGHT)
        add_labeled_row(grid, 1, "K-factor =", self.k_spin, ROW_HEIGHT)
        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        self._apply_length_mode()
        return frame

    def _build_result_column(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)

        chart_frame, chart_layout = _section_frame("Profile")
        chart_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.chart = MatplotlibChartWidget(figsize=(9.5, 4.4))
        self.chart.setMinimumHeight(280)
        chart_layout.addWidget(self.chart, 1)

        toggles = QHBoxLayout()
        toggles.setSpacing(16)
        self.show_tangents = QCheckBox("Show Tangents")
        self.show_turning = QCheckBox("Show High/Low Point")
        self.show_ground = QCheckBox("Show Existing Ground")
        self.show_sd = QCheckBox("SD Envelope")
        for box in (self.show_tangents, self.show_turning, self.show_sd):
            box.setChecked(True)
        for box in (self.show_tangents, self.show_turning, self.show_ground, self.show_sd):
            box.setStyleSheet("color: #cccccc;")
            box.toggled.connect(self._redraw_chart)
            toggles.addWidget(box)
        toggles.addStretch()
        chart_layout.addLayout(toggles)
        layout.addWidget(chart_frame, 3)

        results_frame, results_layout = _section_frame("Engineering Results")
        self.results_segmented = SegmentedWidget()
        self.results_stack = QStackedWidget()
        self.results_segmented.addItem(
            "summary", "Geometric Summary", onClick=lambda: self.results_stack.setCurrentIndex(0)
        )
        self.results_segmented.addItem(
            "stakeout", "Stakeout Data", onClick=lambda: self.results_stack.setCurrentIndex(1)
        )
        self.results_segmented.setCurrentItem("summary")
        results_layout.addWidget(self.results_segmented)
        self.summary_table = self._make_table(("Parameter", "Value", "Status"), rows=8)
        self.stakeout_table = self._make_table(
            ("Station", "Tangent Elev (m)", "Correction y (m)", "Final Curve Elev (m)"),
            rows=0,
        )
        self.results_stack.addWidget(self.summary_table)
        self.results_stack.addWidget(self.stakeout_table)
        results_layout.addWidget(self.results_stack, 1)
        layout.addWidget(results_frame, 2)
        return host

    def _make_table(self, headers: tuple[str, ...], *, rows: int) -> QTableWidget:
        table = QTableWidget(rows, len(headers))
        table.setHorizontalHeaderLabels(list(headers))
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(180)
        return table

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def activate_page(self) -> None:
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def _on_curve_type_changed(self, text: str) -> None:
        if self._syncing or not self._ready:
            return
        classified = classify_curve(self.g1_spin.value(), self.g2_spin.value())
        if classified is not None and classified != text:
            self._syncing = True
            try:
                g1 = self.g1_spin.value()
                g2 = self.g2_spin.value()
                self.g1_spin.setValue(g2)
                self.g2_spin.setValue(g1)
            finally:
                self._syncing = False
        self._refresh()

    def _on_length_mode_changed(self, *_args) -> None:
        self._apply_length_mode()
        self._refresh()

    def _apply_length_mode(self) -> None:
        by_length = self.length_mode_l.isChecked()
        self.length_spin.setEnabled(by_length)
        self.k_spin.setEnabled(not by_length)

    def _on_changed(self, *_args) -> None:
        if not self._ready or self._syncing:
            return
        classified = classify_curve(self.g1_spin.value(), self.g2_spin.value())
        if classified is not None and classified != self.curve_type_combo.currentText():
            self._syncing = True
            try:
                self.curve_type_combo.setCurrentText(classified)
            finally:
                self._syncing = False
        self._refresh()

    def _current_result(self):
        by_k = self.length_mode_k.isChecked()
        return compute_vertical_curve(
            curve_type=self.curve_type_combo.currentText(),  # type: ignore[arg-type]
            g1_percent=float(self.g1_spin.value()),
            g2_percent=float(self.g2_spin.value()),
            pvi_station_m=float(self.pvi_sta_spin.value()),
            pvi_elev_m=float(self.pvi_elev_spin.value()),
            length_m=None if by_k else float(self.length_spin.value()),
            target_k=float(self.k_spin.value()) if by_k else None,
            speed_kmh=float(self.speed_combo.currentText()),
            sight_criterion=self.sight_combo.currentText(),  # type: ignore[arg-type]
        )

    def _refresh(self) -> None:
        if not self._ready:
            return
        result = self._current_result()
        self._result = result
        self.a_label.setText(f"{result.a_percent:.3f} %")
        self._syncing = True
        try:
            if self.length_mode_k.isChecked():
                self.length_spin.setValue(result.length_m)
            elif result.k_provided is not None:
                self.k_spin.setValue(result.k_provided)
        finally:
            self._syncing = False
        self._fill_summary(result)
        self._fill_stakeout(result)
        self._redraw_chart()
        self._push_quick_results()

    def _redraw_chart(self, *_args) -> None:
        if self.chart.figure is None or self.chart.canvas is None:
            return
        self.chart.figure.clear()
        ax = self.chart.figure.add_subplot(111)
        draw_vertical_curve(
            ax,
            self._result,
            show_tangents=self.show_tangents.isChecked(),
            show_turning_point=self.show_turning.isChecked(),
            show_existing_ground=self.show_ground.isChecked(),
            show_sd_envelope=self.show_sd.isChecked(),
        )
        try:
            self.chart.figure.tight_layout()
        except Exception:
            pass
        self.chart.canvas.draw_idle()

    def _fill_summary(self, result) -> None:
        turning_name = "High point" if result.curve_type == "Crest" else "Low point"
        turning_sta = (
            format_station(result.turning_station_m) if result.turning_station_m is not None else "—"
        )
        turning_elv = f"{result.turning_elev_m:.2f} m" if result.turning_elev_m is not None else "—"
        if result.design_ok is True:
            status = "AASHTO SSD PASS"
        elif result.design_ok is False:
            status = "AASHTO SSD FAIL"
        else:
            status = "—"
        k_prov = f"{result.k_provided:.3f}" if result.k_provided is not None else "—"
        k_req = f"{result.k_required:.3f}" if result.k_required is not None else "—"
        rows = (
            ("Curve classification", result.curve_type, ""),
            ("Required K-factor", k_req, status),
            ("Provided K-factor", k_prov, status),
            ("Curve length L", f"{result.length_m:.2f} m", ""),
            ("PVC", f"{format_station(result.pvc_station_m)}  /  {result.pvc_elev_m:.2f} m", ""),
            ("PVI", f"{format_station(result.pvi_station_m)}  /  {result.pvi_elev_m:.2f} m", ""),
            ("PVT", f"{format_station(result.pvt_station_m)}  /  {result.pvt_elev_m:.2f} m", ""),
            (turning_name, f"{turning_sta}  /  {turning_elv}", ""),
        )
        self.summary_table.setRowCount(len(rows))
        accent = QColor(theme_tokens().accent)
        for r, (name, value, badge) in enumerate(rows):
            self.summary_table.setItem(r, 0, QTableWidgetItem(name))
            value_item = QTableWidgetItem(value)
            value_item.setForeground(accent)
            self.summary_table.setItem(r, 1, value_item)
            badge_item = QTableWidgetItem(badge)
            if "PASS" in badge:
                badge_item.setForeground(QColor("#4caf7a"))
            elif "FAIL" in badge:
                badge_item.setForeground(QColor("#e07070"))
            self.summary_table.setItem(r, 2, badge_item)

    def _fill_stakeout(self, result) -> None:
        self.stakeout_table.setRowCount(len(result.stakeout))
        for r, row in enumerate(result.stakeout):
            values = (
                format_station(row.station_m),
                f"{row.tangent_elev_m:.3f}",
                f"{row.correction_y_m:.3f}",
                f"{row.curve_elev_m:.3f}",
            )
            for c, text in enumerate(values):
                self.stakeout_table.setItem(r, c, QTableWidgetItem(text))

    def quick_results(self) -> dict[str, str]:
        r = self._result
        if r is None:
            return {}
        out = {
            "Curve type": r.curve_type,
            "Length L": f"{r.length_m:.2f} m",
            "A": f"{r.a_percent:.3f} %",
        }
        if r.k_provided is not None:
            out["Provided K"] = f"{r.k_provided:.2f}"
        if r.k_required is not None:
            out["Required K"] = f"{r.k_required:.2f}"
        out["PVC"] = format_station(r.pvc_station_m)
        out["PVT"] = format_station(r.pvt_station_m)
        if r.design_ok is True:
            out["Check"] = "PASS"
        elif r.design_ok is False:
            out["Check"] = "FAIL"
        return out

    def _setup_quick_panel(self) -> None:
        mw = self.window()
        if not hasattr(mw, "quick_panel"):
            return
        if hasattr(mw.quick_panel, "set_vertical_curve_schema"):
            mw.quick_panel.set_vertical_curve_schema()
        mw.quick_panel.set_results(self.quick_results())

    def _push_quick_results(self) -> None:
        self._setup_quick_panel()

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
