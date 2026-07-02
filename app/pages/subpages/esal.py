"""ESAL subpage."""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.ui_scale import UiScale
from app.core.ui_style import card_title_style, section_title_style
from app.pages.subpages.common import (
    BarChart,
    configure_result_description_note_layout,
    result_card,
    result_description_label,
    result_description_note,
    wrap_result_description_lines,
)
from app.services.traffic_esal import (
    EsalResult,
    build_design_period_description_html,
    chart_bars_from_esal,
)

_ESAL_IMAGE_FILES = {
    "steering_wheel": "Single Axle Steering wheel.png",
    "single_tire": "Single Axle Sing Tire.png",
    "tandem_single_tire": "Tamdem Axle signle tire.png",
    "dual_tire": "Single Axle Dual Tire.png",
    "tandem_dual_tire": "Tandem Axle Dual tire.png",
    "tridem_dual_tire": "Tridem Axle Dual Tire.png",
}

_HEADER_ROW_HEIGHT = 34
_BODY_ROW_WEIGHTS = (1.0, 1.0, 1.15, 1.35)
_COLUMN_WEIGHTS = (3.0, 3.5, 1.2, 3.0, 3.5, 1.2)

_EMPTY_DESCRIPTION_LINES = (
    "- Design period in 15 year is ____",
    "- Design period in 20 year is ____",
    "- Design period in 25 year is ____",
)


def _empty_description(*, panel_width: int | None = None) -> str:
    return wrap_result_description_lines(list(_EMPTY_DESCRIPTION_LINES), panel_width=panel_width)


def _image_assets_dir() -> Path:
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / "app" / "assets" / "image"
    return Path(__file__).resolve().parent.parent.parent / "assets" / "image"


def _format_number(value: int) -> str:
    return f"{value:,}" if value else "-"


class RemarqueImageLabel(QLabel):
    """Scales an axle diagram to fill the Remarque table cell."""

    def __init__(self, filename: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._source = QPixmap()
        path = _image_assets_dir() / filename
        if path.is_file():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self._source = pixmap
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #ffffff; border: none;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(1, 1)
        self._refresh_pixmap()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self) -> None:
        if self._source.isNull():
            self.clear()
            return
        available = self.size().expandedTo(self.minimumSize())
        margin = 6
        target_w = max(1, available.width() - margin * 2)
        target_h = max(1, available.height() - margin * 2)
        self.setPixmap(
            self._source.scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class DescriptionCell(QLabel):
    """Wrapped description text for ESAL table cells."""

    def __init__(self, text: str, *, background: str = "#ffffff", parent: QWidget | None = None):
        super().__init__(text, parent)
        self._background = background
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.apply_ui_scale(table_width=0)

    def apply_ui_scale(self, *, table_width: int) -> None:
        padding = UiScale.px_local(8, table_width, reference=900)
        font_pt = UiScale.pt_local(10, table_width, reference=900)
        self.setStyleSheet(
            f"background-color: {self._background}; color: #111111; "
            f"padding: {padding}px; font-size: {font_pt}pt;"
        )


class EsalAxleTable(QTableWidget):
    """ESAL axle summary table that expands to fill available space."""

    _NUMBER_CELLS: tuple[tuple[int, int, str], ...] = (
        (1, 2, "steering_sast"),
        (2, 5, "sadt"),
        (3, 2, "tast"),
        (3, 5, "tadt"),
        (4, 5, "trdt"),
    )

    def __init__(self, parent: QWidget | None = None):
        super().__init__(5, 6, parent)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustIgnored)
        self.verticalHeader().setMinimumSectionSize(1)
        self.horizontalHeader().setMinimumSectionSize(1)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: #d8d8dc;
                color: #111111;
                border: 1px solid #606060;
                gridline-color: #606060;
            }}
            QTableWidget::item {{
                padding: {UiScale.px(6)}px;
            }}
        """)
        self._populate()
        self._configure_resize_modes()

    def apply_ui_scale(self) -> None:
        table_width = max(self.viewport().width(), self.width(), 1)
        padding = UiScale.px_local(6, table_width, reference=900)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: #d8d8dc;
                color: #111111;
                border: 1px solid #606060;
                gridline-color: #606060;
            }}
            QTableWidget::item {{
                padding: {padding}px;
            }}
        """)

        header_pt = UiScale.pt_local(10, table_width, reference=900)
        number_pt = UiScale.pt_local(11, table_width, reference=900)
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item is None:
                    continue
                font = item.font()
                if row == 0:
                    font.setPointSizeF(header_pt)
                    font.setBold(True)
                elif column in (2, 5):
                    font.setPointSizeF(number_pt)
                    font.setBold(True)
                item.setFont(font)

        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                widget = self.cellWidget(row, column)
                if isinstance(widget, DescriptionCell):
                    widget.apply_ui_scale(table_width=table_width)

        self._fit_table_layout()

    def _configure_resize_modes(self) -> None:
        vertical_header = self.verticalHeader()
        horizontal_header = self.horizontalHeader()
        for row_index in range(self.rowCount()):
            vertical_header.setSectionResizeMode(row_index, QHeaderView.ResizeMode.Fixed)
        for column_index in range(self.columnCount()):
            horizontal_header.setSectionResizeMode(column_index, QHeaderView.ResizeMode.Fixed)

    def _populate(self) -> None:
        header_brush = QBrush(QColor("#f2f2f2"))
        body_brush = QBrush(QColor("#ffffff"))
        empty_brush = QBrush(QColor("#d8d8dc"))

        def set_header(row: int, column: int, text: str) -> None:
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(header_brush)
            font = item.font()
            font.setPointSizeF(UiScale.pt(10))
            font.setBold(True)
            item.setFont(font)
            self.setItem(row, column, item)

        def set_number(row: int, column: int, text: str = "-") -> None:
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(body_brush)
            font = item.font()
            font.setPointSizeF(UiScale.pt(11))
            font.setBold(True)
            item.setFont(font)
            self.setItem(row, column, item)

        def set_description(row: int, column: int, text: str) -> None:
            self.setCellWidget(row, column, DescriptionCell(text))

        def set_remarque(row: int, column: int, image_key: str) -> None:
            filename = _ESAL_IMAGE_FILES[image_key]
            self.setCellWidget(row, column, RemarqueImageLabel(filename))

        def set_empty(row: int, column: int) -> None:
            item = QTableWidgetItem("")
            item.setBackground(empty_brush)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(row, column, item)

        for offset in (0, 3):
            set_header(0, offset, "Descriptions")
            set_header(0, offset + 1, "Remarque")
            set_header(0, offset + 2, "Number")

        set_description(1, 0, "Single Axle Steering Wheel")
        set_remarque(1, 1, "steering_wheel")
        set_number(1, 2)
        self.setSpan(1, 2, 2, 1)

        set_description(2, 0, "Single Axle Single Tire (SAST)")
        set_remarque(2, 1, "single_tire")

        for column in range(3, 6):
            set_empty(1, column)

        set_description(2, 3, "Single Axle Dual Tire (SADT)")
        set_remarque(2, 4, "dual_tire")
        set_number(2, 5)

        set_description(3, 0, "Tandem Axle Single Tire (TAST)")
        set_remarque(3, 1, "tandem_single_tire")
        set_number(3, 2)

        set_description(3, 3, "Tandem Axle Dual Tire (TADT)")
        set_remarque(3, 4, "tandem_dual_tire")
        set_number(3, 5)

        for column in range(3):
            set_empty(4, column)

        set_description(4, 3, "Tridem Axle Dual Tire (TRDT)")
        set_remarque(4, 4, "tridem_dual_tire")
        set_number(4, 5)

    def update_numbers(self, axle_numbers: dict[str, int] | None) -> None:
        numbers = axle_numbers or {}
        for row, column, key in self._NUMBER_CELLS:
            item = self.item(row, column)
            if item is None:
                continue
            item.setText(_format_number(numbers.get(key, 0)))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_table_layout()
        self.apply_ui_scale()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._fit_table_layout()

    def _fit_table_layout(self) -> None:
        viewport_height = self.viewport().height()
        viewport_width = self.viewport().width()
        if viewport_height <= 0 or viewport_width <= 0:
            return

        header_height = min(UiScale.px(_HEADER_ROW_HEIGHT), max(UiScale.px(20), viewport_height // 8))
        self.setRowHeight(0, header_height)

        body_height = max(1, viewport_height - header_height)
        weight_total = sum(_BODY_ROW_WEIGHTS)
        assigned_height = 0
        for row_index, weight in enumerate(_BODY_ROW_WEIGHTS, start=1):
            if row_index == self.rowCount() - 1:
                row_height = max(1, body_height - assigned_height)
            else:
                row_height = max(1, int(body_height * weight / weight_total))
                assigned_height += row_height
            self.setRowHeight(row_index, row_height)

        column_widths = self._column_widths_for_viewport(viewport_width)
        for column_index, width in enumerate(column_widths):
            self.setColumnWidth(column_index, width)

        row_delta = viewport_height - sum(self.rowHeight(row) for row in range(self.rowCount()))
        if row_delta:
            last_row = self.rowCount() - 1
            self.setRowHeight(last_row, max(1, self.rowHeight(last_row) + row_delta))

        column_delta = viewport_width - sum(self.columnWidth(column) for column in range(self.columnCount()))
        if column_delta:
            last_column = self.columnCount() - 1
            self.setColumnWidth(last_column, max(1, self.columnWidth(last_column) + column_delta))

        self.verticalScrollBar().setValue(0)
        self.horizontalScrollBar().setValue(0)

    @staticmethod
    def _column_widths_for_viewport(viewport_width: int) -> list[int]:
        weight_total = sum(_COLUMN_WEIGHTS)
        widths = [max(1, int(viewport_width * weight / weight_total)) for weight in _COLUMN_WEIGHTS]
        width_delta = viewport_width - sum(widths)
        widths[-1] += width_delta
        return widths


class EsalPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: EsalResult | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        table_card = result_card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(8)

        self._table_title = QLabel("ESAL Axle Type Summary")
        table_layout.addWidget(self._table_title)

        self._axle_table = EsalAxleTable()
        self._axle_table.setMinimumHeight(UiScale.px(180))
        table_layout.addWidget(self._axle_table, 1)
        layout.addWidget(table_card, 3)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(16)

        chart_card = result_card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)

        self._chart_title = QLabel("ESAL by Design Period")
        chart_layout.addWidget(self._chart_title)

        self._chart_slot = QVBoxLayout()
        self._chart_slot.setContentsMargins(0, 0, 0, 0)
        self._chart = BarChart([], y_step=100_000, show_values=True)
        self._chart_slot.addWidget(self._chart, 1)
        chart_layout.addLayout(self._chart_slot, 1)
        bottom_row.addWidget(chart_card, 2)

        description_card = result_card()
        description_layout = QVBoxLayout(description_card)
        description_layout.setContentsMargins(12, 12, 12, 12)
        description_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._description_title = QLabel("Design Period Description")
        description_layout.addWidget(self._description_title, 0, Qt.AlignmentFlag.AlignTop)

        note = result_description_note(dark_background=False)
        note_layout = QVBoxLayout(note)
        note_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._description = result_description_label()
        configure_result_description_note_layout(note_layout, self._description)
        description_layout.addWidget(note, 1, Qt.AlignmentFlag.AlignTop)
        bottom_row.addWidget(description_card, 1)
        layout.addLayout(bottom_row, 2)
        self.refresh_ui_scale()

    def _description_panel_width(self) -> int:
        width = self._description.width()
        if width > 0:
            return width
        note = self._description.parentWidget()
        if note is not None and note.width() > 0:
            return note.width()
        return UiScale.width() // 3

    def refresh_ui_scale(self) -> None:
        self._table_title.setStyleSheet(section_title_style(18))
        self._chart_title.setStyleSheet(card_title_style(14))
        self._description_title.setStyleSheet(card_title_style(14))
        self._axle_table.setMinimumHeight(UiScale.px(180))
        self._axle_table.apply_ui_scale()
        self._refresh()

    def set_esal_result(self, result: EsalResult | None) -> None:
        self._result = result
        self._refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._axle_table._fit_table_layout()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._axle_table._fit_table_layout()
        self._axle_table.apply_ui_scale()
        panel_width = self._description_panel_width()
        if self._result is not None and self._result.has_data:
            description = build_design_period_description_html(
                self._result.design_periods,
                panel_width=panel_width,
            )
        else:
            description = _empty_description(panel_width=panel_width)
        self._description.setText(description)

    def _refresh(self) -> None:
        panel_width = self._description_panel_width()
        if self._result is not None and self._result.has_data:
            self._axle_table.update_numbers(self._result.axle_numbers)
            bars = chart_bars_from_esal(self._result)
            description = build_design_period_description_html(
                self._result.design_periods,
                panel_width=panel_width,
            )
        else:
            self._axle_table.update_numbers(None)
            bars = []
            description = _empty_description(panel_width=panel_width)

        self._description.setText(description)
        y_step = self._chart_y_step(bars)
        self._chart_slot.removeWidget(self._chart)
        self._chart.deleteLater()
        self._chart = BarChart(bars, y_step=y_step, show_values=True)
        self._chart_slot.addWidget(self._chart, 1)

    @staticmethod
    def _chart_y_step(bars: list[tuple[str, float, str]]) -> int:
        if not bars:
            return 100_000
        max_value = max(value for _label, value, _color in bars)
        if max_value <= 1_000:
            return 100
        if max_value <= 10_000:
            return 1_000
        if max_value <= 100_000:
            return 10_000
        if max_value <= 1_000_000:
            return 100_000
        return max(100_000, int(math.ceil(max_value / 5 / 100_000)) * 100_000)
