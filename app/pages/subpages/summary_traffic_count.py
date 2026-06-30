"""Summary Traffic count data subpage."""
from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.pages.subpages.common import result_card

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
        return QSize(900, self._auto_chart_height())

    def _auto_chart_height(self) -> int:
        return max(320, 260 + max(0, len(self._values) - 12) * 14)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(64, 38, -24, -70)

        if not self._values:
            painter.setPen(QColor("#888888"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                _EMPTY_MESSAGE,
            )
            return

        min_value = 0
        max_value = max(self._values)
        axis_max = max(Y_AXIS_STEP, ((max_value + Y_AXIS_STEP - 1) // Y_AXIS_STEP) * Y_AXIS_STEP)
        span = max(axis_max - min_value, 1)
        step_x = rect.width() / max(len(self._values) - 1, 1)

        painter.setPen(QPen(QColor("#606060"), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())

        tick_values = range(0, axis_max + Y_AXIS_STEP, Y_AXIS_STEP)
        for value in tick_values:
            y = int(rect.bottom() - ((value - min_value) / span) * rect.height())
            painter.setPen(QPen(QColor("#444444"), 1))
            painter.drawLine(rect.left(), y, rect.right(), y)
            painter.setPen(QColor("#cccccc"))
            painter.drawText(6, y - 8, 52, 18, Qt.AlignmentFlag.AlignRight, str(value))

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
        painter.drawText(8, rect.top() - 24, 52, 18, Qt.AlignmentFlag.AlignRight, "Total")
        painter.drawText(rect.right() - 20, self.height() - 16, "Time")

        label_font = painter.font()
        label_font.setPointSize(7)
        painter.setFont(label_font)
        for index, (label, value, point) in enumerate(zip(self._labels, self._values, points)):
            x = int(rect.left() + step_x * index - 28)
            painter.drawText(x, rect.bottom() + 8, 56, 34, Qt.AlignmentFlag.AlignCenter, label.replace(":00", ""))

            value_y = max(rect.top() - 22, int(point.y()) - 20)
            painter.drawText(x, value_y, 56, 18, Qt.AlignmentFlag.AlignCenter, str(value))


class TrafficCountSummaryTable(QWidget):
    """Compact Excel-style total table with two header rows and one total row."""

    _COLUMN_WIDTHS = [78, 58, 66, 58, 72, 64, 68, 72, 84, 58, 58, 58, 68, 72, 76, 68, 72, 76, 76, 62]
    _HEADER_ROW_HEIGHT = 25
    _BODY_ROW_HEIGHT = 26

    def __init__(self, rows: list[list] | None = None, summary_total_row: list | None = None, parent=None):
        super().__init__(parent)
        self._rows = rows or []
        self._summary_total_row = summary_total_row

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header_table = QTableWidget(2, 20)
        self.body_table = QTableWidget(1, 20)
        self._configure_table(self.header_table, is_header=True)
        self._configure_table(self.body_table, is_header=False)
        self._populate_header()
        self._populate_body()

        self.header_table.setFixedHeight(self._HEADER_ROW_HEIGHT * 2 + 2)
        self.body_table.setFixedHeight(self._BODY_ROW_HEIGHT + 2)

        layout.addWidget(self.header_table)
        layout.addWidget(self.body_table)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_columns_to_width()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_columns_to_width()

    def _configure_table(self, table: QTableWidget, *, is_header: bool) -> None:
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setShowGrid(True)
        table.setWordWrap(True)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        row_height = self._HEADER_ROW_HEIGHT if is_header else self._BODY_ROW_HEIGHT
        for row in range(table.rowCount()):
            table.setRowHeight(row, row_height)

    def _set_item(self, table: QTableWidget, row: int, column: int, text: str, brush: QBrush, bold: bool = False) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setBackground(brush)
        font = item.font()
        font.setPointSize(7)
        font.setBold(bold)
        item.setFont(font)
        table.setItem(row, column, item)

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
            self._set_item(self.header_table, 0, column, text, header_brush, bold=True)
            self.header_table.setSpan(0, column, 2, 1)

        axle_groups = [
            (9, "2 axles", 2),
            (11, "3 axles", 1),
            (12, "4 axles", 3),
            (15, "5 axles", 3),
            (18, "6 axles", 1),
        ]
        for column, text, span in axle_groups:
            self._set_item(self.header_table, 0, column, text, header_brush, bold=True)
            if span > 1:
                self.header_table.setSpan(0, column, 1, span)

        axle_headers = [
            "4 tires", "6 tires", "6 tires",
            "No-trailer", "Full-trailer", "Semi-trailer", "No-trailer", "Full-trailer",
            "Semi-trailer", "Semi-trailer",
        ]
        for column, text in enumerate(axle_headers, start=9):
            self._set_item(self.header_table, 1, column, text, header_brush, bold=True)

    def _populate_body(self) -> None:
        total_brush = QBrush(QColor("#888888"))
        if self._summary_total_row and len(self._summary_total_row) >= 20:
            totals = self._summary_total_row[:20]
        elif self._rows:
            totals = ["Total"] + [sum(int(row[column]) for row in self._rows) for column in range(1, 20)]
        else:
            totals = ["Total"] + ["-"] * 19
        for column, value in enumerate(totals):
            self._set_item(self.body_table, 0, column, str(value), total_brush, bold=True)

    def _fit_columns_to_width(self) -> None:
        available_width = self.body_table.viewport().width()
        if available_width <= 0:
            return

        min_width = 28
        if available_width < min_width * len(self._COLUMN_WIDTHS):
            equal_width = max(1, available_width // len(self._COLUMN_WIDTHS))
            scaled_widths = [equal_width] * len(self._COLUMN_WIDTHS)
            scaled_widths[-1] += available_width - sum(scaled_widths)
        else:
            total_base_width = sum(self._COLUMN_WIDTHS)
            scaled_widths = [max(min_width, int(width * available_width / total_base_width)) for width in self._COLUMN_WIDTHS]
            if sum(scaled_widths) != available_width:
                scaled_widths[-1] += available_width - sum(scaled_widths)

        for column, width in enumerate(scaled_widths):
            self.header_table.setColumnWidth(column, width)
            self.body_table.setColumnWidth(column, width)


def traffic_count_summary_table(
    rows: list[list] | None = None,
    summary_total_row: list | None = None,
) -> TrafficCountSummaryTable:
    return TrafficCountSummaryTable(rows, summary_total_row=summary_total_row)


class SummaryTrafficCountPage(QWidget):
    """Summary tab with traffic-count table and total-by-time chart."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[list] = []
        self._summary_total_row = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        table_card = result_card()
        self._table_layout = QVBoxLayout(table_card)
        self._table_layout.setContentsMargins(0, 0, 0, 0)
        self._table = traffic_count_summary_table(self._rows)
        self._table_layout.addWidget(self._table)
        layout.addWidget(table_card)

        chart_card = result_card()
        chart_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._chart_layout = QVBoxLayout(chart_card)
        self._chart_layout.setContentsMargins(12, 12, 12, 12)
        self._chart_layout.addWidget(QLabel("Total traffic by time"))
        self._chart = TrafficTotalLineChart(self._rows)
        self._chart_layout.addWidget(self._chart, 1)
        layout.addWidget(chart_card, 1)

    def set_traffic_count_rows(
        self,
        rows: list[list],
        summary_total_row: list | None = None,
    ) -> None:
        """Update table and chart from parsed Excel rows."""
        self._rows = rows
        self._summary_total_row = summary_total_row
        self._table_layout.removeWidget(self._table)
        self._table.deleteLater()
        self._table = traffic_count_summary_table(self._rows, summary_total_row=self._summary_total_row)
        self._table_layout.addWidget(self._table)

        self._chart_layout.removeWidget(self._chart)
        self._chart.deleteLater()
        self._chart = TrafficTotalLineChart(self._rows)
        self._chart_layout.addWidget(self._chart, 1)
