"""
Road Geometry Design > Horizontal Curvature
- R_min formula
- Table lookup
- Verification
- Simple-curve diagram + Engineering Results (summary / stakeout)
- PDF preview + download
"""

import shutil
from pathlib import Path

from qfluentwidgets import SegmentedWidget

from app.data.tables_Horizontal_Curvature import (
    calc_rmin,
    calc_rmin_ongrade,
    lookup_rmin_table,
    get_f_options_for_table_7_5,
)
from app.data.simple_curve_geometry import (
    compute_curve_stakeout,
    compute_simple_curve_elements,
    format_angle_dms,
)
from app.data.vertical_curve import format_station
from app.services import pdf_preview as pdf_preview_svc
from app.core.theme import theme_tokens
from app.core.ui_style import section_title_style, title_style
from app.widgets.labeled_input import add_labeled_row
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content
from app.widgets.button import primary_button, secondary_button

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QGridLayout,
    QMessageBox,
    QFileDialog,
    QStackedWidget,
    QComboBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
)
from PyQt6.QtGui import QColor, QShowEvent
from PyQt6.QtCore import Qt

from app.chart import MatplotlibChartWidget, draw_simple_curve_diagram
from app.widgets.form_controls import make_combo, make_double_spin


try:
    from app.config.settings import APP_NAME
except Exception:
    APP_NAME = "Report"


# Vehicle speed options (km/h) — discrete values per Table 7.5 / 7.6
VEHICLE_SPEED_OPTIONS = [25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130]
ROW_HEIGHT = 36
BLOCK_SPACING = 16
LEFT_WIDTH = 420
STAKE_INTERVAL_M = 20.0
SECTION_TITLE_STYLE = section_title_style(16)

# Friction factor type → hint text shown next to combo
FRICTION_HINTS = {
    "Des max": "(Desired Maximum)",
    "Ads max": "(Absoluted Maximum)",
}

# Options per Surface Type: Sealed roads → (Vehicle Type list, Friction factor type list)
SURFACE_OPTIONS = {
    "Sealed roads": (
        ["Truck", "Car"],           # Vehicle Type
        ["Des max", "Ads max"],     # Friction factor type
    ),
    "Unsealed roads": (
        ["Cars and Trucks"],        # Vehicle Type
        ["Des max"],               # Friction factor type
    ),
}


def _section_frame(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("horizontalCurveSection")
    frame.setStyleSheet(
        "#horizontalCurveSection { background-color: transparent; "
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


def _set_combo_items(combo: QComboBox, items: list[str], current: str | None = None) -> None:
    """Replace combo items; set current to current if in list else first."""
    combo.blockSignals(True)
    try:
        combo.clear()
        combo.addItems(items)
        if current and current in items:
            i = combo.findText(current)
            if i >= 0:
                combo.setCurrentIndex(i)
            else:
                combo.setCurrentIndex(0)
        else:
            combo.setCurrentIndex(0)
    finally:
        combo.blockSignals(False)


class RGDHorizontalCurvaturePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._results = {}
        self._pdf_preview_path: str | None = None

        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(24, 24, 24, 0)
        title_row.setSpacing(12)
        self._page_title = QLabel("Horizontal Curvature")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.preview_pdf_btn = secondary_button("Preview PDF", min_height=36)
        self.preview_pdf_btn.clicked.connect(self._show_pdf_preview)
        title_row.addWidget(self.preview_pdf_btn)
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        layout.addLayout(title_row)

        layout.addWidget(self.stack)

        # -------------------------
        # Page 0: Form
        # -------------------------
        form_page = self._build_form_page()

        # -------------------------
        # Page 1: PDF Preview
        # -------------------------
        self.pdf_preview_page = self._build_pdf_preview_page()

        self.stack.addWidget(form_page)
        self.stack.addWidget(self.pdf_preview_page)

        self._on_input_changed()

    # -------------------------
    # Layout: Form (two columns)
    # -------------------------
    def _build_form_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        body = QHBoxLayout()
        body.setSpacing(BLOCK_SPACING)
        body.addWidget(self._build_input_column(), 0)
        body.addWidget(self._build_result_column(), 1)
        layout.addLayout(body, 1)
        return page

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
        layout.addWidget(self._build_input_card())
        layout.addWidget(self._build_design_card())
        self.calculate_btn = primary_button("Calculate Geometry", min_height=40, icon="fa5s.bolt")
        self.calculate_btn.clicked.connect(self._calculate)
        layout.addWidget(self.calculate_btn)
        layout.addStretch(0)
        scroll.setWidget(inner)
        configure_page_scroll(scroll)
        outer.addWidget(scroll, 1)
        return host

    def _build_input_card(self) -> QFrame:
        frame, layout = _section_frame("Input")
        grid_host = QWidget()
        form_grid = QGridLayout(grid_host)
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(14)
        form_grid.setContentsMargins(0, 0, 0, 0)

        row = 0
        speed_items = [f"{s} km/h" for s in VEHICLE_SPEED_OPTIONS]
        self.v_combo = make_combo(speed_items, editable=False)
        self.v_combo.setCurrentIndex(speed_items.index("90 km/h"))  # default 90 km/h
        self.v_combo.currentTextChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Vehicle Speed V =", self.v_combo, ROW_HEIGHT)
        row += 1

        # Superelevation (e_max >= 2.5%) — Fluent DoubleSpinBox when available
        self.e_spin = make_double_spin()
        self.e_spin.setRange(2.5, 20)
        self.e_spin.setDecimals(2)
        self.e_spin.setSuffix(" %")
        self.e_spin.setToolTip("Pavement superelevation e_max >= 2.5%")
        self.e_spin.valueChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Pavement Superelevation (e_max) =", self.e_spin, ROW_HEIGHT)
        row += 1

        # Surface Type (Selection only recommended)
        self.surface_combo = make_combo(["Sealed roads", "Unsealed roads"], editable=False)
        self.surface_combo.setCurrentIndex(0)
        self.surface_combo.currentTextChanged.connect(self._on_surface_changed)
        add_labeled_row(form_grid, row, "Surface Type =", self.surface_combo, ROW_HEIGHT)
        row += 1

        # Vehicle Type (depends on Surface: Sealed → Truck/Car; Unsealed → Cars and Trucks)
        vehicles, frictions = SURFACE_OPTIONS["Sealed roads"]
        self.vehicle_combo = make_combo(vehicles, editable=False)
        self.vehicle_combo.setCurrentIndex(0)
        self.vehicle_combo.currentTextChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Vehicle Type =", self.vehicle_combo, ROW_HEIGHT)
        row += 1

        # Friction type (depends on Surface: Sealed → Des max/Ads max; Unsealed → Des max)
        self.friction_type_combo = make_combo(frictions, editable=False)
        self.friction_type_combo.setToolTip("Des max = Desired Maximum; Ads max = Absolute Maximum")
        self.friction_type_combo.currentTextChanged.connect(self._on_friction_changed)

        friction_wrap = QWidget()
        friction_layout = QHBoxLayout(friction_wrap)
        friction_layout.setContentsMargins(0, 0, 0, 0)
        friction_layout.setSpacing(8)
        friction_layout.addWidget(self.friction_type_combo, 1)

        self.friction_hint_label = QLabel(FRICTION_HINTS.get(self.friction_type_combo.currentText(), "(Desired Maximum)"))
        self.friction_hint_label.setStyleSheet("color: #888;")
        friction_layout.addWidget(self.friction_hint_label, 0)

        add_labeled_row(form_grid, row, "Friction factor type =", friction_wrap, ROW_HEIGHT)
        row += 1

        # Side friction factor (from Table 7.5; options depend on V, surface, vehicle, friction type)
        self.f_combo = make_combo(["0.12"], editable=False)  # populated in _update_f_combo_from_table
        self.f_combo.setToolTip("From Table 7.5 Recommended side friction factors")
        self.f_combo.currentTextChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Maximum Side friction factor f_min=", self.f_combo, ROW_HEIGHT)
        row += 1

        # Grading (>= 3%) — Fluent DoubleSpinBox when available
        self.grading_spin = make_double_spin()
        self.grading_spin.setRange(3.0, 100.0)
        self.grading_spin.setDecimals(2)
        self.grading_spin.setSuffix(" %")
        self.grading_spin.setToolTip("Grading >= 3%")
        self.grading_spin.valueChanged.connect(self._on_input_changed)
        add_labeled_row(form_grid, row, "Grading =", self.grading_spin, ROW_HEIGHT)

        form_grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        return frame

    def _build_design_card(self) -> QFrame:
        frame, layout = _section_frame("Design")
        grid_host = QWidget()
        design_grid = QGridLayout(grid_host)
        design_grid.setHorizontalSpacing(12)
        design_grid.setVerticalSpacing(14)
        design_grid.setContentsMargins(0, 0, 0, 0)

        self.design_pc_station_spin = make_double_spin()
        self.design_pc_station_spin.setRange(0.0, 1_000_000.0)
        self.design_pc_station_spin.setDecimals(2)
        self.design_pc_station_spin.setSuffix(" m")
        self.design_pc_station_spin.setValue(1000.0)
        self.design_pc_station_spin.setToolTip("PC station used to number the stakeout points")
        self.design_pc_station_spin.valueChanged.connect(self._on_design_changed)
        add_labeled_row(design_grid, 0, "PC station =", self.design_pc_station_spin, ROW_HEIGHT)

        self.design_radius_spin = make_double_spin()
        self.design_radius_spin.setRange(1.0, 50_000.0)
        self.design_radius_spin.setDecimals(3)
        self.design_radius_spin.setSuffix(" m")
        self.design_radius_spin.setValue(400.0)
        self.design_radius_spin.setToolTip("Curve radius R")
        self.design_radius_spin.valueChanged.connect(self._on_design_changed)
        add_labeled_row(design_grid, 1, "Radius R =", self.design_radius_spin, ROW_HEIGHT)

        self.design_deflection_spin = make_double_spin()
        self.design_deflection_spin.setRange(0.01, 179.99)
        self.design_deflection_spin.setDecimals(4)
        self.design_deflection_spin.setSuffix(" °")
        self.design_deflection_spin.setValue(79.0 + 14.0 / 60.0 + 55.17 / 3600.0)
        self.design_deflection_spin.setToolTip("Deflection angle Δ at PI")
        self.design_deflection_spin.valueChanged.connect(self._on_design_changed)
        add_labeled_row(design_grid, 2, "Deflection angle Δ =", self.design_deflection_spin, ROW_HEIGHT)

        design_grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        return frame

    def _build_result_column(self) -> QWidget:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)

        chart_frame, chart_layout = _section_frame("Profile")
        chart_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.design_chart = MatplotlibChartWidget(figsize=(8.5, 5.0))
        self.design_chart.setMinimumHeight(300)
        chart_layout.addWidget(self.design_chart, 1)

        toggles = QHBoxLayout()
        toggles.setSpacing(16)
        self.show_tangents = QCheckBox("Show Tangents")
        self.show_radius = QCheckBox("Show Radius")
        self.show_labels = QCheckBox("Show Labels")
        self.show_stations = QCheckBox("Show Stations")
        for box in (self.show_tangents, self.show_radius, self.show_labels, self.show_stations):
            box.setChecked(True)
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
        self.summary_table = self._make_table(("Parameter", "Value", "Status"), rows=10)
        self.stakeout_table = self._make_table(
            ("Point", "Station", "Deflection", "Chord (m)", "X (m)", "Y (m)"),
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

    # -------------------------
    # Design block
    # -------------------------
    def _on_design_changed(self, *_args) -> None:
        self._refresh_design()

    def _refresh_design(self) -> None:
        radius = float(self.design_radius_spin.value())
        deflection = float(self.design_deflection_spin.value())
        elements = compute_simple_curve_elements(radius, deflection)

        if elements is None:
            self.summary_table.setRowCount(0)
            self.stakeout_table.setRowCount(0)
            if self.design_chart.figure is not None:
                self.design_chart.clear()
            return

        self._fill_summary(elements)
        self._fill_stakeout(elements)
        self._redraw_chart(elements)

    def _sync_design_radius_from_results(self) -> None:
        r_calc = self._results.get("Minimum Radius")
        if r_calc is None:
            return
        try:
            value = float(r_calc)
        except (TypeError, ValueError):
            return
        if value <= 0:
            return
        self.design_radius_spin.blockSignals(True)
        self.design_radius_spin.setValue(round(value, 3))
        self.design_radius_spin.blockSignals(False)

    # -------------------------
    # Charts
    # -------------------------
    def _redraw_chart(self, *_args) -> None:
        if self.design_chart.figure is None or self.design_chart.canvas is None:
            return
        elements = compute_simple_curve_elements(
            float(self.design_radius_spin.value()),
            float(self.design_deflection_spin.value()),
        )
        self.design_chart.figure.clear()
        if elements is None:
            self.design_chart.canvas.draw_idle()
            return
        ax = self.design_chart.figure.add_subplot(111)
        draw_simple_curve_diagram(
            ax,
            elements,
            show_tangents=self.show_tangents.isChecked(),
            show_radius=self.show_radius.isChecked(),
            show_labels=self.show_labels.isChecked(),
            show_stations=self.show_stations.isChecked(),
        )
        try:
            self.design_chart.figure.tight_layout()
        except Exception:
            pass
        self.design_chart.canvas.draw_idle()

    # -------------------------
    # Engineering Results
    # -------------------------
    def _fill_summary(self, elements) -> None:
        r_calc = self._results.get("Minimum Radius")
        r_table = self._results.get("Minimum Radius from table")
        r_ongrade = self._results.get("Minimum radius on grade R_min_ongrade")
        verification = str(self._results.get("Verification") or "")
        if "Not Ok" in verification:
            status = "FAIL"
        elif "Ok" in verification:
            status = "PASS"
        else:
            status = ""

        def _metres(value) -> str:
            try:
                return f"{float(value):.3f} m"
            except (TypeError, ValueError):
                return "—"

        rows = (
            ("Radius R", f"{elements.radius_m:.3f} m", ""),
            ("Deflection Δ", format_angle_dms(elements.deflection_deg), ""),
            ("Tangent length TL", f"{elements.tangent_length_m:.3f} m", ""),
            ("Curve length L", f"{elements.curve_length_m:.3f} m", ""),
            ("Long chord C", f"{elements.chord_length_m:.3f} m", ""),
            ("External distance E", f"{elements.external_distance_m:.3f} m", ""),
            ("Middle ordinate M", f"{elements.middle_ordinate_m:.3f} m", ""),
            ("Minimum radius R_min", _metres(r_calc), status),
            ("Minimum radius from table", _metres(r_table), ""),
            ("Minimum radius on grade", _metres(r_ongrade), ""),
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

    def _fill_stakeout(self, elements) -> None:
        points = compute_curve_stakeout(
            elements.radius_m,
            elements.deflection_deg,
            pc_station_m=float(self.design_pc_station_spin.value()),
            interval_m=STAKE_INTERVAL_M,
        )
        self.stakeout_table.setRowCount(len(points))
        for r, point in enumerate(points):
            values = (
                point.name,
                format_station(point.station_m),
                format_angle_dms(point.deflection_deg) if point.deflection_deg is not None else "—",
                f"{point.chord_m:.3f}" if point.chord_m is not None else "—",
                f"{point.x_m:.3f}",
                f"{point.y_m:.3f}",
            )
            for c, text in enumerate(values):
                self.stakeout_table.setItem(r, c, QTableWidgetItem(text))

    # -------------------------
    # UI: PDF Preview Page
    # -------------------------
    def _build_pdf_preview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        back_btn = secondary_button("← Back to Calculator", min_height=36)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_row.addWidget(back_btn)

        download_pdf_btn = secondary_button("Download this PDF", min_height=36)
        download_pdf_btn.clicked.connect(self._download_preview_pdf)
        btn_row.addWidget(download_pdf_btn)

        layout.addLayout(btn_row)

        self.pdf_preview_label = QLabel()
        self.pdf_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_preview_label.setMinimumSize(400, 500)
        self.pdf_preview_label.setStyleSheet(
            "background-color: #1e1e1e; border-radius: 4px; padding: 8px;"
        )
        self.pdf_preview_label.setScaledContents(False)
        self.pdf_preview_label.setText("Generate PDF then click Preview PDF to see it here.")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setWidget(self.pdf_preview_label)
        configure_page_scroll(scroll)

        layout.addWidget(scroll, 1)
        return page

    # -------------------------
    # Qt Events
    # -------------------------
    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        # Avoid full recalculation + chart redraw on every revisit.
        self._sync_quick_panel_button()
        self._push_to_quick_panel_and_state()

    def activate_page(self) -> None:
        self._push_to_quick_panel_and_state()
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

    def _on_surface_changed(self, surface_text: str):
        """Update Vehicle Type and Friction factor type options based on Surface Type."""
        opts = SURFACE_OPTIONS.get(surface_text)
        if not opts:
            return
        vehicles, frictions = opts
        current_vehicle = self.vehicle_combo.currentText() if self.vehicle_combo.currentText() else None
        current_friction = self.friction_type_combo.currentText() if self.friction_type_combo.currentText() else None
        _set_combo_items(self.vehicle_combo, vehicles, current_vehicle)
        _set_combo_items(self.friction_type_combo, frictions, current_friction)
        self._update_friction_hint()
        self._on_input_changed()

    def _update_friction_hint(self):
        """Set hint label next to Friction factor type from current selection."""
        text = self.friction_type_combo.currentText()
        self.friction_hint_label.setText(FRICTION_HINTS.get(text, ""))

    def _on_friction_changed(self, text: str):
        self._update_friction_hint()
        self._on_input_changed()

    def _update_f_combo_from_table(self) -> None:
        """Populate f_min combo from Table 7.5 based on current V, surface, vehicle, friction type."""
        try:
            V = float(self.v_combo.currentText().replace(" km/h", "").strip())
        except Exception:
            V = 90.0
        surface = str(self.surface_combo.currentText())
        vehicle = str(self.vehicle_combo.currentText())
        friction_type = str(self.friction_type_combo.currentText())
        options = get_f_options_for_table_7_5(V, surface, vehicle, friction_type)
        items = [f"{f:.2f}" for f in options]
        if not items:
            items = ["0.12"]
        current_f = self.f_combo.currentText()
        try:
            current_val = float(current_f)
        except Exception:
            current_val = options[0] if options else 0.12
        select = f"{current_val:.2f}" if current_val in options and f"{current_val:.2f}" in items else items[0]
        _set_combo_items(self.f_combo, items, select)

    # -------------------------
    # Data / Compute
    # -------------------------
    def _get_inputs(self):
        return {
            "V_km_h": float(self.v_combo.currentText().replace(" km/h", "").strip()),
            "e_percent": float(self.e_spin.value()),
            "surface_type": str(self.surface_combo.currentText()),
            "vehicle_type": str(self.vehicle_combo.currentText()),
            "friction_factor_type": str(self.friction_type_combo.currentText()),
            "f": float(self.f_combo.currentText()),
            "grading_percent": float(self.grading_spin.value()),
        }

    def _validate_inputs(self, inp: dict) -> str | None:
        """
        Enforce limits per manual:
        - Pavement superelevation e_max >= 2.5% (Section 7.4.1; tables use e from 3%).
        - Grading (grade G) >= 3% (Equation 7.5: "grade over 3%").
        """
        if inp.get("e_percent", 0) < 2.5:
            return "Pavement superelevation e_max must be >= 2.5%."
        if inp.get("grading_percent", 0) < 3.0:
            return "Grading (grade G) must be >= 3% (Equation 7.5)."
        return None

    def _do_compute(self):
        try:
            inp = self._get_inputs()
            err = self._validate_inputs(inp)
            if err:
                return False, err

            V = inp["V_km_h"]
            e = inp["e_percent"]
            f = inp["f"]
            surface = inp["surface_type"]
            grading = inp["grading_percent"]

            r_calc = calc_rmin(V, e, f)
            r_table, table_name = lookup_rmin_table(V, e, surface)
            r_min_ongrade = calc_rmin_ongrade(r_calc, grading)

            if r_table is not None:
                verification = "Rmin_Table < Rmin (Ok)" if r_table < r_calc else "Rmin_Table < Rmin (Not Ok)"
            else:
                verification = "— (no table data)"
                table_name = ""

            return True, (r_calc, r_table, verification, table_name, r_min_ongrade, inp)
        except Exception as ex:
            return False, str(ex)

    def _results_from_compute(self, data):
        r_calc, r_table, verification, _table_name, r_min_ongrade, _inp = data
        self._results = {
            "Minimum Radius": r_calc,
            "Minimum Radius from table": r_table,
            "Verification": verification,
            "Minimum radius on grade R_min_ongrade": r_min_ongrade,
        }
        self._sync_design_radius_from_results()
        self._refresh_design()
        self._push_to_preview_and_state()

    # -------------------------
    # Actions
    # -------------------------
    def _calculate(self):
        ok, data = self._do_compute()
        if ok:
            self._results_from_compute(data)
        else:
            QMessageBox.warning(self, "Invalid input", f"Please enter valid values.\n{data}")

    def _on_input_changed(self, *_args):
        self._update_f_combo_from_table()
        ok, data = self._do_compute()
        if ok:
            self._results_from_compute(data)

    def _show_pdf_preview(self):
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

        self._results_from_compute(data)

        image_path = None
        try:
            path = Path(__file__).resolve().parent.parent / "assets" / "image" / "road.jpg"
            if path.is_file():
                image_path = str(path)
        except Exception:
            pass

        try:
            self._pdf_preview_path = pdf_preview_svc.create_temp_pdf(
                self._get_inputs(),
                self._results,
                title=f"{APP_NAME} – Building Report",
                image_path=image_path,
            )

            if pdf_preview_svc.has_pymupdf():
                pm = pdf_preview_svc.create_preview_pixmap(self._pdf_preview_path, 600, 800)
                if pm and not pm.isNull():
                    self.pdf_preview_label.setPixmap(pm)
                    self.pdf_preview_label.setText("")
                else:
                    self.pdf_preview_label.setText("Could not render PDF preview.")
            else:
                self.pdf_preview_label.setText(
                    "Install pymupdf to see PDF preview here.\n(Pip: pip install pymupdf)"
                )

            self.stack.setCurrentIndex(1)

        except Exception as ex:
            QMessageBox.warning(self, "Preview PDF", f"Could not generate preview.\n{ex}")
            if self._pdf_preview_path and Path(self._pdf_preview_path).exists():
                try:
                    Path(self._pdf_preview_path).unlink()
                except Exception:
                    pass
            self._pdf_preview_path = None

    def _download_preview_pdf(self):
        if not self._pdf_preview_path or not Path(self._pdf_preview_path).exists():
            QMessageBox.warning(self, "Download PDF", "No PDF to download. Generate a preview first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save PDF As", "", "PDF (*.pdf);;All Files (*)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            shutil.copy2(self._pdf_preview_path, path)
            QMessageBox.information(self, "Download PDF", f"Saved: {path}")
        except Exception as ex:
            QMessageBox.warning(self, "Download PDF", f"Could not save file.\n{ex}")

    # -------------------------
    # External state sync
    # -------------------------
    def set_inputs(self, inp: dict):
        if not inp:
            return

        self.v_combo.blockSignals(True)
        self.e_spin.blockSignals(True)
        self.f_combo.blockSignals(True)
        self.grading_spin.blockSignals(True)
        self.surface_combo.blockSignals(True)
        self.vehicle_combo.blockSignals(True)
        self.friction_type_combo.blockSignals(True)

        try:
            v_kmh = float(inp.get("V_km_h", 90))
            best = min(VEHICLE_SPEED_OPTIONS, key=lambda x: abs(x - v_kmh))
            i = self.v_combo.findText(f"{int(best)} km/h")
            if i >= 0:
                self.v_combo.setCurrentIndex(i)
            self.e_spin.setValue(float(inp.get("e_percent", 5)))
            self.grading_spin.setValue(float(inp.get("grading_percent", 3.0)))

            if inp.get("surface_type"):
                i = self.surface_combo.findText(str(inp["surface_type"]))
                if i >= 0:
                    self.surface_combo.setCurrentIndex(i)

            if inp.get("vehicle_type"):
                i = self.vehicle_combo.findText(str(inp["vehicle_type"]))
                if i >= 0:
                    self.vehicle_combo.setCurrentIndex(i)

            if inp.get("friction_factor_type"):
                i = self.friction_type_combo.findText(str(inp["friction_factor_type"]))
                if i >= 0:
                    self.friction_type_combo.setCurrentIndex(i)

        finally:
            self.v_combo.blockSignals(False)
            self.e_spin.blockSignals(False)
            self.f_combo.blockSignals(False)
            self.grading_spin.blockSignals(False)
            self.surface_combo.blockSignals(False)
            self.vehicle_combo.blockSignals(False)
            self.friction_type_combo.blockSignals(False)

        self._on_input_changed()

    def _push_to_quick_panel_and_state(self):
        mw = self.window()
        if hasattr(mw, "quick_panel"):
            try:
                if hasattr(mw.quick_panel, "set_horizontal_curvature_schema"):
                    mw.quick_panel.set_horizontal_curvature_schema()
                mw.quick_panel.set_results(self._results)
            except Exception:
                pass

        if hasattr(mw, "calc_state"):
            try:
                mw.calc_state["inputs"] = self._get_inputs()
                mw.calc_state["results"] = self._results.copy()
            except Exception:
                pass

    def _push_to_preview_and_state(self):
        self._push_to_quick_panel_and_state()
