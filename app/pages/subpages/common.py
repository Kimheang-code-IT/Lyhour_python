"""Shared widgets for Traffic Analysis detail result subpages."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


def result_card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("resultCard")
    frame.setStyleSheet(
        "#resultCard { background-color: #2d2d30; border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    return frame


def empty_message_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setWordWrap(True)
    label.setStyleSheet("font-size: 15px; color: #888888; padding: 24px;")
    return label


def result_table(headers: list[str], rows: list[list[str]]) -> QTableWidget:
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setAlternatingRowColors(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    table.setStyleSheet("""
        QTableWidget {
            background-color: #2d2d30;
            color: #ffffff;
            border: none;
            gridline-color: #3e3e40;
        }
        QHeaderView::section {
            background-color: #333333;
            color: #ffffff;
            border: none;
            padding: 8px;
            font-weight: bold;
        }
        QTableWidget::item {
            padding: 8px;
        }
    """)

    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            table.setItem(row_index, col_index, QTableWidgetItem(value))
    fit_result_table_height(table)
    return table


def fit_result_table_height(table: QTableWidget, *, row_height: int = 36) -> None:
    """Size the table to fit all rows without an internal scrollbar."""
    for row in range(table.rowCount()):
        table.setRowHeight(row, row_height)
    header_height = table.horizontalHeader().height() or 34
    total_height = header_height + max(table.rowCount(), 1) * row_height + 4
    table.setFixedHeight(total_height)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class BarChart(QWidget):
    """Small dependency-free bar chart for result summaries."""

    def __init__(
        self,
        bars: list[tuple[str, float, str]] | None = None,
        *,
        y_step: int | None = None,
        show_legend: bool = False,
        show_values: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._bars = bars or []
        self._y_step = y_step
        self._show_legend = show_legend
        self._show_values = show_values

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(56, 44 if self._show_legend else 24, -22, -48)
        painter.setPen(QPen(QColor("#606060"), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())

        if not self._bars:
            painter.setPen(QColor("#888888"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No data yet.\nUpload Excel from Traffic Analysis Input.",
            )
            return

        max_value = max(value for _label, value, _color in self._bars)
        axis_max = max_value
        if self._y_step:
            axis_max = max(self._y_step, int((max_value + self._y_step - 1) // self._y_step) * self._y_step)

        if self._y_step:
            for tick in range(0, int(axis_max) + self._y_step, self._y_step):
                y = int(rect.bottom() - (tick / axis_max) * rect.height())
                painter.setPen(QPen(QColor("#444444"), 1))
                painter.drawLine(rect.left(), y, rect.right(), y)
                painter.setPen(QColor("#cccccc"))
                painter.drawText(4, y - 8, 48, 18, Qt.AlignmentFlag.AlignRight, str(tick))

        gap = 34
        bar_width = min(76, max(34, int((rect.width() - gap * (len(self._bars) + 1)) / len(self._bars))))
        total_width = len(self._bars) * bar_width + (len(self._bars) - 1) * gap
        start_x = rect.left() + max(0, int((rect.width() - total_width) / 2))
        painter.setPen(Qt.PenStyle.NoPen)

        for index, (label, value, color) in enumerate(self._bars):
            height = int((value / axis_max) * rect.height())
            x = start_x + index * (bar_width + gap)
            y = rect.bottom() - height
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(x, y, bar_width, height, 4, 4)
            if self._show_values:
                painter.setPen(QColor("#ffffff"))
                value_text = f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
                painter.drawText(x - 14, y - 22, bar_width + 28, 18, Qt.AlignmentFlag.AlignCenter, value_text)
            painter.setPen(QColor("#cccccc"))
            painter.drawText(x - 8, rect.bottom() + 20, bar_width + 16, 20, Qt.AlignmentFlag.AlignCenter, label)
            painter.setPen(Qt.PenStyle.NoPen)

        if self._show_legend:
            legend_width = len(self._bars) * 96
            legend_x = rect.center().x() - legend_width // 2
            for index, (label, _value, color) in enumerate(self._bars):
                x = legend_x + index * 96
                painter.setBrush(QColor(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(x, 16, 12, 12)
                painter.setPen(QColor("#ffffff"))
                painter.drawText(x + 18, 12, 70, 20, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)


def description_page(title: str, text: str) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)

    card = result_card()
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(16, 16, 16, 16)

    title_label = QLabel(title)
    title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
    desc = QLabel(text)
    desc.setWordWrap(True)
    desc.setStyleSheet("font-size: 15px; color: #cccccc;")

    card_layout.addWidget(title_label)
    card_layout.addWidget(desc)
    card_layout.addStretch()
    layout.addWidget(card, 1)
    return page
