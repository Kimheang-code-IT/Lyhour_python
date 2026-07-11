"""Number of Lane subpage."""
from __future__ import annotations

import math

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.core.ui_scale import UiScale
from app.core.ui_style import card_title_style, label_style, section_title_style, subtitle_style
from app.data.level_of_service import (
    LOS_OPTIONS,
    build_lane_los_suggestion_text,
    suggest_level_of_service,
)
from app.services.traffic_lane_projection import (
    PROJECTION_COLUMNS,
    LaneProjectionResult,
    chart_bars_from_projection,
)
from app.widgets.form_controls import make_combo
from app.widgets.traffic_results import BarChart, refresh_theme_widgets, result_card, result_description_label, scrollable_result_table


class NumberOfLanePage(QWidget):
    _TABLE_MAX_VISIBLE_ROWS = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: LaneProjectionResult | None = None
        self._road_classification: str | None = None
        self._syncing_los = False

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
        chart_layout.setSpacing(8)

        self._los_row = QWidget()
        los_row_layout = QHBoxLayout(self._los_row)
        los_row_layout.setContentsMargins(0, 0, 0, 0)
        los_row_layout.setSpacing(UiScale.px(12))

        self._los_label = QLabel("Level of service")
        self._los_combo = make_combo(LOS_OPTIONS)
        los_row_layout.addWidget(self._los_label)
        los_row_layout.addWidget(self._los_combo)
        los_row_layout.addStretch(1)

        self._los_suggestion = result_description_label()
        self._los_suggestion.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        los_row_layout.addWidget(self._los_suggestion, 1)
        chart_layout.addWidget(self._los_row)

        self._title = QLabel("Number of Lane")
        chart_layout.addWidget(self._title)

        self._subtitle = QLabel("Required Road Lanes by Future Year")
        chart_layout.addWidget(self._subtitle)

        self._chart_slot = QVBoxLayout()
        self._chart_slot.setContentsMargins(0, 0, 0, 0)
        self._chart = BarChart([], y_step=1, show_values=True)
        self._chart_slot.addWidget(self._chart)
        chart_layout.addLayout(self._chart_slot)
        layout.addWidget(chart_card)

        table_card = result_card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(8)

        self._table_title = QLabel("Lane Projection by Year")
        table_layout.addWidget(self._table_title)

        self._table_slot = QVBoxLayout()
        self._table_slot.setContentsMargins(0, 0, 0, 0)
        self._table = scrollable_result_table(
            PROJECTION_COLUMNS,
            [],
            max_visible_rows=self._TABLE_MAX_VISIBLE_ROWS,
        )
        self._table_slot.addWidget(self._table)
        table_layout.addLayout(self._table_slot)
        layout.addWidget(table_card)
        layout.addStretch()

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)

        self._los_combo.currentTextChanged.connect(self._on_los_changed)
        self.set_lane_los_context(None, LOS_OPTIONS[0])
        self.refresh_ui_scale()

    def set_lane_projection(self, result: LaneProjectionResult | None) -> None:
        self._result = result
        self._refresh()

    def set_lane_los_context(
        self,
        road_classification: str | None,
        selected_los: str | None,
    ) -> None:
        self._road_classification = road_classification
        los = (selected_los or "").strip() or LOS_OPTIONS[0]
        self._syncing_los = True
        if los in LOS_OPTIONS:
            self._los_combo.setCurrentText(los)
        self._syncing_los = False
        self._refresh_los_suggestion()

    def active_los(self) -> str:
        return self._los_combo.currentText()

    def refresh_ui_scale(self) -> None:
        self._los_label.setStyleSheet(label_style(14))
        self._title.setStyleSheet(section_title_style(18))
        self._subtitle.setStyleSheet(subtitle_style(14))
        self._table_title.setStyleSheet(card_title_style(14))
        self._refresh()
        self._refresh_los_suggestion()

    def refresh_theme(self) -> None:
        refresh_theme_widgets(self)
        self.refresh_ui_scale()

    def _on_los_changed(self, _text: str) -> None:
        if self._syncing_los:
            return
        mw = self.window()
        if hasattr(mw, "sync_input_los_from_lane_page"):
            mw.sync_input_los_from_lane_page(self.active_los())

    def _refresh_los_suggestion(self) -> None:
        suggested = suggest_level_of_service(self._road_classification)
        self._los_suggestion.setText(
            build_lane_los_suggestion_text(self._road_classification, suggested)
        )

    def _chart_height(self, bar_count: int) -> int:
        base = UiScale.px(360)
        if bar_count <= 5:
            return base
        return base + (bar_count - 5) * UiScale.px(28)

    def _refresh(self) -> None:
        if self._result is not None and self._result.has_data:
            bars = chart_bars_from_projection(list(self._result.projection_rows))
            table_rows = self._result.projection_table_rows
            subtitle = (
                f"D1 peak: {self._result.d1_peak_volume:,} | "
                f"D2 peak: {self._result.d2_peak_volume:,}"
            )
        else:
            bars = []
            table_rows = []
            subtitle = "Upload Excel from Traffic Analysis Input to calculate lanes."

        self._subtitle.setText(subtitle)
        y_step = self._chart_y_step(bars)
        chart_height = self._chart_height(len(bars))
        self._chart_slot.removeWidget(self._chart)
        self._chart.deleteLater()
        self._chart = BarChart(bars, y_step=y_step, show_values=True)
        self._chart.setMinimumHeight(chart_height)
        self._chart.setFixedHeight(chart_height)
        self._chart_slot.addWidget(self._chart)

        self._table_slot.removeWidget(self._table)
        self._table.deleteLater()
        self._table = scrollable_result_table(
            PROJECTION_COLUMNS,
            table_rows,
            max_visible_rows=self._TABLE_MAX_VISIBLE_ROWS,
        )
        self._table_slot.addWidget(self._table)

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
