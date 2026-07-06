"""Number of Lane subpage."""
import math

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.core.ui_scale import UiScale
from app.core.ui_style import section_title_style, subtitle_style
from app.widgets.traffic_results import BarChart, refresh_theme_widgets, result_card
from app.services.traffic_lane_projection import LaneProjectionResult, chart_bars_from_projection


class NumberOfLanePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: LaneProjectionResult | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = result_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        self._title = QLabel("Number of Lane")
        card_layout.addWidget(self._title)

        self._subtitle = QLabel("Required Road Lanes by Future Year")
        card_layout.addWidget(self._subtitle)

        self._chart_slot = QVBoxLayout()
        self._chart_slot.setContentsMargins(0, 0, 0, 0)
        self._chart = BarChart([], y_step=1, show_values=True)
        self._chart_slot.addWidget(self._chart, 1)
        card_layout.addLayout(self._chart_slot, 1)
        layout.addWidget(card, 1)
        self.refresh_ui_scale()

    def set_lane_projection(self, result: LaneProjectionResult | None) -> None:
        self._result = result
        self._refresh_chart()

    def refresh_ui_scale(self) -> None:
        self._title.setStyleSheet(section_title_style(18))
        self._subtitle.setStyleSheet(subtitle_style(14))
        self._refresh_chart()

    def refresh_theme(self) -> None:
        refresh_theme_widgets(self)
        self.refresh_ui_scale()

    def _refresh_chart(self) -> None:
        if self._result is not None and self._result.has_data:
            bars = chart_bars_from_projection(list(self._result.projection_rows))
            subtitle = (
                f"D1 peak: {self._result.d1_peak_volume:,} | "
                f"D2 peak: {self._result.d2_peak_volume:,}"
            )
        else:
            bars = []
            subtitle = "Upload Excel from Traffic Analysis Input to calculate lanes."

        self._subtitle.setText(subtitle)
        y_step = self._chart_y_step(bars)
        self._chart_slot.removeWidget(self._chart)
        self._chart.deleteLater()
        self._chart = BarChart(bars, y_step=y_step, show_values=True)
        self._chart.setMinimumHeight(UiScale.px(360))
        self._chart_slot.addWidget(self._chart, 1)

    @staticmethod
    def _chart_y_step(bars: list[tuple[str, float, str]]) -> int:
        if not bars:
            return 1
        max_value = max(value for _label, value, _color in bars)
        if max_value <= 4:
            return 1
        if max_value <= 10:
            return 2
        return max(2, int(math.ceil(max_value / 5)))
