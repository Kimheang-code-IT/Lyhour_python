"""Subgrade Design (DCP / FWD / CBR Equivalent)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QShowEvent
from PyQt6.QtWidgets import (
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

from app.data.cbr_equivalent import (
    compute_cbr_equivalent,
    draw_cbr_equivalent_profile,
    summarize_cbr_equivalent,
)
from app.data.dcp_analysis import (
    DcpInputRow,
    analyze_dcp_rows,
    draw_dcp_depth_vs_blows,
    draw_dcp_depth_vs_cbr,
    summarize_dcp_analysis,
)
from app.layouts import BasePage, define_page
from app.core.ui_scale import UiScale
from app.core.ui_style import section_title_style, title_style
from app.widgets.button import secondary_button
from app.widgets.chart_ui import MatplotlibChartWidget
from app.widgets.excel_paste_table import ExcelPasteTable
from app.widgets.form_controls import make_double_spin
from app.widgets.labeled_input import add_labeled_row
from app.widgets.scroll_utils import configure_hidden_scrollbars


def _format_number(value: float | None, *, decimals: int = 2) -> str:
    if value is None:
        return "—"
    if decimals == 0:
        return f"{int(round(value))}"
    return f"{value:.{decimals}f}"


BLOCK_SPACING = 24
SECTION_TITLE_STYLE = section_title_style(18)
ROW_HEIGHT = 36
TABLE_FONT_SIZE = 10
TABLE_ROW_HEIGHT = 38
CHART_MIN_HEIGHT = 340

TAB_DCP = 0
TAB_CBR_EQUIVALENT = 1
TAB_FWD = 2


def _section_frame(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("subgradeSectionFrame")
    frame.setStyleSheet(
        "#subgradeSectionFrame { background-color: transparent; border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    section_layout = QVBoxLayout(frame)
    section_layout.setContentsMargins(16, 12, 16, 16)
    section_layout.setSpacing(12)

    title_label = QLabel(title)
    title_label.setStyleSheet(SECTION_TITLE_STYLE)
    section_layout.addWidget(title_label)
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return frame, section_layout


def _subgrade_table_font() -> QFont:
    font = QFont()
    font.setPointSizeF(UiScale.pt(TABLE_FONT_SIZE))
    return font


def _subgrade_table_item(text: str = "") -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFont(_subgrade_table_font())
    return item


def _style_subgrade_table_item(item: QTableWidgetItem) -> None:
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFont(_subgrade_table_font())


def _apply_subgrade_row_heights(table: QTableWidget) -> None:
    row_height = UiScale.px(TABLE_ROW_HEIGHT)
    table.verticalHeader().setDefaultSectionSize(row_height)
    for row_index in range(table.rowCount()):
        table.setRowHeight(row_index, row_height)


def _configure_subgrade_table(table: QTableWidget) -> None:
    """Hide row numbers, stretch columns, center data, and style table cells."""
    table.verticalHeader().setVisible(False)
    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    font_pt = UiScale.pt(TABLE_FONT_SIZE)
    table.setStyleSheet(
        f"""
        QTableWidget {{
            font-size: {font_pt}pt;
        }}
        QTableWidget::item {{
            font-size: {font_pt}pt;
            padding: 6px 4px;
        }}
        QHeaderView::section {{
            font-size: {font_pt}pt;
            padding: 8px 4px;
        }}
        """
    )
    _apply_subgrade_row_heights(table)

    footer_row = table.footer_row_index() if hasattr(table, "footer_row_index") else None
    data_rows = table.data_row_count() if hasattr(table, "data_row_count") else table.rowCount()

    for row_index in range(data_rows):
        for col_index in range(table.columnCount()):
            item = table.item(row_index, col_index)
            if item is None:
                table.setItem(row_index, col_index, _subgrade_table_item())
            else:
                _style_subgrade_table_item(item)

    if footer_row is not None and hasattr(table, "_refresh_footer_row"):
        table._refresh_footer_row()

    if table.editTriggers() != QTableWidget.EditTrigger.NoEditTriggers:
        def _on_item_changed(changed: QTableWidgetItem) -> None:
            if footer_row is not None and changed.row() == footer_row:
                return
            _style_subgrade_table_item(changed)

        table.itemChanged.connect(_on_item_changed)


def _expand_vertical(widget: QWidget) -> QWidget:
    """Let a widget grow with available page height."""
    policy = widget.sizePolicy()
    widget.setSizePolicy(policy.horizontalPolicy(), QSizePolicy.Policy.Expanding)
    return widget


class DcpTabPage(QWidget):
    """DCP tab: Input table + Analysis table and charts."""

    _INPUT_HEADERS = ["Number of Blow", "Total Penetration (mm)"]
    _ANALYSIS_HEADERS = [
        "Number of Blow",
        "Total Blow Number",
        "Total Penetration (mm)",
        "Change in Penetration (mm)",
        "Penetration Index (mm/blow)",
        "CBR (%)",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        _expand_vertical(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)

        layout.addWidget(self._build_input_block(), 2)
        layout.addWidget(self._build_analysis_block(), 3)

        self._refresh_analysis()

    def quick_results(self) -> dict[str, str]:
        return summarize_dcp_analysis(analyze_dcp_rows(self._read_input_rows()))

    def _section_frame(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        return _section_frame(title)

    def _build_input_block(self) -> QFrame:
        frame, section_layout = self._section_frame("Input")

        self.input_table = ExcelPasteTable(
            self._INPUT_HEADERS,
            initial_rows=16,
            min_rows=8,
            use_add_row_footer=True,
            add_row_label="+ Add row",
        )
        self.input_table.setMinimumHeight(240)
        configure_hidden_scrollbars(self.input_table)
        _configure_subgrade_table(self.input_table)
        self.input_table.data_changed.connect(self._refresh_analysis)
        section_layout.addWidget(_expand_vertical(self.input_table), 1)

        self._seed_sample_data()
        return frame

    def _build_analysis_block(self) -> QFrame:
        frame, section_layout = self._section_frame("Analysis")

        self.analysis_table = QTableWidget(0, len(self._ANALYSIS_HEADERS))
        self.analysis_table.setHorizontalHeaderLabels(self._ANALYSIS_HEADERS)
        self.analysis_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.analysis_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.analysis_table.setAlternatingRowColors(True)
        self.analysis_table.setMinimumHeight(280)
        configure_hidden_scrollbars(self.analysis_table)
        _configure_subgrade_table(self.analysis_table)
        section_layout.addWidget(_expand_vertical(self.analysis_table), 1)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        self.blows_chart = MatplotlibChartWidget(figsize=(4.8, 5.0))
        self.blows_chart.setMinimumHeight(CHART_MIN_HEIGHT)
        charts_row.addWidget(_expand_vertical(self.blows_chart), 1)

        self.cbr_chart = MatplotlibChartWidget(figsize=(4.8, 5.0))
        self.cbr_chart.setMinimumHeight(CHART_MIN_HEIGHT)
        charts_row.addWidget(_expand_vertical(self.cbr_chart), 1)

        section_layout.addLayout(charts_row, 2)
        return frame

    def _seed_sample_data(self) -> None:
        sample_rows = [
            (0, 0),
            (4, 60),
            (4, 130),
            (5, 150),
            (6, 200),
            (4, 250),
            (3, 280),
            (5, 330),
            (3, 380),
            (6, 420),
            (2, 470),
            (2, 510),
            (2, 600),
            (3, 700),
            (2, 800),
        ]
        self.input_table.blockSignals(True)
        try:
            limit = self.input_table.data_row_count()
            for row_index, (blows, depth) in enumerate(sample_rows):
                if row_index >= limit:
                    break
                self.input_table.setItem(row_index, 0, _subgrade_table_item(str(blows)))
                self.input_table.setItem(row_index, 1, _subgrade_table_item(str(depth)))
            if self.input_table.use_add_row_footer:
                self.input_table._refresh_footer_row()
        finally:
            self.input_table.blockSignals(False)

    def _read_input_rows(self) -> list[DcpInputRow]:
        rows: list[DcpInputRow] = []
        for values in self.input_table.read_numeric_rows():
            blow = values[0]
            depth = values[1]
            if blow is None and depth is None:
                continue
            rows.append(
                DcpInputRow(
                    number_of_blow=blow or 0.0,
                    total_penetration_mm=depth or 0.0,
                )
            )
        return rows

    def _refresh_analysis(self) -> None:
        analysis_rows = analyze_dcp_rows(self._read_input_rows())

        self.analysis_table.setRowCount(len(analysis_rows))
        for row_index, row in enumerate(analysis_rows):
            values = [
                _format_number(row.number_of_blow, decimals=0),
                _format_number(row.total_blow_number, decimals=0),
                _format_number(row.total_penetration_mm, decimals=0),
                _format_number(row.change_penetration_mm, decimals=0),
                _format_number(row.penetration_index_mm_per_blow),
                _format_number(row.cbr_percent),
            ]
            for col_index, text in enumerate(values):
                self.analysis_table.setItem(row_index, col_index, _subgrade_table_item(text))

        _apply_subgrade_row_heights(self.analysis_table)
        self._refresh_charts(analysis_rows)

    def _refresh_charts(self, analysis_rows) -> None:
        for chart in (self.blows_chart, self.cbr_chart):
            if chart.figure is None:
                continue
            chart.figure.clear()

        if self.blows_chart.figure is not None and self.blows_chart.canvas is not None:
            ax_blows = self.blows_chart.add_subplot(111)
            draw_dcp_depth_vs_blows(ax_blows, analysis_rows)
            self.blows_chart.figure.tight_layout()
            self.blows_chart.canvas.draw()

        if self.cbr_chart.figure is not None and self.cbr_chart.canvas is not None:
            ax_cbr = self.cbr_chart.add_subplot(111)
            draw_dcp_depth_vs_cbr(ax_cbr, analysis_rows)
            self.cbr_chart.figure.tight_layout()
            self.cbr_chart.canvas.draw()


class CbrEquivalentTabPage(QWidget):
    """CBR Equivalent tab derived from DCP layer CBR values."""

    _ANALYSIS_HEADERS = [
        "From Depth (mm)",
        "To Depth (mm)",
        "Thickness (mm)",
        "CBR (%)",
        "Weighted Contribution",
    ]

    def __init__(self, dcp_page: DcpTabPage, parent=None):
        super().__init__(parent)
        _expand_vertical(self)
        self._dcp_page = dcp_page

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)

        layout.addWidget(self._build_input_block())
        layout.addWidget(self._build_analysis_block(), 1)

        self._refresh_analysis()

    def quick_results(self) -> dict[str, str]:
        return summarize_cbr_equivalent(self._current_result())

    def refresh_analysis(self) -> None:
        self._refresh_analysis()

    def _current_result(self):
        rows = analyze_dcp_rows(self._dcp_page._read_input_rows())
        return compute_cbr_equivalent(
            rows,
            design_depth_mm=float(self.design_depth_spin.value()),
        )

    def _build_input_block(self) -> QFrame:
        frame, section_layout = _section_frame("Input")

        fields_host = QWidget()
        form_grid = QGridLayout(fields_host)
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(14)
        form_grid.setContentsMargins(0, 0, 0, 0)

        self.design_depth_spin = make_double_spin()
        self.design_depth_spin.setRange(50.0, 2_000.0)
        self.design_depth_spin.setDecimals(0)
        self.design_depth_spin.setSuffix(" mm")
        self.design_depth_spin.setValue(300.0)
        self.design_depth_spin.setToolTip("Top subgrade depth used for CBR Equivalent")
        self.design_depth_spin.valueChanged.connect(self._refresh_analysis)
        add_labeled_row(form_grid, 0, "Design influence depth =", self.design_depth_spin, ROW_HEIGHT)
        form_grid.setColumnStretch(1, 1)

        section_layout.addWidget(fields_host)
        return frame

    def _build_analysis_block(self) -> QFrame:
        frame, section_layout = _section_frame("Analysis")

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #cccccc; font-size: 13px; padding: 4px 0;")
        section_layout.addWidget(self.summary_label)

        self.analysis_table = QTableWidget(0, len(self._ANALYSIS_HEADERS))
        self.analysis_table.setHorizontalHeaderLabels(self._ANALYSIS_HEADERS)
        self.analysis_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.analysis_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.analysis_table.setAlternatingRowColors(True)
        self.analysis_table.setMinimumHeight(280)
        configure_hidden_scrollbars(self.analysis_table)
        _configure_subgrade_table(self.analysis_table)
        section_layout.addWidget(_expand_vertical(self.analysis_table), 1)

        self.profile_chart = MatplotlibChartWidget(figsize=(7.0, 5.0))
        self.profile_chart.setMinimumHeight(CHART_MIN_HEIGHT)
        section_layout.addWidget(_expand_vertical(self.profile_chart), 2)
        return frame

    def _refresh_analysis(self) -> None:
        result = self._current_result()

        if result is None or not result.layers:
            self.summary_label.setText("Enter DCP data on the DCP tab to calculate CBR Equivalent.")
            self.analysis_table.setRowCount(0)
            if self.profile_chart.figure is not None:
                self.profile_chart.clear()
            return

        if result.cbr_equivalent_percent is None:
            self.summary_label.setText("No CBR layers available within the design influence depth.")
        else:
            self.summary_label.setText(
                "CBR Equivalent = {:.2f} %   |   Minimum CBR = {:.2f} %   |   "
                "Design depth = {:.0f} mm   |   Layers = {}".format(
                    result.cbr_equivalent_percent,
                    result.minimum_cbr_percent or 0.0,
                    result.design_depth_mm,
                    len(result.layers),
                )
            )

        self.analysis_table.setRowCount(len(result.layers))
        for row_index, layer in enumerate(result.layers):
            values = [
                _format_number(layer.from_depth_mm, decimals=0),
                _format_number(layer.to_depth_mm, decimals=0),
                _format_number(layer.thickness_mm, decimals=0),
                _format_number(layer.cbr_percent),
                _format_number(layer.weighted_contribution),
            ]
            for col_index, text in enumerate(values):
                self.analysis_table.setItem(row_index, col_index, _subgrade_table_item(text))

        _apply_subgrade_row_heights(self.analysis_table)

        if self.profile_chart.figure is None:
            return

        self.profile_chart.figure.clear()
        ax = self.profile_chart.add_subplot(111)
        draw_cbr_equivalent_profile(ax, result)
        self.profile_chart.figure.tight_layout()
        self.profile_chart.canvas.draw()


class FwdTabPage(QWidget):
    """FWD tab placeholder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        frame, section_layout = _section_frame("FWD")
        message = QLabel("FWD analysis will be added here.")
        message.setStyleSheet("color: #888888; font-size: 14px; padding: 24px;")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        section_layout.addWidget(message)
        layout.addWidget(frame)


@define_page("blank", title="Subgrade Design")
class RGDSubgradeDesignPage(BasePage):
    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._page_title = QLabel("Subgrade Design")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        content.addLayout(title_row)

        self.segmented = SegmentedWidget(self)
        self.segmented.setObjectName("subgradeDesignSegmented")
        self.stack = QStackedWidget(self)
        _expand_vertical(self.stack)

        self.dcp_page = DcpTabPage()
        self.cbr_equivalent_page = CbrEquivalentTabPage(self.dcp_page)
        self.fwd_page = FwdTabPage()

        tabs = [
            ("dcp", "DCP", self.dcp_page),
            ("cbr_equivalent", "CBR Equivalent", self.cbr_equivalent_page),
            ("fwd", "FWD", self.fwd_page),
        ]

        for index, (route_key, text, page) in enumerate(tabs):
            self.segmented.addItem(
                route_key,
                text,
                onClick=lambda _=None, tab_index=index: self._set_tab(tab_index),
            )
            self.stack.addWidget(page)

        self.segmented.setCurrentItem("dcp")
        self.stack.setCurrentIndex(0)

        content.addWidget(self.segmented)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidget(self.stack)
        content.addWidget(self.scroll_area, 1)
        _expand_vertical(self)

        self.dcp_page.input_table.data_changed.connect(self._on_dcp_data_changed)
        self.cbr_equivalent_page.design_depth_spin.valueChanged.connect(self._push_quick_results)
        self._push_quick_results()

    def _on_dcp_data_changed(self) -> None:
        self.cbr_equivalent_page.refresh_analysis()
        self._push_quick_results()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def activate_page(self) -> None:
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def _set_tab(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self._setup_quick_panel()

    def _results(self) -> dict[str, str]:
        index = self.stack.currentIndex()
        if index == TAB_DCP:
            return self.dcp_page.quick_results()
        if index == TAB_CBR_EQUIVALENT:
            return self.cbr_equivalent_page.quick_results()
        return {}

    def _setup_quick_panel(self) -> None:
        mw = self.window()
        if not hasattr(mw, "quick_panel"):
            return
        index = self.stack.currentIndex()
        if index == TAB_CBR_EQUIVALENT and hasattr(mw.quick_panel, "set_subgrade_cbr_equivalent_schema"):
            mw.quick_panel.set_subgrade_cbr_equivalent_schema()
        elif hasattr(mw.quick_panel, "set_subgrade_schema"):
            mw.quick_panel.set_subgrade_schema()
        mw.quick_panel.set_results(self._results())

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
