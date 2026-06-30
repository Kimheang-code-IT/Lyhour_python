"""AADT & PCU subpage."""
import math

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.pages.subpages.common import BarChart, result_card
from app.services.traffic_aadt_pcu import AadtPcuResult


class AadtPcuPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: AadtPcuResult | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        card = result_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)

        title = QLabel("AADT & PCU")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        card_layout.addWidget(title)

        chart_title = QLabel("AADT & PCU by Design Period")
        chart_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        card_layout.addWidget(chart_title)

        self._subtitle = QLabel("Upload Excel from Traffic Analysis Input to calculate AADT and PCU.")
        self._subtitle.setStyleSheet("font-size: 14px; color: #cccccc;")
        self._subtitle.setWordWrap(True)
        card_layout.addWidget(self._subtitle)

        self._chart_slot = QVBoxLayout()
        self._chart_slot.setContentsMargins(0, 0, 0, 0)
        self._chart = BarChart([], y_step=10000, show_values=True)
        self._chart.setMinimumHeight(360)
        self._chart_slot.addWidget(self._chart, 1)
        card_layout.addLayout(self._chart_slot, 1)

        layout.addWidget(card, 1)

    def set_aadt_pcu_result(self, result: AadtPcuResult | None) -> None:
        self._result = result
        self._refresh()

    def _refresh(self) -> None:
        if self._result is not None and self._result.has_data:
            bars = self._result.chart_bars
            year = self._result.design_year_label or "design year"
            growth_pct = self._result.growth_rate * 100
            if self._result.input_source == "direct_input":
                source = "Direct Input"
            else:
                source = "Excel count data"
            subtitle = (
                f"Source: {source} | "
                f"Growth rate R = {growth_pct:g}% | "
                f"Design year for Geometry = {year}"
            )
        else:
            bars = []
            if self._result is not None and self._result.input_source == "direct_input":
                subtitle = "Enter AADT and PCU in the Direct Input section on the Input page."
            else:
                subtitle = "Upload Excel from Traffic Analysis Input to calculate AADT and PCU."

        self._subtitle.setText(subtitle)
        y_step = self._chart_y_step(bars)
        self._chart_slot.removeWidget(self._chart)
        self._chart.deleteLater()
        self._chart = BarChart(bars, y_step=y_step, show_values=True)
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
        return max(10000, int(math.ceil(max_value / 5 / 10000)) * 10000)
