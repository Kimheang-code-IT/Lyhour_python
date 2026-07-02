"""Traffic Analysis > Detail Result: segmented result views."""
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from qfluentwidgets import SegmentedWidget

from app.core.ui_style import title_style
from app.pages.subpages.aadt_pcu import AadtPcuPage
from app.pages.subpages.esal import EsalPage
from app.pages.subpages.number_of_lane import NumberOfLanePage
from app.pages.subpages.road_classification import RoadClassificationPage
from app.pages.subpages.summary_traffic_count import SummaryTrafficCountPage
from app.widgets.button import secondary_button


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

        self.summary_page = SummaryTrafficCountPage()
        self.aadt_pcu_page = AadtPcuPage()
        self.road_classification_page = RoadClassificationPage()
        self.number_of_lane_page = NumberOfLanePage()
        self.esal_page = EsalPage()
        tabs = [
            ("summary", "Summary Traffic count data", self.summary_page),
            ("aadt_pcu", "AADT && PCU", self.aadt_pcu_page),
            ("road_classification", "Road Classification", self.road_classification_page),
            ("number_of_lane", "Number of Lane", self.number_of_lane_page),
            ("esal", "ESAL", self.esal_page),
        ]

        for index, (route_key, text, page) in enumerate(tabs):
            self.segmented.addItem(route_key, text, onClick=lambda _=None, i=index: self.stack.setCurrentIndex(i))
            item = self.segmented.widget(route_key)
            if item is not None:
                # Qt treats "&" as mnemonic markup in button text; "&&" displays as "&".
                item.setText(text)
            self.stack.addWidget(page)

        self.segmented.setCurrentItem("summary")
        self.stack.setCurrentIndex(0)
        layout.addWidget(self.segmented)
        layout.addWidget(self.stack, 1)
        self.refresh_ui_scale()

    def refresh_ui_scale(self) -> None:
        self._page_title.setStyleSheet(title_style(22))
        for page in (
            self.summary_page,
            self.aadt_pcu_page,
            self.road_classification_page,
            self.number_of_lane_page,
            self.esal_page,
        ):
            if hasattr(page, "refresh_ui_scale"):
                page.refresh_ui_scale()

    def _toggle_quick_panel(self):
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
        self.summary_page.set_traffic_count_rows(
            rows,
            summary_total_row=summary_total_row,
            pie_daily_totals=pie_daily_totals,
        )

    def set_aadt_pcu_result(self, result) -> None:
        self.aadt_pcu_page.set_aadt_pcu_result(result)

    def set_road_classification(
        self,
        design_year: str | None,
        total_aadt: int | None,
        total_pcu: int | None,
    ) -> None:
        self.road_classification_page.set_road_classification(
            design_year,
            total_aadt,
            total_pcu,
        )

    def set_lane_projection(self, result) -> None:
        self.number_of_lane_page.set_lane_projection(result)

    def set_esal_result(self, result) -> None:
        self.esal_page.set_esal_result(result)
