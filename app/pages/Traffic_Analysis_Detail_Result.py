"""Traffic Analysis > Detail Result: segmented result views."""
from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from qfluentwidgets import SegmentedWidget

from app.core.ui_style import title_style
from app.widgets.button import secondary_button
from app.widgets.traffic_results import refresh_theme_widgets

_TAB_SUMMARY = 0
_TAB_AADT = 1
_TAB_ROAD = 2
_TAB_LANE = 3
_TAB_ESAL = 4


class TrafficAnalysisDetailResultPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        self._page_title = QLabel("Detail Result")
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        layout.addLayout(title_row)

        self.segmented = SegmentedWidget(self)
        self.segmented.setObjectName("trafficResultSegmented")
        self.stack = QStackedWidget(self)

        self.summary_page = None
        self.aadt_pcu_page = None
        self.road_classification_page = None
        self.number_of_lane_page = None
        self.esal_page = None

        # Pending payloads applied when a lazy tab is first created.
        self._pending_summary = None
        self._pending_aadt = None
        self._pending_road = None
        self._pending_lane = None
        self._pending_lane_los = None
        self._pending_esal = None

        tab_defs = (
            ("summary", "Summary Traffic count data"),
            ("aadt_pcu", "AADT && PCU"),
            ("road_classification", "Road Classification"),
            ("number_of_lane", "Number of Lane"),
            ("esal", "ESAL"),
        )
        for index, (route_key, text) in enumerate(tab_defs):
            self.segmented.addItem(
                route_key,
                text,
                onClick=lambda _=None, i=index: self._set_tab(i),
            )
            item = self.segmented.widget(route_key)
            if item is not None:
                item.setText(text)
            self.stack.addWidget(QWidget())

        self.segmented.setCurrentItem("summary")
        layout.addWidget(self.segmented)
        layout.addWidget(self.stack, 1)

        self._ensure_tab(_TAB_SUMMARY)
        self.stack.setCurrentIndex(_TAB_SUMMARY)
        self.refresh_ui_scale()

    def _replace_stack_page(self, index: int, page: QWidget) -> None:
        old = self.stack.widget(index)
        self.stack.removeWidget(old)
        if old is not None:
            old.deleteLater()
        self.stack.insertWidget(index, page)

    def _set_tab(self, index: int) -> None:
        self._ensure_tab(index)
        self.stack.setCurrentIndex(index)

    def _ensure_tab(self, index: int) -> None:
        if index == _TAB_SUMMARY:
            if self.summary_page is not None:
                return
            from app.pages.Analysis.summary_traffic_count import SummaryTrafficCountPage

            self.summary_page = SummaryTrafficCountPage()
            self._replace_stack_page(_TAB_SUMMARY, self.summary_page)
            if self._pending_summary is not None:
                args, kwargs = self._pending_summary
                self.summary_page.set_traffic_count_rows(*args, **kwargs)
                self._pending_summary = None
            return

        if index == _TAB_AADT:
            if self.aadt_pcu_page is not None:
                return
            from app.pages.Analysis.aadt_pcu import AadtPcuPage

            self.aadt_pcu_page = AadtPcuPage()
            self._replace_stack_page(_TAB_AADT, self.aadt_pcu_page)
            if self._pending_aadt is not None:
                self.aadt_pcu_page.set_aadt_pcu_result(self._pending_aadt)
                self._pending_aadt = None
            return

        if index == _TAB_ROAD:
            if self.road_classification_page is not None:
                return
            from app.pages.Analysis.road_classification import RoadClassificationPage

            self.road_classification_page = RoadClassificationPage()
            self._replace_stack_page(_TAB_ROAD, self.road_classification_page)
            if self._pending_road is not None:
                self.road_classification_page.set_road_classification(*self._pending_road)
                self._pending_road = None
            return

        if index == _TAB_LANE:
            if self.number_of_lane_page is not None:
                return
            from app.pages.Analysis.number_of_lane import NumberOfLanePage

            self.number_of_lane_page = NumberOfLanePage()
            self._replace_stack_page(_TAB_LANE, self.number_of_lane_page)
            if self._pending_lane is not None:
                self.number_of_lane_page.set_lane_projection(self._pending_lane)
                self._pending_lane = None
            if self._pending_lane_los is not None:
                self.number_of_lane_page.set_lane_los_context(*self._pending_lane_los)
                self._pending_lane_los = None
            return

        if index == _TAB_ESAL:
            if self.esal_page is not None:
                return
            from app.pages.Analysis.esal import EsalPage

            self.esal_page = EsalPage()
            self._replace_stack_page(_TAB_ESAL, self.esal_page)
            if self._pending_esal is not None:
                self.esal_page.set_esal_result(self._pending_esal)
                self._pending_esal = None

    def _iter_pages(self):
        for page in (
            self.summary_page,
            self.aadt_pcu_page,
            self.road_classification_page,
            self.number_of_lane_page,
            self.esal_page,
        ):
            if page is not None:
                yield page

    def refresh_ui_scale(self) -> None:
        self._page_title.setStyleSheet(title_style(22))
        for page in self._iter_pages():
            if hasattr(page, "refresh_ui_scale"):
                page.refresh_ui_scale()

    def refresh_theme(self) -> None:
        refresh_theme_widgets(self)
        self.refresh_ui_scale()
        for page in self._iter_pages():
            if hasattr(page, "refresh_theme"):
                page.refresh_theme()
            elif hasattr(page, "refresh_ui_scale"):
                page.refresh_ui_scale()
        mw = self.window()
        if hasattr(mw, "toggle_quick_panel"):
            self.sync_quick_panel_button(mw.toggle_quick_panel())

    def _toggle_quick_panel(self) -> None:
        mw = self.window()
        if hasattr(mw, "toggle_quick_panel"):
            self.sync_quick_panel_button(mw.toggle_quick_panel())

    def sync_quick_panel_button(self, visible: bool) -> None:
        self.quick_panel_btn.setText("Hide Quick Result" if visible else "Show Quick Result")

    def set_traffic_count_rows(
        self,
        rows: list[list],
        summary_total_row: list | None = None,
        *,
        pie_daily_totals: dict[str, list[int]] | None = None,
    ) -> None:
        self._ensure_tab(_TAB_SUMMARY)
        self.summary_page.set_traffic_count_rows(
            rows,
            summary_total_row=summary_total_row,
            pie_daily_totals=pie_daily_totals,
        )

    def set_aadt_pcu_result(self, result) -> None:
        if self.aadt_pcu_page is None:
            self._pending_aadt = result
            return
        self.aadt_pcu_page.set_aadt_pcu_result(result)

    def set_road_classification(
        self,
        design_year: str | None,
        total_aadt: int | None,
        total_pcu: int | None,
    ) -> None:
        payload = (design_year, total_aadt, total_pcu)
        if self.road_classification_page is None:
            self._pending_road = payload
            return
        self.road_classification_page.set_road_classification(*payload)

    def set_lane_projection(self, result) -> None:
        if self.number_of_lane_page is None:
            self._pending_lane = result
            return
        self.number_of_lane_page.set_lane_projection(result)

    def set_lane_los_context(
        self,
        road_classification: str | None,
        selected_los: str | None,
    ) -> None:
        payload = (road_classification, selected_los)
        if self.number_of_lane_page is None:
            self._pending_lane_los = payload
            return
        self.number_of_lane_page.set_lane_los_context(*payload)

    def set_esal_result(self, result) -> None:
        if self.esal_page is None:
            self._pending_esal = result
            return
        self.esal_page.set_esal_result(result)

    def show_esal_tab(self) -> None:
        self._ensure_tab(_TAB_ESAL)
        self.segmented.setCurrentItem("esal")
        self.stack.setCurrentIndex(_TAB_ESAL)
