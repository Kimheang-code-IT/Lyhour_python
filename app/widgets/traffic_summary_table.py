"""Traffic count summary table widget."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.ui_scale import UiScale
from app.core.ui_style import section_title_style
class TrafficCountSummaryTable(QWidget):
    """Excel-style summary table with merged header rows and one data row."""

    _COLUMN_WIDTHS = [78, 58, 66, 58, 72, 64, 68, 72, 84, 58, 58, 58, 68, 72, 76, 68, 72, 76, 76, 62]
    _TITLE_HEIGHT = 28
    _OUTER_MARGIN = 12
    _TITLE_SPACING = 8

    def __init__(self, rows: list[list] | None = None, summary_total_row: list | None = None, parent=None):
        super().__init__(parent)
        self._rows = rows or []
        self._summary_total_row = summary_total_row

        layout = QVBoxLayout(self)
        layout.setContentsMargins(self._OUTER_MARGIN, self._OUTER_MARGIN, self._OUTER_MARGIN, self._OUTER_MARGIN)
        layout.setSpacing(self._TITLE_SPACING)

        title = QLabel("Data per day")
        title.setFixedHeight(UiScale.px(self._TITLE_HEIGHT))
        title.setStyleSheet(section_title_style(16))
        layout.addWidget(title)
        self._title_label = title

        self.table = QTableWidget(3, 20)
        self._configure_table()
        self._populate_header()
        self._populate_body()
        self.table.setRowHeight(0, UiScale.px(26))
        self.table.setRowHeight(1, UiScale.px(26))
        self.table.setRowHeight(2, UiScale.px(30))
        layout.addWidget(self.table)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._sync_table_height()

    def apply_ui_scale(self) -> None:
        self._title_label.setFixedHeight(UiScale.px(self._TITLE_HEIGHT))
        self._title_label.setStyleSheet(section_title_style(16))
        header_row_height = UiScale.px(26)
        body_row_height = UiScale.px(30)
        self.table.setRowHeight(0, header_row_height)
        self.table.setRowHeight(1, header_row_height)
        self.table.setRowHeight(2, body_row_height)
        for row in range(self.table.rowCount()):
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item is None:
                    continue
                font = item.font()
                font.setPointSizeF(UiScale.pt(7))
                font.setBold(row < 2 or row == 2)
                item.setFont(font)
        self._sync_table_height()
        self._fit_table_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_table_layout()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_table_layout()

    def _configure_table(self) -> None:
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setShowGrid(True)
        self.table.setWordWrap(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustIgnored)
        self.table.verticalHeader().setMinimumSectionSize(1)
        self.table.horizontalHeader().setMinimumSectionSize(1)
        for row_index in range(self.table.rowCount()):
            self.table.verticalHeader().setSectionResizeMode(row_index, QHeaderView.ResizeMode.Fixed)
        for column_index in range(self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.ResizeMode.Fixed)

    def _sync_table_height(self) -> None:
        frame = self.table.frameWidth() * 2
        row_total = sum(self.table.rowHeight(row) for row in range(self.table.rowCount()))
        self.table.setFixedHeight(row_total + frame)
        outer_height = (
            self._OUTER_MARGIN * 2
            + UiScale.px(self._TITLE_HEIGHT)
            + self._TITLE_SPACING
            + self.table.height()
        )
        self.setFixedHeight(outer_height)

    def _fit_table_layout(self) -> None:
        viewport_width = self.table.viewport().width()
        if viewport_width <= 0:
            return

        min_width = 28
        if viewport_width < min_width * len(self._COLUMN_WIDTHS):
            equal_width = max(1, viewport_width // len(self._COLUMN_WIDTHS))
            scaled_widths = [equal_width] * len(self._COLUMN_WIDTHS)
            scaled_widths[-1] += viewport_width - sum(scaled_widths)
        else:
            total_base_width = sum(self._COLUMN_WIDTHS)
            scaled_widths = [
                max(min_width, int(width * viewport_width / total_base_width))
                for width in self._COLUMN_WIDTHS
            ]
            width_delta = viewport_width - sum(scaled_widths)
            scaled_widths[-1] += width_delta

        for column_index, width in enumerate(scaled_widths):
            self.table.setColumnWidth(column_index, width)

        header_row_height = UiScale.px(26)
        body_row_height = UiScale.px(30)
        self.table.setRowHeight(0, header_row_height)
        self.table.setRowHeight(1, header_row_height)
        self.table.setRowHeight(2, body_row_height)
        self._sync_table_height()
        self.table.verticalScrollBar().setValue(0)
        self.table.horizontalScrollBar().setValue(0)

    def _set_item(
        self,
        row: int,
        column: int,
        text: str,
        brush: QBrush,
        *,
        bold: bool = False,
    ) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setBackground(brush)
        font = item.font()
        font.setPointSizeF(UiScale.pt(7))
        font.setBold(bold)
        item.setFont(font)
        self.table.setItem(row, column, item)

    def _populate_header(self) -> None:
        header_brush = QBrush(QColor("#606060"))
        single_headers = {
            0: "Driver",
            1: "Motor",
            2: "Tricycles",
            3: "Koyon",
            4: "Passenger\nCar",
            5: "Pick-up",
            6: "Max 15\nSeats",
            7: "More than 15\nSeats",
            8: "More than 24\nSeats",
            19: "Total",
        }
        for column, text in single_headers.items():
            self._set_item(0, column, text, header_brush, bold=True)
            self.table.setSpan(0, column, 2, 1)

        axle_groups = [
            (9, "2 axles", 2),
            (11, "3 axles", 1),
            (12, "4 axles", 3),
            (15, "5 axles", 3),
            (18, "6 axles", 1),
        ]
        for column, text, span in axle_groups:
            self._set_item(0, column, text, header_brush, bold=True)
            if span > 1:
                self.table.setSpan(0, column, 1, span)

        axle_headers = [
            "4 tires", "6 tires", "6 tires",
            "No-trailer", "Full-trailer", "Semi-trailer", "No-trailer", "Full-trailer",
            "Semi-trailer", "Semi-trailer",
        ]
        for column, text in enumerate(axle_headers, start=9):
            self._set_item(1, column, text, header_brush, bold=True)

    def _populate_body(self) -> None:
        total_brush = QBrush(QColor("#888888"))
        if self._summary_total_row and len(self._summary_total_row) >= 20:
            totals = self._summary_total_row[:20]
        elif self._rows:
            totals = ["Total"] + [sum(int(row[column]) for row in self._rows) for column in range(1, 20)]
        else:
            totals = ["Total"] + ["-"] * 19
        for column, value in enumerate(totals):
            self._set_item(2, column, str(value), total_brush, bold=True)


def _chart_card(title: str, chart: QWidget, *, fixed_chart: bool = False) -> tuple[QFrame, QLabel]:
    card = result_card()
    if fixed_chart:
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    else:
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)
    title_label = QLabel(title)
    title_label.setStyleSheet(card_title_style(14))
    layout.addWidget(title_label)
    layout.addWidget(chart, 1)
    return card, title_label


def traffic_count_summary_table(
    rows: list[list] | None = None,
    summary_total_row: list | None = None,
) -> TrafficCountSummaryTable:
    return TrafficCountSummaryTable(rows, summary_total_row=summary_total_row)
