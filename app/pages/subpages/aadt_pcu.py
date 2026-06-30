"""AADT & PCU subpage."""
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.pages.subpages.common import BarChart, result_card
from app.services.traffic_aadt_pcu import AadtPcuResult


class AadtPcuPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: AadtPcuResult | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = result_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)

        title = QLabel("AADT & PCU")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        card_layout.addWidget(title)

        self._chart_slot = QVBoxLayout()
        self._chart_slot.setContentsMargins(0, 0, 0, 0)
        self._chart = BarChart([], y_step=10000, show_legend=True, show_values=True)
        self._chart.setMinimumHeight(360)
        self._chart_slot.addWidget(self._chart, 1)
        card_layout.addLayout(self._chart_slot, 1)
        layout.addWidget(card, 1)

    def set_aadt_pcu_result(self, result: AadtPcuResult | None) -> None:
        self._result = result
        self._refresh_chart()

    def _refresh_chart(self) -> None:
        bars = self._result.chart_bars if self._result and self._result.total_aadt else []
        y_step = self._chart_y_step(bars)
        self._chart_slot.removeWidget(self._chart)
        self._chart.deleteLater()
        self._chart = BarChart(bars, y_step=y_step, show_legend=True, show_values=True)
        self._chart.setMinimumHeight(360)
        self._chart_slot.addWidget(self._chart, 1)

    @staticmethod
    def _chart_y_step(bars: list[tuple[str, float, str]]) -> int:
        if not bars:
            return 10000
        max_value = max(value for _label, value, _color in bars)
        if max_value <= 1000:
            return 100
        if max_value <= 10000:
            return 1000
        if max_value <= 100000:
            return 10000
        return 50000
