"""Summary Traffic count data subpage."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.ui_scale import UiScale
from app.core.ui_style import card_title_style
from app.services.traffic_excel import sum_d1_d2_vehicle_group_totals
from app.widgets.traffic_charts import TrafficTotalLineChart, TrafficVehicleGroupPieChart
from app.widgets.traffic_results import refresh_theme_widgets, result_card
from app.widgets.traffic_summary_table import traffic_count_summary_table


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


class SummaryTrafficCountPage(QWidget):
    """Summary tab with traffic-count table and charts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[list] = []
        self._summary_total_row = None
        self._pie_groups: list[tuple[str, int, str]] = []

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

        table_card = result_card()
        table_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._table_layout = QVBoxLayout(table_card)
        self._table_layout.setContentsMargins(0, 0, 0, 0)
        self._table = traffic_count_summary_table(self._rows)
        self._table_layout.addWidget(self._table)
        table_card.setFixedHeight(self._table.height())
        layout.addWidget(table_card)

        charts_column = QVBoxLayout()
        charts_column.setSpacing(16)

        self._line_chart = TrafficTotalLineChart(self._rows)
        line_card, self._line_chart_title = _chart_card("Total traffic by time", self._line_chart)

        self._pie_chart = TrafficVehicleGroupPieChart(self._pie_groups)
        pie_card, self._pie_chart_title = _chart_card("Vehicle type", self._pie_chart, fixed_chart=True)

        charts_column.addWidget(line_card)
        charts_column.addWidget(pie_card)
        layout.addLayout(charts_column)
        layout.addStretch()

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)
        self.refresh_ui_scale()

    def refresh_ui_scale(self) -> None:
        self._line_chart_title.setStyleSheet(card_title_style(14))
        self._pie_chart_title.setStyleSheet(card_title_style(14))
        self._table.apply_ui_scale()
        self._line_chart.setMinimumHeight(self._line_chart._auto_chart_height())
        self._line_chart.update()
        self._pie_chart.setMinimumHeight(UiScale.px(260))
        self._pie_chart.setFixedHeight(UiScale.px(260))
        self._pie_chart.update()
        table_card = self._table.parentWidget()
        if table_card is not None:
            table_card.setFixedHeight(self._table.height())

    def refresh_theme(self) -> None:
        refresh_theme_widgets(self)
        self.refresh_ui_scale()

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
