"""Subgrade Design > DCP page."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.chart import (
    MatplotlibChartWidget,
    draw_dcp_depth_vs_blows,
    draw_dcp_depth_vs_cbr,
)
from app.data.dcp_analysis import (
    DcpInputRow,
    analyze_dcp_rows,
    build_layered_cbr_summary,
    summarize_dcp_analysis,
)
from app.pages.Subgrade_Design.common import (
    BLOCK_SPACING,
    CHART_MIN_HEIGHT,
    apply_subgrade_row_heights,
    configure_subgrade_table,
    format_number,
    section_frame,
    subgrade_table_item,
)
from app.widgets.excel_paste_table import ExcelPasteTable
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content


class DcpPage(QWidget):
    """DCP input table + analysis table, charts, and layered CBR summary."""

    _INPUT_HEADERS = ["Number of Blow", "Total Penetration (mm)"]
    _ANALYSIS_HEADERS = [
        "Number of Blow",
        "Total Blow Number",
        "Total Penetration (mm)",
        "Change in Penetration (mm)",
        "Penetration Index (mm/blow)",
        "CBR (%)",
    ]
    _LAYERED_HEADERS = [
        "Depth (mm)",
        "Layer Thickness (mm)",
        "Total Blows",
        "Blows / 300 mm",
        "Layered-CBR (%)",
        "Remark",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        fit_scroll_content(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)

        layout.addWidget(self._build_input_block())
        layout.addWidget(self._build_analysis_block())
        layout.addStretch(0)

        # Defer first analysis/charts so the page can appear immediately.
        QTimer.singleShot(0, self._refresh_analysis)

    def quick_results(self) -> dict[str, str]:
        return summarize_dcp_analysis(analyze_dcp_rows(self.read_input_rows()))

    def read_input_rows(self) -> list[DcpInputRow]:
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

    def read_layered_cbr_summary(self):
        """Layered CBR Summary rows used by CBR Equivalent (Use DCP data)."""
        return build_layered_cbr_summary(analyze_dcp_rows(self.read_input_rows()))

    def _build_input_block(self) -> QFrame:
        frame, section_layout = section_frame("Input")

        hint = QLabel(
            "Excel-like: Ctrl+C copy · Ctrl+X cut · Ctrl+V paste from Excel · "
            "Delete clear cells · Shift+Delete remove row"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888888; font-size: 11px;")
        section_layout.addWidget(hint)

        self.input_table = ExcelPasteTable(
            self._INPUT_HEADERS,
            initial_rows=15,
            min_rows=1,
            use_add_row_footer=True,
            add_row_label="+ Add row",
            auto_fit_height=True,
            show_row_numbers=True,
        )
        configure_subgrade_table(self.input_table)
        # Keep Excel row numbers + no inner scroll (configure_subgrade_table hides them).
        self.input_table.verticalHeader().setVisible(True)
        self.input_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_table.data_changed.connect(self._on_input_changed)
        section_layout.addWidget(self.input_table)

        self._seed_sample_data()
        self.input_table.fit_height_to_rows()
        return frame

    def _on_input_changed(self) -> None:
        self.input_table.fit_height_to_rows()
        self._refresh_analysis()

    def _build_analysis_block(self) -> QFrame:
        frame, section_layout = section_frame("Analysis")

        self.analysis_table = QTableWidget(0, len(self._ANALYSIS_HEADERS))
        self.analysis_table.setHorizontalHeaderLabels(self._ANALYSIS_HEADERS)
        self.analysis_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.analysis_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.analysis_table.setAlternatingRowColors(True)
        self.analysis_table.setMinimumHeight(280)
        self.analysis_table.setMaximumHeight(360)
        configure_page_scroll(self.analysis_table)
        configure_subgrade_table(self.analysis_table)
        section_layout.addWidget(self.analysis_table)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        self.blows_chart = MatplotlibChartWidget(figsize=(4.8, 5.0))
        self.blows_chart.setMinimumHeight(CHART_MIN_HEIGHT)
        self.blows_chart.setMaximumHeight(CHART_MIN_HEIGHT + 40)
        charts_row.addWidget(self.blows_chart, 1)

        self.cbr_chart = MatplotlibChartWidget(figsize=(4.8, 5.0))
        self.cbr_chart.setMinimumHeight(CHART_MIN_HEIGHT)
        self.cbr_chart.setMaximumHeight(CHART_MIN_HEIGHT + 40)
        charts_row.addWidget(self.cbr_chart, 1)

        section_layout.addLayout(charts_row)

        layered_title = QLabel("Layered CBR Summary")
        layered_title.setStyleSheet("color: #cccccc; font-weight: 600; font-size: 14px;")
        section_layout.addWidget(layered_title)

        self.layered_table = QTableWidget(0, len(self._LAYERED_HEADERS))
        self.layered_table.setHorizontalHeaderLabels(self._LAYERED_HEADERS)
        self.layered_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.layered_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.layered_table.setAlternatingRowColors(True)
        self.layered_table.setMinimumHeight(220)
        self.layered_table.setMaximumHeight(320)
        configure_page_scroll(self.layered_table)
        configure_subgrade_table(self.layered_table)
        section_layout.addWidget(self.layered_table)

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
            self.input_table._ensure_data_rows(len(sample_rows))
            for row_index, (blows, depth) in enumerate(sample_rows):
                self.input_table.setItem(row_index, 0, subgrade_table_item(str(blows)))
                self.input_table.setItem(row_index, 1, subgrade_table_item(str(depth)))
            if self.input_table.use_add_row_footer:
                self.input_table._refresh_footer_row()
        finally:
            self.input_table.blockSignals(False)

    def _refresh_analysis(self) -> None:
        analysis_rows = analyze_dcp_rows(self.read_input_rows())

        self.analysis_table.setRowCount(len(analysis_rows))
        for row_index, row in enumerate(analysis_rows):
            values = [
                format_number(row.number_of_blow, decimals=0),
                format_number(row.total_blow_number, decimals=0),
                format_number(row.total_penetration_mm, decimals=0),
                format_number(row.change_penetration_mm, decimals=0),
                format_number(row.penetration_index_mm_per_blow),
                format_number(row.cbr_percent),
            ]
            for col_index, text in enumerate(values):
                self.analysis_table.setItem(row_index, col_index, subgrade_table_item(text))

        apply_subgrade_row_heights(self.analysis_table)
        self._refresh_charts(analysis_rows)
        self._refresh_layered_summary(analysis_rows)

    def _refresh_layered_summary(self, analysis_rows) -> None:
        summary_rows = build_layered_cbr_summary(analysis_rows)
        self.layered_table.setRowCount(len(summary_rows))

        for row_index, row in enumerate(summary_rows):
            values = [
                format_number(row.depth_mm, decimals=0),
                (
                    format_number(row.layer_thickness_mm, decimals=0)
                    if row.layer_thickness_mm is not None
                    else "—"
                ),
                format_number(row.total_blows, decimals=0),
                (
                    format_number(row.blows_per_300_mm, decimals=2)
                    if row.blows_per_300_mm is not None
                    else "—"
                ),
                (
                    format_number(row.layered_cbr_percent, decimals=2)
                    if row.layered_cbr_percent is not None
                    else "—"
                ),
                row.remark or "",
            ]
            for col_index, text in enumerate(values):
                self.layered_table.setItem(row_index, col_index, subgrade_table_item(text))

        apply_subgrade_row_heights(self.layered_table)

    def _refresh_charts(self, analysis_rows) -> None:
        for chart in (self.blows_chart, self.cbr_chart):
            if chart.figure is None:
                continue
            chart.figure.clear()

        if self.blows_chart.figure is not None and self.blows_chart.canvas is not None:
            ax_blows = self.blows_chart.add_subplot(111)
            draw_dcp_depth_vs_blows(ax_blows, analysis_rows)
            self.blows_chart.figure.tight_layout()
            self.blows_chart.redraw()

        if self.cbr_chart.figure is not None and self.cbr_chart.canvas is not None:
            ax_cbr = self.cbr_chart.add_subplot(111)
            draw_dcp_depth_vs_cbr(ax_cbr, analysis_rows)
            self.cbr_chart.figure.tight_layout()
            self.cbr_chart.redraw()
