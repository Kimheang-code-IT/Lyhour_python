"""Traffic Analysis > Detail Result: segmented result views."""
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from qfluentwidgets import SegmentedWidget

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
        lbl = QLabel("Detail Result")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        title_row.addWidget(lbl)
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
        tabs = [
            ("summary", "Summary Traffic count data", self.summary_page),
            ("aadt_pcu", "AADT&PCU", self.aadt_pcu_page),
            ("road_classification", "Road Classification", RoadClassificationPage()),
            ("number_of_lane", "Number of Lane", NumberOfLanePage()),
            ("esal", "ESAL", EsalPage()),
        ]

        for index, (route_key, text, page) in enumerate(tabs):
            self.segmented.addItem(route_key, text, onClick=lambda _=None, i=index: self.stack.setCurrentIndex(i))
            self.stack.addWidget(page)

        self.segmented.setCurrentItem("summary")
        self.stack.setCurrentIndex(0)
        layout.addWidget(self.segmented)
        layout.addWidget(self.stack, 1)

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
    ) -> None:
        self.summary_page.set_traffic_count_rows(rows, summary_total_row=summary_total_row)

    def set_aadt_pcu_result(self, result) -> None:
        self.aadt_pcu_page.set_aadt_pcu_result(result)
