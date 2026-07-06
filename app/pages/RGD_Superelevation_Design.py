"""Road Geometry Design > Superelevation Design."""
from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import QFrame, QGridLayout, QSizePolicy, QVBoxLayout

from app.layouts import BasePage, define_page
from app.widgets.form_controls import make_combo, make_double_spin
from app.widgets.labeled_input import add_labeled_row

VEHICLE_SPEED_OPTIONS = [f"{v} km/h" for v in (25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130)]
ROAD_CLASSIFICATION_OPTIONS = ["Class I", "Class II", "Class III", "Rural", "Urban"]

ROW_HEIGHT = 36


@define_page("scroll", title="Superelevation Design")
class RGDSuperelevationDesignPage(BasePage):
    def setup(self, content: QVBoxLayout) -> None:
        form_widget = QFrame()
        form_widget.setObjectName("inputSectionFrame")
        form_widget.setStyleSheet(
            "#inputSectionFrame { background-color: transparent; border: 1px solid #3e3e40; border-radius: 6px; }"
        )
        form_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        form_grid = QGridLayout(form_widget)
        form_grid.setHorizontalSpacing(12)
        form_grid.setVerticalSpacing(14)
        form_grid.setContentsMargins(16, 12, 16, 16)

        row = 0

        self.vehicle_speed_combo = make_combo(VEHICLE_SPEED_OPTIONS)
        self.vehicle_speed_combo.setCurrentIndex(VEHICLE_SPEED_OPTIONS.index("80 km/h"))
        add_labeled_row(form_grid, row, "Vehicle speed V =", self.vehicle_speed_combo, ROW_HEIGHT)
        row += 1

        self.e1_spin = make_double_spin()
        self.e1_spin.setRange(-10, 10)
        self.e1_spin.setDecimals(2)
        self.e1_spin.setSuffix(" %")
        self.e1_spin.setValue(2.5)
        add_labeled_row(form_grid, row, "Gross fall e1 =", self.e1_spin, ROW_HEIGHT)
        row += 1

        self.e_max_spin = make_double_spin()
        self.e_max_spin.setRange(2.5, 20)
        self.e_max_spin.setDecimals(2)
        self.e_max_spin.setSuffix(" %")
        self.e_max_spin.setValue(5.0)
        add_labeled_row(
            form_grid, row, "Pavement Superelevation (e_max) =", self.e_max_spin, ROW_HEIGHT
        )
        row += 1

        self.road_class_combo = make_combo(ROAD_CLASSIFICATION_OPTIONS)
        add_labeled_row(form_grid, row, "Road Classification =", self.road_class_combo, ROW_HEIGHT)
        row += 1

        self.lane_width_spin = make_double_spin()
        self.lane_width_spin.setRange(2.5, 5.0)
        self.lane_width_spin.setDecimals(2)
        self.lane_width_spin.setSuffix(" m")
        self.lane_width_spin.setValue(3.5)
        add_labeled_row(form_grid, row, "Lane width WR =", self.lane_width_spin, ROW_HEIGHT)

        form_grid.setColumnStretch(1, 1)
        content.addWidget(form_widget)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._setup_preview()

    def activate_page(self) -> None:
        self._setup_preview()

    def _setup_preview(self) -> None:
        mw = self.window()
        if not hasattr(mw, "preview_panel"):
            return
        if hasattr(mw.preview_panel, "set_superelevation_schema"):
            mw.preview_panel.set_superelevation_schema()
        mw.preview_panel.set_results({})
