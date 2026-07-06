"""AADT & PCU subpage."""
import math

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.core.ui_scale import UiScale
from app.core.ui_style import card_title_style
from app.widgets.traffic_results import (
    GroupedBarChart,
    highlight_result_table_row,
    refresh_theme_widgets,
    result_card,
    scrollable_result_table,
)
from app.services.traffic_aadt_pcu import AadtPcuResult


class AadtPcuPage(QWidget):
    _TABLE_MAX_VISIBLE_ROWS = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: AadtPcuResult | None = None

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        chart_card = result_card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        chart_layout.setSpacing(12)

        self._chart_title = QLabel("AADT & PCU by Design Year")
        chart_layout.addWidget(self._chart_title)

        self._chart_slot = QVBoxLayout()
        self._chart_slot.setContentsMargins(0, 0, 0, 0)
        self._chart = GroupedBarChart([], y_step=10000, show_values=True)
        self._chart_slot.addWidget(self._chart)
        chart_layout.addLayout(self._chart_slot)
        layout.addWidget(chart_card)

        table_card = result_card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(8)

        self._table_title = QLabel("Projected Traffic by Year")
        table_layout.addWidget(self._table_title)

        self._table_slot = QVBoxLayout()
        self._table_slot.setContentsMargins(0, 0, 0, 0)
        self._table = scrollable_result_table(
            ["Year", "AADT", "PCU"],
            [],
            max_visible_rows=self._TABLE_MAX_VISIBLE_ROWS,
        )
        self._table_slot.addWidget(self._table)
        table_layout.addLayout(self._table_slot)
        layout.addWidget(table_card)
        layout.addStretch()

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)
        self.refresh_ui_scale()

    def set_aadt_pcu_result(self, result: AadtPcuResult | None) -> None:
        self._result = result
        self._refresh()

    def refresh_ui_scale(self) -> None:
        self._chart_title.setStyleSheet(card_title_style(14))
        self._table_title.setStyleSheet(card_title_style(14))
        self._refresh()

    def refresh_theme(self) -> None:
        refresh_theme_widgets(self)
        self.refresh_ui_scale()

    def _chart_height(self, group_count: int) -> int:
        base = UiScale.px(320)
        if group_count <= 4:
            return base
        return base + (group_count - 4) * UiScale.px(28)

    def _refresh(self) -> None:
        if self._result is not None and self._result.has_data:
            groups = self._result.chart_groups
            table_rows = self._result.projection_table_rows
            highlight_row = self._result.projection_table_highlight_row
        else:
            groups = []
            table_rows = []
            highlight_row = None

        y_step = self._chart_y_step(groups)
        chart_height = self._chart_height(len(groups))
        self._chart_slot.removeWidget(self._chart)
        self._chart.deleteLater()
        self._chart = GroupedBarChart(groups, y_step=y_step, show_values=True)
        self._chart.setMinimumHeight(chart_height)
        self._chart.setFixedHeight(chart_height)
        self._chart_slot.addWidget(self._chart)

        self._table_slot.removeWidget(self._table)
        self._table.deleteLater()
        self._table = scrollable_result_table(
            ["Year", "AADT", "PCU"],
            table_rows,
            max_visible_rows=self._TABLE_MAX_VISIBLE_ROWS,
        )
        highlight_result_table_row(self._table, highlight_row)
        if highlight_row is not None:
            item = self._table.item(highlight_row, 0)
            if item is not None:
                self._table.scrollToItem(
                    item,
                    QAbstractItemView.ScrollHint.PositionAtCenter,
                )
        self._table_slot.addWidget(self._table)

    @staticmethod
    def _chart_y_step(groups: list[tuple[str, list[tuple[float, str]]]]) -> int:
        values = [value for _label, series in groups for value, _color in series]
        if not values:
            return 10000
        max_value = max(values)
        if max_value <= 1000:
            return 100
        if max_value <= 10000:
            return 1000
        if max_value <= 100000:
            return 10000
        return max(10000, int(math.ceil(max_value / 5 / 10000)) * 10000)
