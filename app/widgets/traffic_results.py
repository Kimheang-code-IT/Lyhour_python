"""Reusable result cards, tables, and charts for traffic analysis views."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
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

from app.core.theme import card_stylesheet, current_theme, table_stylesheet, theme_tokens
from app.core.ui_scale import UiScale
from app.core.ui_style import card_title_style, muted_style, section_title_style, subtitle_style


def result_card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("resultCard")
    frame.setStyleSheet(card_stylesheet(theme_tokens()))
    return frame


def result_description_note(*, dark_background: bool | None = None) -> QFrame:
    """Framed note area for large result description text."""
    note = QFrame()
    note.setObjectName("resultDescriptionNote")
    use_panel = dark_background if dark_background is not None else current_theme() == "dark"
    tokens = theme_tokens()
    if use_panel:
        note.setStyleSheet(card_stylesheet(tokens))
    else:
        note.setStyleSheet(
            "#resultDescriptionNote { border: none; background-color: transparent; }"
        )
    return note


def result_description_label(parent: QWidget | None = None) -> QLabel:
    """Rich-text label used for Road Classification and ESAL summaries."""
    label = QLabel(parent)
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
    return label


def configure_result_description_note_layout(
    note_layout: QVBoxLayout,
    description: QLabel,
    *,
    margins: int = 8,
) -> None:
    """Keep large description text pinned to the top of its card."""
    note_layout.setContentsMargins(margins, margins, margins, margins)
    note_layout.setSpacing(0)
    note_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    note_layout.addWidget(description, 0, Qt.AlignmentFlag.AlignTop)
    note_layout.addStretch(1)


from app.utils.result_html import (
    RESULT_DESCRIPTION_BODY_STYLE,
    RESULT_DESCRIPTION_EMPHASIS_STYLE,
    RESULT_DESCRIPTION_HIGHLIGHT_STYLE,
    RESULT_DESCRIPTION_LINE_GAP_PX,
    RESULT_DESCRIPTION_TITLE_STYLE,
    wrap_result_description_lines,
    wrap_result_description_with_emphasis,
)


def empty_message_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setWordWrap(True)
    label.setStyleSheet(muted_style(15))
    return label


def _table_style() -> str:
    return (
        table_stylesheet(theme_tokens())
        + """
        QTableWidget { border: none; }
        QHeaderView::section { font-weight: bold; }
        QTableWidget::item { padding: 8px; }
    """
    )


def refresh_theme_widgets(root: QWidget) -> None:
    """Re-apply card/table styles after theme change."""
    tokens = theme_tokens()
    card_qss = card_stylesheet(tokens)
    table_qss = _table_style()
    for frame in root.findChildren(QFrame):
        name = frame.objectName()
        if name in ("resultCard", "resultDescriptionNote", "trafficSectionFrame"):
            frame.setStyleSheet(card_qss)
    for table in root.findChildren(QTableWidget):
        table.setStyleSheet(table_qss)
    try:
        from app.widgets.traffic_charts import TrafficTotalLineChart, TrafficVehicleGroupPieChart

        for chart in root.findChildren(TrafficTotalLineChart):
            chart.update()
        for chart in root.findChildren(TrafficVehicleGroupPieChart):
            chart.update()
    except Exception:
        pass


def result_table(headers: list[str], rows: list[list[str]]) -> QTableWidget:
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setAlternatingRowColors(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    table.setStyleSheet(_table_style())

    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            table.setItem(row_index, col_index, QTableWidgetItem(value))
    fit_result_table_height(table)
    return table


def scrollable_result_table(
    headers: list[str],
    rows: list[list[str]],
    *,
    max_visible_rows: int = 12,
    row_height: int | None = None,
    font_size: int = 12,
) -> QTableWidget:
    """Result table with vertical row scrolling and a fixed visible height."""
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setAlternatingRowColors(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    font_pt = UiScale.pt(font_size)
    table.setStyleSheet(f"""
        QTableWidget {{
            background-color: #2d2d30;
            color: #ffffff;
            border: none;
            gridline-color: #3e3e40;
            font-size: {font_pt}pt;
        }}
        QHeaderView::section {{
            background-color: #333333;
            color: #ffffff;
            border: none;
            padding: 8px;
            font-weight: bold;
            font-size: {font_pt}pt;
        }}
        QTableWidget::item {{
            padding: 8px;
            font-size: {font_pt}pt;
        }}
    """)

    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            item = QTableWidgetItem(value)
            font = item.font()
            font.setPointSizeF(font_pt)
            item.setFont(font)
            table.setItem(row_index, col_index, item)

    resolved_row_height = row_height or UiScale.px(42)
    for row in range(table.rowCount()):
        table.setRowHeight(row, resolved_row_height)

    header_height = table.horizontalHeader().height() or UiScale.px(40)
    visible_rows = min(max(table.rowCount(), 1), max_visible_rows)
    table.setFixedHeight(header_height + visible_rows * resolved_row_height + UiScale.px(4))
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
        self.setMinimumHeight(UiScale.px(240))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._bars = bars or []
        self._y_step = y_step
        self._show_legend = show_legend
        self._show_values = show_values

    def _set_chart_font(self, painter: QPainter, base_pt: float) -> None:
        font = painter.font()
        font.setPointSizeF(UiScale.pt(base_pt))
        painter.setFont(font)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        left = UiScale.px(56)
        top = UiScale.px(44 if self._show_legend else 24)
        right = UiScale.px(22)
        bottom = UiScale.px(48)
        rect = self.rect().adjusted(left, top, -right, -bottom)
        painter.setPen(QPen(QColor("#606060"), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())

        if not self._bars:
            self._set_chart_font(painter, 9)
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

        tick_height = UiScale.px(18)
        if self._y_step:
            for tick in range(0, int(axis_max) + self._y_step, self._y_step):
                y = int(rect.bottom() - (tick / axis_max) * rect.height())
                painter.setPen(QPen(QColor("#444444"), 1))
                painter.drawLine(rect.left(), y, rect.right(), y)
                self._set_chart_font(painter, 8)
                painter.setPen(QColor("#cccccc"))
                painter.drawText(4, y - tick_height, UiScale.px(48), tick_height, Qt.AlignmentFlag.AlignRight, str(tick))

        gap = UiScale.px(34)
        bar_width = min(UiScale.px(76), max(UiScale.px(34), int((rect.width() - gap * (len(self._bars) + 1)) / len(self._bars))))
        total_width = len(self._bars) * bar_width + (len(self._bars) - 1) * gap
        start_x = rect.left() + max(0, int((rect.width() - total_width) / 2))
        painter.setPen(Qt.PenStyle.NoPen)
        label_height = UiScale.px(20)
        value_height = UiScale.px(18)

        for index, (label, value, color) in enumerate(self._bars):
            height = int((value / axis_max) * rect.height())
            x = start_x + index * (bar_width + gap)
            y = rect.bottom() - height
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(x, y, bar_width, height, 4, 4)
            if self._show_values:
                self._set_chart_font(painter, 8)
                painter.setPen(QColor("#ffffff"))
                value_text = f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
                painter.drawText(
                    x - UiScale.px(14),
                    y - UiScale.px(22),
                    bar_width + UiScale.px(28),
                    value_height,
                    Qt.AlignmentFlag.AlignCenter,
                    value_text,
                )
            self._set_chart_font(painter, 8)
            painter.setPen(QColor("#cccccc"))
            painter.drawText(
                x - UiScale.px(8),
                rect.bottom() + UiScale.px(8),
                bar_width + UiScale.px(16),
                label_height,
                Qt.AlignmentFlag.AlignCenter,
                label,
            )
            painter.setPen(Qt.PenStyle.NoPen)

        if self._show_legend:
            legend_width = len(self._bars) * UiScale.px(96)
            legend_x = rect.center().x() - legend_width // 2
            for index, (label, _value, color) in enumerate(self._bars):
                x = legend_x + index * UiScale.px(96)
                painter.setBrush(QColor(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(x, UiScale.px(16), UiScale.px(12), UiScale.px(12))
                self._set_chart_font(painter, 8)
                painter.setPen(QColor("#ffffff"))
                painter.drawText(
                    x + UiScale.px(18),
                    UiScale.px(12),
                    UiScale.px(70),
                    label_height,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    label,
                )


class GroupedBarChart(QWidget):
    """Grouped bar chart: each category shows multiple series (e.g. AADT and PCU)."""

    def __init__(
        self,
        groups: list[tuple[str, list[tuple[float, str]]]] | None = None,
        *,
        series_labels: tuple[str, str] = ("AADT", "PCU"),
        y_step: int | None = None,
        show_values: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setMinimumHeight(UiScale.px(240))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._groups = groups or []
        self._series_labels = series_labels
        self._y_step = y_step
        self._show_values = show_values

    def _set_chart_font(self, painter: QPainter, base_pt: float) -> None:
        font = painter.font()
        font.setPointSizeF(UiScale.pt(base_pt))
        painter.setFont(font)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        left = UiScale.px(56)
        top = UiScale.px(44)
        right = UiScale.px(22)
        bottom = UiScale.px(48)
        rect = self.rect().adjusted(left, top, -right, -bottom)
        painter.setPen(QPen(QColor("#606060"), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())

        if not self._groups or not any(
            value > 0 for _label, series in self._groups for value, _color in series
        ):
            self._set_chart_font(painter, 9)
            painter.setPen(QColor("#888888"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No data yet.\nUpload Excel from Traffic Analysis Input.",
            )
            return

        max_value = max(
            value for _label, series in self._groups for value, _color in series
        )
        axis_max = max_value
        if self._y_step:
            axis_max = max(self._y_step, int((max_value + self._y_step - 1) // self._y_step) * self._y_step)

        tick_height = UiScale.px(18)
        if self._y_step:
            for tick in range(0, int(axis_max) + self._y_step, self._y_step):
                y = int(rect.bottom() - (tick / axis_max) * rect.height())
                painter.setPen(QPen(QColor("#444444"), 1))
                painter.drawLine(rect.left(), y, rect.right(), y)
                self._set_chart_font(painter, 8)
                painter.setPen(QColor("#cccccc"))
                painter.drawText(4, y - tick_height, UiScale.px(48), tick_height, Qt.AlignmentFlag.AlignRight, str(tick))

        group_count = len(self._groups)
        series_count = max((len(series) for _label, series in self._groups), default=1)
        group_gap = UiScale.px(28)
        bar_gap = UiScale.px(8)
        group_width = max(
            UiScale.px(56),
            int((rect.width() - group_gap * (group_count + 1)) / max(group_count, 1)),
        )
        bar_width = max(
            UiScale.px(18),
            int((group_width - bar_gap * (series_count - 1)) / max(series_count, 1)),
        )
        total_width = group_count * group_width + (group_count - 1) * group_gap
        start_x = rect.left() + max(0, int((rect.width() - total_width) / 2))
        label_height = UiScale.px(20)
        value_height = UiScale.px(18)

        for group_index, (group_label, series) in enumerate(self._groups):
            group_x = start_x + group_index * (group_width + group_gap)
            bars_total_width = len(series) * bar_width + max(0, len(series) - 1) * bar_gap
            bars_start_x = group_x + max(0, int((group_width - bars_total_width) / 2))
            for series_index, (value, color) in enumerate(series):
                height = int((value / axis_max) * rect.height()) if axis_max else 0
                x = bars_start_x + series_index * (bar_width + bar_gap)
                y = rect.bottom() - height
                painter.setBrush(QColor(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(x, y, bar_width, height, 4, 4)
                if self._show_values and value > 0:
                    self._set_chart_font(painter, 7)
                    painter.setPen(QColor("#ffffff"))
                    value_text = f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
                    painter.drawText(
                        x - UiScale.px(10),
                        y - UiScale.px(20),
                        bar_width + UiScale.px(20),
                        value_height,
                        Qt.AlignmentFlag.AlignCenter,
                        value_text,
                    )
            self._set_chart_font(painter, 8)
            painter.setPen(QColor("#cccccc"))
            painter.drawText(
                group_x,
                rect.bottom() + UiScale.px(8),
                group_width,
                label_height,
                Qt.AlignmentFlag.AlignCenter,
                group_label,
            )

        if self._groups:
            sample_series = self._groups[0][1]
            legend_items = [
                (self._series_labels[index] if index < len(self._series_labels) else f"Series {index + 1}", color)
                for index, (_value, color) in enumerate(sample_series)
            ]
            legend_width = len(legend_items) * UiScale.px(96)
            legend_x = rect.center().x() - legend_width // 2
            for index, (label, color) in enumerate(legend_items):
                x = legend_x + index * UiScale.px(96)
                painter.setBrush(QColor(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(x, UiScale.px(16), UiScale.px(12), UiScale.px(12))
                self._set_chart_font(painter, 8)
                painter.setPen(QColor("#ffffff"))
                painter.drawText(
                    x + UiScale.px(18),
                    UiScale.px(12),
                    UiScale.px(70),
                    label_height,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    label,
                )


def highlight_result_table_row(
    table: QTableWidget,
    row_index: int | None,
    *,
    background: str = "#3a5a7a",
) -> None:
    """Highlight one data row in a result table."""
    if row_index is None or row_index < 0 or row_index >= table.rowCount():
        return
    brush = QBrush(QColor(background))
    for column in range(table.columnCount()):
        item = table.item(row_index, column)
        if item is not None:
            item.setBackground(brush)
            font = item.font()
            font.setBold(True)
            item.setFont(font)


def description_page(title: str, text: str) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)

    card = result_card()
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(16, 16, 16, 16)

    title_label = QLabel(title)
    title_label.setStyleSheet(section_title_style(18))
    desc = QLabel(text)
    desc.setWordWrap(True)
    desc.setStyleSheet(subtitle_style(15, color="#cccccc"))

    card_layout.addWidget(title_label)
    card_layout.addWidget(desc)
    card_layout.addStretch()
    layout.addWidget(card, 1)
    return page
