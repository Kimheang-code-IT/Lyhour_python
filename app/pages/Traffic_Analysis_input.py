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
    QButtonGroup,
    QRadioButton,
)

from app.widgets.form_controls import (
    make_combo,
    make_decimal_line_edit,
    make_double_spin,
    make_integer_line_edit,
    make_radio,
)
from app.core.theme import card_stylesheet, theme_tokens
from app.core.ui_scale import UiScale
from app.core.ui_style import section_title_style, title_style
from app.core.i18n import tr
from app.services.excel_io import ExcelIOService
from app.data.area_type import AREA_TYPE_OPTIONS, DEFAULT_AREA_TYPE
from app.widgets.labeled_input import add_labeled_row
from app.widgets.button import secondary_button
from app.widgets.scroll_utils import configure_hidden_scrollbars
from app.widgets.traffic_results import refresh_theme_widgets

try:
    from qfluentwidgets import SubtitleLabel
    _HAS_FLUENT = True
except Exception:
    SubtitleLabel = None  # type: ignore[assignment]
    _HAS_FLUENT = False

# Options for dropdowns
TRAFFIC_COUNT_HOURS = ["12h", "24h"]
AREA_TYPE_COMBO_OPTIONS = list(AREA_TYPE_OPTIONS)
DESIGN_YEAR_OPTIONS = [f"{v} year" for v in (5, 10, 15, 20, 25, 30, 35, 40)]
from app.data.level_of_service import LOS_OPTIONS

ROW_HEIGHT = 36


def section_with_radio(
    title: str, parent: QWidget, header_widget: QWidget | None = None
) -> tuple[QWidget, QRadioButton, QFrame, QGridLayout, QWidget]:
    """Return (section_widget, radio, frame, grid). Radio is outside frame for show/hide logic."""
    section_widget = QWidget(parent)
    section_layout = QVBoxLayout(section_widget)
    section_layout.setContentsMargins(0, 0, 0, 0)
    section_layout.setSpacing(4)

    # Title row with radio, title, (optional) button
    title_row = QHBoxLayout()
    radio = make_radio(checked=True)
    if _HAS_FLUENT and SubtitleLabel is not None:
        title_lbl = SubtitleLabel(title)
    else:
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(section_title_style(16))
    title_row.addWidget(radio)
    title_row.addWidget(title_lbl)
    title_row.addStretch()
    if header_widget is not None:
        title_row.addWidget(header_widget)
    section_layout.addLayout(title_row)

    # The input card frame
    frame = QFrame(section_widget)
    frame.setObjectName("trafficSectionFrame")
    frame.setStyleSheet(card_stylesheet(theme_tokens()))
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
    return section_widget, radio, frame, grid, title_lbl


class TrafficAnalysisInputPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        def _expand_width(widget: QWidget) -> QWidget:
            """Make form control fill the available grid column width."""
            policy = widget.sizePolicy()
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, policy.verticalPolicy())
            return widget

        if _HAS_FLUENT and SubtitleLabel is not None:
            page_title = SubtitleLabel("Traffic Analysis Input")
        else:
            page_title = QLabel("Traffic Analysis Input")
            page_title.setStyleSheet(title_style(22))
        self._page_title = page_title
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
        configure_hidden_scrollbars(scroll)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 8, 0, 0)
        scroll_layout.setSpacing(20)

        # Section with radio logic for Read Data
        read_section, read_radio, read_frame, read_grid, read_title = section_with_radio(
            "Read Data", scroll_content
        )

        self.read_r = make_double_spin()
        self.read_r.setRange(0, 100)
        self.read_r.setDecimals(2)
        self.read_r.setSuffix(" %")
        self.read_r.setValue(3.0)
        _expand_width(self.read_r)
        add_labeled_row(read_grid, 0, "Traffic Growth Rate R =", self.read_r, ROW_HEIGHT)
        self.read_r.valueChanged.connect(self._on_growth_rate_changed)

        self.read_count_hour = make_combo(TRAFFIC_COUNT_HOURS)
        _expand_width(self.read_count_hour)
        add_labeled_row(read_grid, 1, "Traffic Count Hour =", self.read_count_hour, ROW_HEIGHT)
        self.read_count_hour.currentTextChanged.connect(self._on_count_hour_changed)

        self.read_area_type = make_combo(AREA_TYPE_COMBO_OPTIONS)
        self.read_area_type.setCurrentText(DEFAULT_AREA_TYPE)
        _expand_width(self.read_area_type)
        add_labeled_row(read_grid, 2, "Area Type =", self.read_area_type, ROW_HEIGHT)
        self.read_area_type.currentTextChanged.connect(self._on_area_type_changed)

        self.read_geometry_design_year = make_combo(DESIGN_YEAR_OPTIONS)
        _expand_width(self.read_geometry_design_year)
        add_labeled_row(read_grid, 3, "Design year for Geometry =", self.read_geometry_design_year, ROW_HEIGHT)
        self.read_geometry_design_year.currentTextChanged.connect(self._on_geometry_design_year_changed)

        self.read_pavement_design_year = make_combo(DESIGN_YEAR_OPTIONS)
        _expand_width(self.read_pavement_design_year)
        add_labeled_row(read_grid, 4, "Design year for Pavement =", self.read_pavement_design_year, ROW_HEIGHT)
        self.read_pavement_design_year.currentTextChanged.connect(self._on_pavement_design_year_changed)

        self.read_los = make_combo(LOS_OPTIONS)
        _expand_width(self.read_los)
        add_labeled_row(read_grid, 5, "Level of Service LOS =", self.read_los, ROW_HEIGHT)

        scroll_layout.addWidget(read_section)

        # ---------- Direct Input ----------

        # Section with radio logic for Direct Input
        direct_section, direct_radio, direct_frame, direct_grid, direct_title = section_with_radio(
            "Direct Input", scroll_content
        )

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
        _expand_width(self.direct_r)
        add_labeled_row(direct_grid, 0, "Traffic Growth Rate R =", self.direct_r, ROW_HEIGHT)
        self.direct_r.valueChanged.connect(self._on_growth_rate_changed)

        self.direct_count_hour = make_combo(TRAFFIC_COUNT_HOURS)
        _expand_width(self.direct_count_hour)
        add_labeled_row(direct_grid, 1, "Traffic Count Hour =", self.direct_count_hour, ROW_HEIGHT)
        self.direct_count_hour.currentTextChanged.connect(self._on_count_hour_changed)

        self.direct_area_type = make_combo(AREA_TYPE_COMBO_OPTIONS)
        self.direct_area_type.setCurrentText(DEFAULT_AREA_TYPE)
        _expand_width(self.direct_area_type)
        add_labeled_row(direct_grid, 2, "Area Type =", self.direct_area_type, ROW_HEIGHT)
        self.direct_area_type.currentTextChanged.connect(self._on_area_type_changed)

        self.direct_geometry_design_year = make_combo(DESIGN_YEAR_OPTIONS)
        _expand_width(self.direct_geometry_design_year)
        add_labeled_row(direct_grid, 3, "Design year for Geometry =", self.direct_geometry_design_year, ROW_HEIGHT)
        self.direct_geometry_design_year.currentTextChanged.connect(self._on_geometry_design_year_changed)

        self.direct_pavement_design_year = make_combo(DESIGN_YEAR_OPTIONS)
        _expand_width(self.direct_pavement_design_year)
        add_labeled_row(direct_grid, 4, "Design year for Pavement =", self.direct_pavement_design_year, ROW_HEIGHT)
        self.direct_pavement_design_year.currentTextChanged.connect(self._on_pavement_design_year_changed)

        self.direct_los = make_combo(LOS_OPTIONS)
        _expand_width(self.direct_los)
        add_labeled_row(direct_grid, 5, "Level of Service LOS =", self.direct_los, ROW_HEIGHT)

        self.read_los.currentTextChanged.connect(self._on_los_changed)
        self.direct_los.currentTextChanged.connect(self._on_los_changed)

        self.direct_aadt = make_integer_line_edit(maximum=9_999_999)
        _expand_width(self.direct_aadt)
        add_labeled_row(direct_grid, 6, "Average Annual Daily Traffic AADT =", self.direct_aadt, ROW_HEIGHT)
        self.direct_aadt.textChanged.connect(self._on_direct_aadt_pcu_changed)

        self.direct_pcu = make_decimal_line_edit(maximum=9_999_999.99, decimals=2)
        _expand_width(self.direct_pcu)
        add_labeled_row(direct_grid, 7, "Passenger Car Unit PCU =", self.direct_pcu, ROW_HEIGHT)
        self.direct_pcu.textChanged.connect(self._on_direct_aadt_pcu_changed)

        scroll_layout.addWidget(direct_section)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        self._section_titles = [
            title for title in (read_title, direct_title) if isinstance(title, QLabel)
        ]
        self.refresh_ui_scale()

    def refresh_ui_scale(self) -> None:
        if isinstance(self._page_title, QLabel):
            self._page_title.setStyleSheet(title_style(22))
        for title_label in self._section_titles:
            title_label.setStyleSheet(section_title_style(16))
        row_height = UiScale.px(ROW_HEIGHT)
        for widget in (
            self.read_r,
            self.read_count_hour,
            self.read_area_type,
            self.read_geometry_design_year,
            self.read_pavement_design_year,
            self.read_los,
            self.direct_r,
            self.direct_count_hour,
            self.direct_area_type,
            self.direct_geometry_design_year,
            self.direct_pavement_design_year,
            self.direct_los,
            self.direct_aadt,
            self.direct_pcu,
        ):
            widget.setMinimumHeight(row_height)
            widget.setMaximumHeight(row_height)

    def refresh_theme(self) -> None:
        refresh_theme_widgets(self)
        self.refresh_ui_scale()

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

    def active_area_type(self) -> str:
        if self.input_mode_group.checkedId() == 0:
            return self.read_area_type.currentText()
        return self.direct_area_type.currentText()

    def active_growth_rate(self) -> float:
        if self.input_mode_group.checkedId() == 0:
            return self.read_r.value() / 100.0
        return self.direct_r.value() / 100.0

    def active_los(self) -> str:
        if self.is_read_data_mode():
            return self.read_los.currentText()
        return self.direct_los.currentText()

    def set_active_los(self, los: str) -> None:
        if los not in LOS_OPTIONS:
            return
        combo = self.read_los if self.is_read_data_mode() else self.direct_los
        combo.blockSignals(True)
        combo.setCurrentText(los)
        combo.blockSignals(False)

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

    def active_traffic_count_hour(self) -> str:
        if self.is_read_data_mode():
            return self.read_count_hour.currentText()
        return self.direct_count_hour.currentText()

    def _on_input_mode_changed(self) -> None:
        mw = self.window()
        if hasattr(mw, "refresh_aadt_pcu"):
            mw.refresh_aadt_pcu()
        if hasattr(mw, "refresh_traffic_summary"):
            mw.refresh_traffic_summary(self.active_traffic_count_hour())

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

    def _on_los_changed(self, _text: str = "") -> None:
        mw = self.window()
        if hasattr(mw, "refresh_lane_los_context"):
            mw.refresh_lane_los_context()

    def _on_geometry_design_year_changed(self, _text: str = "") -> None:
        mw = self.window()
        if hasattr(mw, "refresh_aadt_pcu"):
            mw.refresh_aadt_pcu()
        elif hasattr(mw, "refresh_road_classification"):
            mw.refresh_road_classification()
        if hasattr(mw, "refresh_esal"):
            mw.refresh_esal()

    def _on_pavement_design_year_changed(self, _text: str = "") -> None:
        mw = self.window()
        if hasattr(mw, "refresh_esal"):
            mw.refresh_esal()
        if hasattr(mw, "refresh_traffic_quick_results"):
            mw.refresh_traffic_quick_results()

    def _on_area_type_changed(self, _text: str = "") -> None:
        mw = self.window()
        if hasattr(mw, "refresh_aadt_pcu"):
            mw.refresh_aadt_pcu()

    def _on_count_hour_changed(self, _text: str) -> None:
        mw = self.window()
        if hasattr(mw, "refresh_traffic_summary"):
            mw.refresh_traffic_summary(self.active_traffic_count_hour())

    def _on_read_excel(self):
        """Import Excel via main window (temporary cache, no data preview)."""
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("menu.file.import_excel"),
            "",
            ExcelIOService.excel_filter(),
        )
        if not path:
            return
        mw = self.window()
        count_hour = self.active_traffic_count_hour()
        if hasattr(mw, "import_excel_file"):
            mw.import_excel_file(path, count_hour=count_hour)
            self.read_excel_path = path
