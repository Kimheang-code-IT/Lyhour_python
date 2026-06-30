"""Traffic Analysis > Input: Read Data (Excel) and Direct Input sections."""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QRadioButton,
    QButtonGroup,
)

from app.core.components.form_controls import (
    make_combo,
    make_decimal_line_edit,
    make_double_spin,
    make_integer_line_edit,
)
from app.services.traffic_excel import read_traffic_investigation_workbook
from app.widgets.labeled_input import add_labeled_row
from app.widgets.button import secondary_button

try:
    from qfluentwidgets import SubtitleLabel
    _HAS_FLUENT = True
except Exception:
    SubtitleLabel = None  # type: ignore[assignment]
    _HAS_FLUENT = False

# Options for dropdowns
READ_TRAFFIC_COUNT_HOURS = ["12h", "24h"]
TRAFFIC_COUNT_HOURS = ["6h", "8h", "12h", "24h"]
DESIGN_SPEED_OPTIONS = [f"{v} km/h" for v in (30, 40, 50, 60, 70, 80, 90, 100, 110, 120)]
DESIGN_YEAR_OPTIONS = [f"{v} year" for v in (5, 10, 15, 20, 25, 30, 35, 40)]
LOS_OPTIONS = ["A", "B", "C", "D", "E", "F"]

ROW_HEIGHT = 36


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
        title_row = QHBoxLayout()
        title_row.addWidget(page_title)
        title_row.addStretch()

        read_excel_btn = secondary_button("Read Excel", min_height=36)
        read_excel_btn.clicked.connect(self._on_read_excel)
        title_row.addWidget(read_excel_btn)

        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        layout.addLayout(title_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 8, 0, 0)
        scroll_layout.setSpacing(20)

        # Section with radio logic for Read Data
        read_section, read_radio, read_frame, read_grid = section_with_radio("Read Data", scroll_content)

        self.read_r = make_double_spin()
        self.read_r.setRange(0, 100)
        self.read_r.setDecimals(2)
        self.read_r.setSuffix(" %")
        self.read_r.setValue(3.0)
        add_labeled_row(read_grid, 0, "Traffic Growth Rate R =", self.read_r, ROW_HEIGHT)
        self.read_r.valueChanged.connect(self._on_growth_rate_changed)

        self.read_count_hour = make_combo(READ_TRAFFIC_COUNT_HOURS)
        add_labeled_row(read_grid, 1, "Traffic Count Hour =", self.read_count_hour, ROW_HEIGHT)
        self.read_count_hour.currentTextChanged.connect(self._on_read_count_hour_changed)

        self.read_design_speed = make_combo(DESIGN_SPEED_OPTIONS)
        self.read_design_speed.setCurrentIndex(DESIGN_SPEED_OPTIONS.index("80 km/h"))
        add_labeled_row(read_grid, 2, "Design Speed V =", self.read_design_speed, ROW_HEIGHT)

        self.read_geometry_design_year = make_combo(DESIGN_YEAR_OPTIONS)
        add_labeled_row(read_grid, 3, "Design year for Geometry =", self.read_geometry_design_year, ROW_HEIGHT)
        self.read_geometry_design_year.currentTextChanged.connect(self._on_geometry_design_year_changed)

        self.read_pavement_design_year = make_combo(DESIGN_YEAR_OPTIONS)
        add_labeled_row(read_grid, 4, "Design year for Pavement =", self.read_pavement_design_year, ROW_HEIGHT)
        self.read_pavement_design_year.currentTextChanged.connect(self._on_pavement_design_year_changed)

        self.read_los = make_combo(LOS_OPTIONS)
        add_labeled_row(read_grid, 5, "Level of Service LOS =", self.read_los, ROW_HEIGHT)

        scroll_layout.addWidget(read_section)

        # ---------- Direct Input ----------

        # Section with radio logic for Direct Input
        direct_section, direct_radio, direct_frame, direct_grid = section_with_radio("Direct Input", scroll_content)

        self.input_mode_group = QButtonGroup(self)
        self.input_mode_group.setExclusive(True)
        self.input_mode_group.addButton(read_radio, 0)
        self.input_mode_group.addButton(direct_radio, 1)

        def update_visible_section() -> None:
            read_frame.setVisible(read_radio.isChecked())
            direct_frame.setVisible(direct_radio.isChecked())

        read_radio.toggled.connect(lambda _checked: update_visible_section())
        direct_radio.toggled.connect(lambda _checked: update_visible_section())
        read_radio.toggled.connect(lambda _checked: self._on_input_mode_changed())
        direct_radio.toggled.connect(lambda _checked: self._on_input_mode_changed())
        read_radio.toggled.connect(lambda _checked: self._on_geometry_design_year_changed())
        direct_radio.toggled.connect(lambda _checked: self._on_geometry_design_year_changed())
        read_radio.blockSignals(True)
        direct_radio.blockSignals(True)
        direct_radio.setChecked(False)
        read_radio.setChecked(True)
        read_radio.blockSignals(False)
        direct_radio.blockSignals(False)
        update_visible_section()

        self.direct_r = make_double_spin()
        self.direct_r.setRange(0, 100)
        self.direct_r.setDecimals(2)
        self.direct_r.setSuffix(" %")
        self.direct_r.setValue(3.0)
        add_labeled_row(direct_grid, 0, "Traffic Growth Rate R =", self.direct_r, ROW_HEIGHT)
        self.direct_r.valueChanged.connect(self._on_growth_rate_changed)

        self.direct_count_hour = make_combo(TRAFFIC_COUNT_HOURS)
        add_labeled_row(direct_grid, 1, "Traffic Count Hour =", self.direct_count_hour, ROW_HEIGHT)

        self.direct_design_speed = make_combo(DESIGN_SPEED_OPTIONS)
        self.direct_design_speed.setCurrentIndex(DESIGN_SPEED_OPTIONS.index("80 km/h"))
        add_labeled_row(direct_grid, 2, "Design Speed V =", self.direct_design_speed, ROW_HEIGHT)

        self.direct_geometry_design_year = make_combo(DESIGN_YEAR_OPTIONS)
        add_labeled_row(direct_grid, 3, "Design year for Geometry =", self.direct_geometry_design_year, ROW_HEIGHT)
        self.direct_geometry_design_year.currentTextChanged.connect(self._on_geometry_design_year_changed)

        self.direct_pavement_design_year = make_combo(DESIGN_YEAR_OPTIONS)
        add_labeled_row(direct_grid, 4, "Design year for Pavement =", self.direct_pavement_design_year, ROW_HEIGHT)
        self.direct_pavement_design_year.currentTextChanged.connect(self._on_pavement_design_year_changed)

        self.direct_los = make_combo(LOS_OPTIONS)
        add_labeled_row(direct_grid, 5, "Level of Service LOS =", self.direct_los, ROW_HEIGHT)

        self.direct_aadt = make_integer_line_edit(maximum=9_999_999)
        add_labeled_row(direct_grid, 6, "Average Annual Daily Traffic AADT =", self.direct_aadt, ROW_HEIGHT)
        self.direct_aadt.textChanged.connect(self._on_direct_aadt_pcu_changed)

        self.direct_pcu = make_decimal_line_edit(maximum=9_999_999.99, decimals=2)
        add_labeled_row(direct_grid, 7, "Passenger Car Unit PCU =", self.direct_pcu, ROW_HEIGHT)
        self.direct_pcu.textChanged.connect(self._on_direct_aadt_pcu_changed)

        scroll_layout.addWidget(direct_section)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

    def _toggle_quick_panel(self):
        mw = self.window()
        if hasattr(mw, "toggle_quick_panel"):
            self.sync_quick_panel_button(mw.toggle_quick_panel())

    def sync_quick_panel_button(self, visible: bool) -> None:
        self.quick_panel_btn.setText("Hide Quick Result" if visible else "Show Quick Result")

    def is_read_data_mode(self) -> bool:
        return self.input_mode_group.checkedId() == 0

    def is_direct_input_mode(self) -> bool:
        return self.input_mode_group.checkedId() == 1

    def active_geometry_design_year(self) -> str:
        if self.input_mode_group.checkedId() == 0:
            return self.read_geometry_design_year.currentText()
        return self.direct_geometry_design_year.currentText()

    def active_pavement_design_year(self) -> str:
        if self.input_mode_group.checkedId() == 0:
            return self.read_pavement_design_year.currentText()
        return self.direct_pavement_design_year.currentText()

    def active_growth_rate(self) -> float:
        if self.input_mode_group.checkedId() == 0:
            return self.read_r.value() / 100.0
        return self.direct_r.value() / 100.0

    @staticmethod
    def _parse_int_text(text: str) -> int:
        value = (text or "").strip().replace(",", "")
        if not value:
            return 0
        try:
            return max(0, int(value))
        except ValueError:
            return 0

    @staticmethod
    def _parse_float_text(text: str) -> float:
        value = (text or "").strip().replace(",", "")
        if not value:
            return 0.0
        try:
            return max(0.0, float(value))
        except ValueError:
            return 0.0

    def active_direct_aadt(self) -> int:
        return self._parse_int_text(self.direct_aadt.text())

    def active_direct_pcu(self) -> float:
        return self._parse_float_text(self.direct_pcu.text())

    def _on_input_mode_changed(self) -> None:
        mw = self.window()
        if hasattr(mw, "refresh_aadt_pcu"):
            mw.refresh_aadt_pcu()

    def _on_direct_aadt_pcu_changed(self, _text: str = "") -> None:
        if not self.is_direct_input_mode():
            return
        mw = self.window()
        if hasattr(mw, "refresh_aadt_pcu"):
            mw.refresh_aadt_pcu()

    def _on_growth_rate_changed(self, _value: float = 0.0) -> None:
        mw = self.window()
        if hasattr(mw, "refresh_lane_projection"):
            mw.refresh_lane_projection()
        if hasattr(mw, "refresh_aadt_pcu"):
            mw.refresh_aadt_pcu()

    def _on_geometry_design_year_changed(self, _text: str = "") -> None:
        mw = self.window()
        if hasattr(mw, "refresh_aadt_pcu"):
            mw.refresh_aadt_pcu()
        elif hasattr(mw, "refresh_road_classification"):
            mw.refresh_road_classification()

    def _on_pavement_design_year_changed(self, _text: str = "") -> None:
        mw = self.window()
        if hasattr(mw, "refresh_traffic_quick_results"):
            mw.refresh_traffic_quick_results()

    def _on_read_count_hour_changed(self, _text: str) -> None:
        mw = self.window()
        if hasattr(mw, "refresh_traffic_summary"):
            mw.refresh_traffic_summary(self.read_count_hour.currentText())

    def _on_read_excel(self):
        """Read sheets D1/D2 and store temporary traffic data for this session."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        path, _ = QFileDialog.getOpenFileName(
            self, "Read Excel", "", "Excel (*.xlsx *.xls);;All Files (*)"
        )
        if not path:
            return

        self.read_excel_path = path
        count_hour = self.read_count_hour.currentText()
        try:
            traffic_data = read_traffic_investigation_workbook(path, count_hour=count_hour)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Read Excel",
                f"Selected Excel file:\n{path}\n\nCould not read traffic count data:\n{exc}",
            )
            return

        traffic_rows = traffic_data.get("traffic_count_rows", [])
        summary_row = traffic_data.get("summary_total_row", [])
        if not traffic_rows and not summary_row:
            QMessageBox.information(
                self,
                "Read Excel",
                f"Selected Excel file:\n{path}\n\n"
                "No hourly traffic rows were found in sheets D1 and D2.",
            )
            return

        mw = self.window()
        if hasattr(mw, "set_traffic_excel_data"):
            mw.set_traffic_excel_data(traffic_data)
        elif hasattr(mw, "set_traffic_count_rows"):
            mw.set_traffic_count_rows(traffic_rows)

        sheet_lines = []
        for sheet_name in ("D1", "D2"):
            count = len(traffic_data.get("sheets", {}).get(sheet_name, []))
            if count:
                sheet_lines.append(f"{sheet_name}: {count} hourly row(s)")

        missing = traffic_data.get("missing_sheets") or []
        missing_text = ""
        if missing:
            missing_text = f"\n\nMissing sheet(s): {', '.join(missing)}"

        power = "1.2" if count_hour == "24h" else "1.0"

        QMessageBox.information(
            self,
            "Read Excel",
            (
                f"Selected Excel file:\n{path}\n\n"
                f"Temporary data loaded from sheets D1 and D2.\n"
                f"{chr(10).join(sheet_lines)}\n"
                f"Combined hourly rows: {len(traffic_rows)}\n"
                f"Daily total row (C69) D1 + D2 with {count_hour} power x{power} applied."
                f"{missing_text}\n\n"
                "Summary Traffic count data table and chart are updated.\n"
                "AADT & PCU and Number of Lane tabs are updated."
            ),
        )
