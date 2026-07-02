"""Summary Traffic count data subpage."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
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
from app.pages.subpages.common import result_card
from app.services.traffic_excel import sum_d1_d2_vehicle_group_totals

Y_AXIS_STEP = 500
_EMPTY_MESSAGE = "No data yet. Upload Excel from Traffic Analysis Input."


class TrafficTotalLineChart(QWidget):
    """Line chart using time on X and total traffic on Y."""

    def __init__(self, rows: list[list], parent=None):
        super().__init__(parent)
        self._labels = [str(row[0]) for row in rows]
        self._values = [int(row[-1]) for row in rows]
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(self._auto_chart_height())

    def sizeHint(self) -> QSize:
        return QSize(640, self._auto_chart_height())

    def _auto_chart_height(self) -> int:
        return max(UiScale.px(300), UiScale.px(240) + max(0, len(self._values) - 12) * UiScale.px(12))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(UiScale.px(56), UiScale.px(28), -UiScale.px(16), -UiScale.px(64))

        if not self._values:
            label_font = painter.font()
            label_font.setPointSizeF(UiScale.pt(9))
            painter.setFont(label_font)
            painter.setPen(QColor("#888888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _EMPTY_MESSAGE)
            return

        min_value = 0
        max_value = max(self._values)
        axis_max = max(Y_AXIS_STEP, ((max_value + Y_AXIS_STEP - 1) // Y_AXIS_STEP) * Y_AXIS_STEP)
        span = max(axis_max - min_value, 1)
        step_x = rect.width() / max(len(self._values) - 1, 1)

        painter.setPen(QPen(QColor("#606060"), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())

        for value in range(0, axis_max + Y_AXIS_STEP, Y_AXIS_STEP):
            y = int(rect.bottom() - ((value - min_value) / span) * rect.height())
            painter.setPen(QPen(QColor("#444444"), 1))
            painter.drawLine(rect.left(), y, rect.right(), y)
            painter.setPen(QColor("#cccccc"))
            painter.drawText(4, y - UiScale.px(8), UiScale.px(48), UiScale.px(18), Qt.AlignmentFlag.AlignRight, str(value))

        points: list[QPointF] = []
        for index, value in enumerate(self._values):
            x = rect.left() + step_x * index
            y = rect.bottom() - ((value - min_value) / span) * rect.height()
            points.append(QPointF(x, y))

        painter.setPen(QPen(QColor("#4da3ff"), 2))
        for start, end in zip(points, points[1:]):
            painter.drawLine(start, end)

        painter.setBrush(QColor("#4da3ff"))
        painter.setPen(Qt.PenStyle.NoPen)
        for point in points:
            painter.drawEllipse(point, 3, 3)

        painter.setPen(QColor("#cccccc"))
        painter.drawText(8, rect.top() - 18, 52, 18, Qt.AlignmentFlag.AlignRight, "Total")
        painter.drawText(rect.right() - 20, self.height() - 14, "Time")

        label_font = painter.font()
        label_font.setPointSizeF(UiScale.pt(7))
        painter.setFont(label_font)
        label_box = UiScale.px(56)
        for index, (label, value, point) in enumerate(zip(self._labels, self._values, points)):
            x = int(rect.left() + step_x * index - label_box / 2)
            painter.drawText(x, rect.bottom() + UiScale.px(6), label_box, UiScale.px(34), Qt.AlignmentFlag.AlignCenter, label.replace(":00", ""))
            value_y = max(rect.top() - UiScale.px(20), int(point.y()) - UiScale.px(18))
            painter.drawText(x, value_y, label_box, UiScale.px(18), Qt.AlignmentFlag.AlignCenter, str(value))


class TrafficVehicleGroupPieChart(QWidget):
    """Pie chart for three vehicle groups (D1 + D2 summed)."""

    def __init__(self, groups: list[tuple[str, int, str]] | None = None, parent=None):
        super().__init__(parent)
        self._groups = groups or []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(UiScale.px(300))
        self.setMinimumWidth(UiScale.px(220))

    def sizeHint(self) -> QSize:
        return QSize(280, 320)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._groups or not any(value for _label, value, _color in self._groups):
            label_font = painter.font()
            label_font.setPointSizeF(UiScale.pt(9))
            painter.setFont(label_font)
            painter.setPen(QColor("#888888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _EMPTY_MESSAGE)
            return

        total = sum(value for _label, value, _color in self._groups)
        if total <= 0:
            label_font = painter.font()
            label_font.setPointSizeF(UiScale.pt(9))
            painter.setFont(label_font)
            painter.setPen(QColor("#888888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _EMPTY_MESSAGE)
            return

        side = min(self.width() - UiScale.px(24), self.height() - UiScale.px(120), UiScale.px(220))
        pie_rect = QRectF(
            (self.width() - side) / 2,
            UiScale.px(28),
            side,
            side,
        )

        start_angle = 90 * 16
        for _label, value, color in self._groups:
            if value <= 0:
                continue
            span_angle = -int(round((value / total) * 360 * 16))
            painter.setBrush(QColor(color))
            painter.setPen(QPen(QColor("#1e1e1e"), 2))
            painter.drawPie(pie_rect, start_angle, span_angle)
            start_angle += span_angle

        legend_y = int(pie_rect.bottom()) + UiScale.px(16)
        row_height = UiScale.px(22)
        legend_font = painter.font()
        legend_font.setPointSizeF(UiScale.pt(8))
        painter.setFont(legend_font)
        for index, (label, value, color) in enumerate(self._groups):
            y = legend_y + index * row_height
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(UiScale.px(12), y + UiScale.px(4), UiScale.px(12), UiScale.px(12), 2, 2)
            percent = (value / total) * 100
            painter.setPen(QColor("#ffffff"))
            painter.drawText(
                UiScale.px(30),
                y,
                self.width() - UiScale.px(36),
                row_height,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{label}: {value:,} ({percent:.1f}%)",
            )


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


def _chart_card(title: str, chart: QWidget) -> tuple[QFrame, QLabel]:
    card = result_card()
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


class SummaryTrafficCountPage(QWidget):
    """Summary tab with traffic-count table and charts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[list] = []
        self._summary_total_row = None
        self._pie_groups: list[tuple[str, int, str]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        table_card = result_card()
        table_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._table_layout = QVBoxLayout(table_card)
        self._table_layout.setContentsMargins(0, 0, 0, 0)
        self._table = traffic_count_summary_table(self._rows)
        self._table_layout.addWidget(self._table)
        table_card.setFixedHeight(self._table.height())
        layout.addWidget(table_card)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        self._line_chart = TrafficTotalLineChart(self._rows)
        line_card, self._line_chart_title = _chart_card("Total traffic by time", self._line_chart)

        self._pie_chart = TrafficVehicleGroupPieChart(self._pie_groups)
        pie_card, self._pie_chart_title = _chart_card("Vehicle type analysis (D1 + D2)", self._pie_chart)

        charts_row.addWidget(line_card, 2)
        charts_row.addWidget(pie_card, 1)
        layout.addLayout(charts_row, 1)
        self.refresh_ui_scale()

    def refresh_ui_scale(self) -> None:
        self._line_chart_title.setStyleSheet(card_title_style(14))
        self._pie_chart_title.setStyleSheet(card_title_style(14))
        self._table.apply_ui_scale()
        self._line_chart.setMinimumHeight(self._line_chart._auto_chart_height())
        self._line_chart.update()
        self._pie_chart.setMinimumHeight(UiScale.px(300))
        self._pie_chart.setMinimumWidth(UiScale.px(220))
        self._pie_chart.update()
        table_card = self._table.parentWidget()
        if table_card is not None:
            table_card.setFixedHeight(self._table.height())

    def set_traffic_count_rows(
        self,
        rows: list[list],
        summary_total_row: list | None = None,
        *,
        pie_daily_totals: dict[str, list[int]] | None = None,
    ) -> None:
        """Update table and charts from parsed Excel rows."""
        self._rows = rows
        self._summary_total_row = summary_total_row
        self._pie_groups = sum_d1_d2_vehicle_group_totals(pie_daily_totals)

        self._table_layout.removeWidget(self._table)
        self._table.deleteLater()
        self._table = traffic_count_summary_table(self._rows, summary_total_row=self._summary_total_row)
        self._table_layout.addWidget(self._table)
        self._table.apply_ui_scale()
        table_card = self._table.parentWidget()
        if table_card is not None:
            table_card.setFixedHeight(self._table.height())

        self._line_chart._labels = [str(row[0]) for row in rows]
        self._line_chart._values = [int(row[-1]) for row in rows]
        self._line_chart.setMinimumHeight(self._line_chart._auto_chart_height())
        self._line_chart.update()

        self._pie_chart._groups = self._pie_groups
        self._pie_chart.update()
