"""Flexible Pavement > Catalog / Analysis page."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.chart import MatplotlibChartWidget, draw_pavement_catalog_section
from app.core.theme import theme_tokens
from app.data.pavement_catalog import (
    CATALOG_OPTIONS_BY_SEAL,
    FOUNDATION_OPTIONS,
    available_traffic_classes,
    foundation_from_cbr,
    lookup_pavement_design,
    summarize_pavement_design,
)
from app.pages.Flexible_Pavement.common import (
    BLOCK_SPACING,
    ROW_HEIGHT,
    section_frame,
    set_input_height,
)
from app.widgets.form_controls import make_combo, make_double_spin
from app.widgets.labeled_input import add_labeled_row
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content

SEAL_TYPE_OPTIONS = ["AC", "DBST"]


class CatalogAnalysisPage(QWidget):
    """Catalog / Analysis: inputs lookup one pavement stack + design chart."""

    inputs_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._updating_combos = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        fit_scroll_content(content)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(BLOCK_SPACING)
        content_layout.addWidget(self._build_input_block())
        content_layout.addWidget(self._build_design_block())
        content_layout.addStretch(0)

        scroll.setWidget(content)
        configure_page_scroll(scroll)
        outer.addWidget(scroll, 1)

        self._refresh_dependent_options(initial=True)
        QTimer.singleShot(0, self._refresh_design)

    def connect_inputs_changed(self, callback) -> None:
        self.inputs_changed.connect(callback)

    def quick_results(self) -> dict[str, str]:
        design = self._current_design()
        results = summarize_pavement_design(design)
        results["Subgrade CBR"] = f"{self.subgrade_spin.value():,.2f} %"
        return results

    def get_inputs(self) -> dict[str, float | str]:
        return {
            "seal_type": self.seal_type_combo.currentText(),
            "traffic": self.traffic_combo.currentText(),
            "subgrade_cbr_percent": float(self.subgrade_spin.value()),
            "foundation": self.foundation_combo.currentText(),
            "catalog": self.catalog_combo.currentText(),
        }

    def _current_design(self):
        return lookup_pavement_design(
            seal_type=self.seal_type_combo.currentText(),
            catalog_name=self.catalog_combo.currentText(),
            traffic=self.traffic_combo.currentText(),
            foundation=self.foundation_combo.currentText(),
        )

    def _notify_changed(self, *_args) -> None:
        if self._updating_combos:
            return
        self._refresh_design()
        self.inputs_changed.emit()

    def _build_input_block(self) -> QFrame:
        frame, section_layout = section_frame("Input")

        body = QHBoxLayout()
        body.setSpacing(BLOCK_SPACING)
        body.addWidget(self._build_left_inputs(), 1)
        body.addWidget(self._build_right_selects(), 1)
        section_layout.addLayout(body)
        return frame

    def _build_left_inputs(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("catalogLeftPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        row = 0
        self.seal_type_combo = make_combo(SEAL_TYPE_OPTIONS)
        self.seal_type_combo.setCurrentText("AC")
        set_input_height(self.seal_type_combo)
        self.seal_type_combo.currentTextChanged.connect(self._on_seal_changed)
        add_labeled_row(grid, row, "Seal type =", self.seal_type_combo, ROW_HEIGHT)
        row += 1

        self.traffic_combo = make_combo(["T7"])
        set_input_height(self.traffic_combo)
        self.traffic_combo.currentTextChanged.connect(self._notify_changed)
        add_labeled_row(grid, row, "Traffic =", self.traffic_combo, ROW_HEIGHT)
        row += 1

        self.subgrade_spin = make_double_spin()
        self.subgrade_spin.setRange(0.0, 100.0)
        self.subgrade_spin.setDecimals(2)
        self.subgrade_spin.setSuffix(" %")
        self.subgrade_spin.setValue(5.0)
        self.subgrade_spin.setToolTip("Subgrade CBR (%) — suggests Foundation class")
        set_input_height(self.subgrade_spin)
        self.subgrade_spin.valueChanged.connect(self._on_subgrade_changed)
        add_labeled_row(grid, row, "Subgrade CBR =", self.subgrade_spin, ROW_HEIGHT)

        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        layout.addStretch()
        return panel

    def _build_right_selects(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("catalogRightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        row = 0
        self.foundation_combo = make_combo(list(FOUNDATION_OPTIONS))
        set_input_height(self.foundation_combo)
        self.foundation_combo.currentTextChanged.connect(self._on_foundation_manual)
        add_labeled_row(grid, row, "Foundation (Select 1) =", self.foundation_combo, ROW_HEIGHT)
        row += 1

        self.catalog_combo = make_combo(["-"])
        set_input_height(self.catalog_combo)
        self.catalog_combo.currentTextChanged.connect(self._on_catalog_changed)
        add_labeled_row(grid, row, "Catalog (Select 2) =", self.catalog_combo, ROW_HEIGHT)

        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)

        hint = QLabel("Select 1 = foundation class · Select 2 = catalog structure family")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(hint)
        layout.addStretch()
        return panel

    def _build_design_block(self) -> QFrame:
        frame, section_layout = section_frame("Design")

        self.design_chart = MatplotlibChartWidget(figsize=(7.2, 5.4))
        self.design_chart.setMinimumHeight(360)
        self.design_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        section_layout.addWidget(self.design_chart)
        return frame

    def _set_combo_items(self, combo, items: list[str], preferred: str | None = None) -> None:
        current = preferred if preferred in items else (combo.currentText() if combo.currentText() in items else None)
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        if current:
            combo.setCurrentText(current)
        elif items:
            combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def _refresh_dependent_options(self, *, initial: bool = False) -> None:
        self._updating_combos = True
        try:
            seal = self.seal_type_combo.currentText()
            catalogs = list(CATALOG_OPTIONS_BY_SEAL.get(seal, ()))
            preferred_catalog = None
            if initial and seal == "AC":
                preferred_catalog = CATALOG_OPTIONS_BY_SEAL["AC"][0]
            self._set_combo_items(self.catalog_combo, catalogs, preferred_catalog)

            traffic_items = list(available_traffic_classes(self.catalog_combo.currentText()))
            preferred_traffic = "T7" if "T7" in traffic_items else None
            self._set_combo_items(self.traffic_combo, traffic_items, preferred_traffic)

            if initial:
                suggested = foundation_from_cbr(float(self.subgrade_spin.value()))
                self.foundation_combo.blockSignals(True)
                self.foundation_combo.setCurrentText(suggested)
                self.foundation_combo.blockSignals(False)
        finally:
            self._updating_combos = False

    def _on_seal_changed(self, *_args) -> None:
        self._refresh_dependent_options()
        self._notify_changed()

    def _on_catalog_changed(self, *_args) -> None:
        if self._updating_combos:
            return
        self._updating_combos = True
        try:
            traffic_items = list(available_traffic_classes(self.catalog_combo.currentText()))
            self._set_combo_items(self.traffic_combo, traffic_items)
        finally:
            self._updating_combos = False
        self._notify_changed()

    def _on_subgrade_changed(self, *_args) -> None:
        suggested = foundation_from_cbr(float(self.subgrade_spin.value()))
        self._updating_combos = True
        try:
            self.foundation_combo.blockSignals(True)
            self.foundation_combo.setCurrentText(suggested)
            self.foundation_combo.blockSignals(False)
        finally:
            self._updating_combos = False
        self._notify_changed()

    def _on_foundation_manual(self, *_args) -> None:
        self._notify_changed()

    def _refresh_design(self) -> None:
        design = self._current_design()

        if self.design_chart.figure is None:
            return

        tokens = theme_tokens()
        self.design_chart.figure.clear()
        self.design_chart.figure.patch.set_facecolor(tokens.bg_window)
        ax = self.design_chart.add_subplot(111)
        draw_pavement_catalog_section(ax, design)
        self.design_chart.figure.subplots_adjust(bottom=0.30, left=0.06, right=0.98, top=0.96)
        self.design_chart.redraw()
