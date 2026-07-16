"""Flexible Pavement > AASHTO page."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.ui_scale import UiScale
from app.data.aashto_resilient_modulus import MONTH_LABELS, compute_effective_resilient_modulus
from app.pages.Flexible_Pavement.common import (
    BLOCK_SPACING,
    MODULUS_LABEL_COLUMN_WIDTH,
    ROW_HEIGHT,
    configure_modulus_table,
    fit_modulus_table_height,
    layer_band,
    modulus_row_label,
    modulus_summary_html,
    modulus_table_item,
    section_frame,
    set_input_height,
    set_modulus_spin_height,
    thickness_marker,
)
from app.widgets.form_controls import make_double_spin
from app.widgets.labeled_input import add_labeled_row
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content


class AashtoPage(QWidget):
    """AASHTO flexible pavement design inputs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._on_changed = None
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
        content_layout.addWidget(self._build_modulus_block())

        scroll.setWidget(content)
        configure_page_scroll(scroll)
        outer.addWidget(scroll, 1)

        self._refresh_modulus_table()

    def connect_inputs_changed(self, callback) -> None:
        self._on_changed = callback
        for spin in self._all_input_spins():
            spin.valueChanged.connect(self._notify_changed)

    def _notify_changed(self, *_args) -> None:
        if self._on_changed is not None:
            self._on_changed()

    def _all_input_spins(self) -> list:
        spins = [
            self.esal_spin,
            self.pt_spin,
            self.p0_spin,
            self.s0_spin,
            self.r0_spin,
            self.h4_spin,
            self.e1_spin,
            self.e2_spin,
            self.e3_spin,
            self.subgrade_cbr_spin,
        ]
        spins.extend(self._monthly_cbr_spins)
        return spins

    def quick_results(self) -> dict[str, str]:
        modulus = compute_effective_resilient_modulus(self._monthly_cbr_values())
        results = {
            "ESAL": f"{self.esal_spin.value():,.4f} million",
            "Initial serviceability P0": f"{self.p0_spin.value():,.2f}",
            "Terminal serviceability Pt": f"{self.pt_spin.value():,.2f}",
            "Reliability R0": f"{self.r0_spin.value():,.0f}",
        }
        if modulus.effective_mr_psi is not None:
            results["Effective MR"] = f"{modulus.effective_mr_psi:,.0f} psi"
        if modulus.average_relative_damage is not None:
            results["Average uf"] = f"{modulus.average_relative_damage:,.3f}"
        return results

    def _build_input_block(self) -> QFrame:
        frame, section_layout = section_frame("1. Given Parameters")

        body = QHBoxLayout()
        body.setSpacing(BLOCK_SPACING)

        body.addWidget(self._build_given_parameters_panel(), 1)
        body.addWidget(self._build_layer_parameters_panel(), 1)

        section_layout.addLayout(body)
        return frame

    def _build_given_parameters_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("aashtoGivenPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        row = 0

        self.esal_spin = make_double_spin()
        self.esal_spin.setRange(0.0, 999.9999)
        self.esal_spin.setDecimals(4)
        self.esal_spin.setValue(3.8834)
        self.esal_spin.setSuffix(" million")
        set_input_height(self.esal_spin)
        add_labeled_row(grid, row, "Total traffic, ESAL (80kN) =", self.esal_spin, ROW_HEIGHT)
        row += 1

        self.pt_spin = make_double_spin()
        self.pt_spin.setRange(0.0, 5.0)
        self.pt_spin.setDecimals(2)
        self.pt_spin.setValue(2.5)
        set_input_height(self.pt_spin)
        add_labeled_row(grid, row, "Terminal serviceability Pt =", self.pt_spin, ROW_HEIGHT)
        row += 1

        self.p0_spin = make_double_spin()
        self.p0_spin.setRange(0.0, 5.0)
        self.p0_spin.setDecimals(2)
        self.p0_spin.setValue(4.4)
        set_input_height(self.p0_spin)
        add_labeled_row(grid, row, "Initial serviceability P0 =", self.p0_spin, ROW_HEIGHT)
        row += 1

        self.s0_spin = make_double_spin()
        self.s0_spin.setRange(0.0, 2.0)
        self.s0_spin.setDecimals(2)
        self.s0_spin.setValue(0.45)
        set_input_height(self.s0_spin)
        add_labeled_row(grid, row, "Standard deviation S0 =", self.s0_spin, ROW_HEIGHT)
        row += 1

        self.r0_spin = make_double_spin()
        self.r0_spin.setRange(0.0, 100.0)
        self.r0_spin.setDecimals(0)
        self.r0_spin.setValue(75.0)
        set_input_height(self.r0_spin)
        add_labeled_row(grid, row, "Reliability design R0 =", self.r0_spin, ROW_HEIGHT)
        row += 1

        self.h4_spin = make_double_spin()
        self.h4_spin.setRange(0.0, 500.0)
        self.h4_spin.setDecimals(0)
        self.h4_spin.setSuffix(" cm")
        self.h4_spin.setValue(0.0)
        set_input_height(self.h4_spin)
        add_labeled_row(grid, row, "Th. of selected subgrade h4 =", self.h4_spin, ROW_HEIGHT)

        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        layout.addStretch()
        return panel

    def _build_layer_row(
        self,
        layer_name: str,
        band_color: str,
        spin,
        unit: str,
        thickness_label: str,
    ) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        row_layout.addWidget(layer_band(layer_name, band_color), 2)

        param_row = QHBoxLayout()
        param_row.setSpacing(6)
        param_row.addWidget(spin, 1)
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #cccccc; font-size: 13px;")
            param_row.addWidget(unit_label)
        row_layout.addLayout(param_row, 2)

        row_layout.addWidget(thickness_marker(thickness_label), 0)
        return row_widget

    def _build_layer_parameters_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("aashtoLayerPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.e1_spin = make_double_spin()
        self.e1_spin.setRange(1.0, 50_000.0)
        self.e1_spin.setDecimals(0)
        self.e1_spin.setValue(1400.0)
        set_input_height(self.e1_spin)

        self.e2_spin = make_double_spin()
        self.e2_spin.setRange(1.0, 50_000.0)
        self.e2_spin.setDecimals(0)
        self.e2_spin.setValue(350.0)
        set_input_height(self.e2_spin)

        self.e3_spin = make_double_spin()
        self.e3_spin.setRange(1.0, 50_000.0)
        self.e3_spin.setDecimals(0)
        self.e3_spin.setValue(200.0)
        set_input_height(self.e3_spin)

        self.subgrade_cbr_spin = make_double_spin()
        self.subgrade_cbr_spin.setRange(0.0, 100.0)
        self.subgrade_cbr_spin.setDecimals(2)
        self.subgrade_cbr_spin.setSuffix(" %")
        set_input_height(self.subgrade_cbr_spin)

        e1_wrap = QWidget()
        e1_layout = QHBoxLayout(e1_wrap)
        e1_layout.setContentsMargins(0, 0, 0, 0)
        e1_layout.setSpacing(6)
        e1_label = QLabel("E1 =")
        e1_label.setStyleSheet("color: #cccccc; font-weight: 600;")
        e1_layout.addWidget(e1_label)
        e1_layout.addWidget(self.e1_spin, 1)
        e1_layout.addWidget(QLabel("MPa"))

        e2_wrap = QWidget()
        e2_layout = QHBoxLayout(e2_wrap)
        e2_layout.setContentsMargins(0, 0, 0, 0)
        e2_layout.setSpacing(6)
        e2_label = QLabel("E2 =")
        e2_label.setStyleSheet("color: #cccccc; font-weight: 600;")
        e2_layout.addWidget(e2_label)
        e2_layout.addWidget(self.e2_spin, 1)
        e2_layout.addWidget(QLabel("MPa"))

        e3_wrap = QWidget()
        e3_layout = QHBoxLayout(e3_wrap)
        e3_layout.setContentsMargins(0, 0, 0, 0)
        e3_layout.setSpacing(6)
        e3_label = QLabel("E3 =")
        e3_label.setStyleSheet("color: #cccccc; font-weight: 600;")
        e3_layout.addWidget(e3_label)
        e3_layout.addWidget(self.e3_spin, 1)
        e3_layout.addWidget(QLabel("MPa"))

        cbr_wrap = QWidget()
        cbr_layout = QHBoxLayout(cbr_wrap)
        cbr_layout.setContentsMargins(0, 0, 0, 0)
        cbr_layout.setSpacing(6)
        cbr_label = QLabel("CBR =")
        cbr_label.setStyleSheet("color: #cccccc; font-weight: 600;")
        cbr_layout.addWidget(cbr_label)
        cbr_layout.addWidget(self.subgrade_cbr_spin, 1)

        layout.addWidget(self._build_layer_row("HMA", "#5b8fd8", e1_wrap, "", "h₁"))
        layout.addWidget(self._build_layer_row("Granular base", "#6fbf6f", e2_wrap, "", "h₂"))
        layout.addWidget(self._build_layer_row("Subbase", "#b58a52", e3_wrap, "", "h₃"))
        layout.addWidget(self._build_layer_row("Selected subgrade", "#d9c4a0", cbr_wrap, "", "h₄"))
        layout.addStretch()
        return panel

    def _build_modulus_block(self) -> QFrame:
        frame, section_layout = section_frame("2. Effective Roadbed Soil Resilient Modulus")

        self.modulus_table = QTableWidget(4, len(MONTH_LABELS) + 1)
        self.modulus_table.setHorizontalHeaderLabels(["Month", *MONTH_LABELS])
        self.modulus_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.modulus_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.modulus_table.setAlternatingRowColors(True)
        configure_modulus_table(self.modulus_table)

        row_labels = ["CBR(%)", "CBR_eff(%)", "MR (psi)", "uf"]
        self._monthly_cbr_spins: list = []

        for row_index, row_label in enumerate(row_labels):
            self.modulus_table.setCellWidget(row_index, 0, modulus_row_label(row_label))

            for col_index in range(len(MONTH_LABELS)):
                if row_index == 0:
                    spin = make_double_spin()
                    spin.setRange(0.0, 100.0)
                    spin.setDecimals(2)
                    spin.setValue(4.0)
                    set_modulus_spin_height(spin)
                    spin.valueChanged.connect(self._refresh_modulus_table)
                    self._monthly_cbr_spins.append(spin)
                    self.modulus_table.setCellWidget(row_index, col_index + 1, spin)
                else:
                    self.modulus_table.setItem(row_index, col_index + 1, modulus_table_item("—"))

        self.modulus_table.setColumnWidth(0, UiScale.px(MODULUS_LABEL_COLUMN_WIDTH))
        header = self.modulus_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        for col_index in range(1, self.modulus_table.columnCount()):
            header.setSectionResizeMode(col_index, QHeaderView.ResizeMode.Stretch)
        fit_modulus_table_height(self.modulus_table)
        section_layout.addWidget(self.modulus_table)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        self.summary_label.setText(modulus_summary_html(None, None))
        section_layout.addWidget(self.summary_label)

        return frame

    def _monthly_cbr_values(self) -> list[float]:
        return [float(spin.value()) for spin in self._monthly_cbr_spins]

    def _refresh_modulus_table(self) -> None:
        if not hasattr(self, "modulus_table"):
            return

        result = compute_effective_resilient_modulus(self._monthly_cbr_values())

        for col_index, month_result in enumerate(result.months):
            values = [
                None,
                f"{month_result.cbr_effective_percent:.0f}",
                f"{month_result.mr_psi:.0f}",
                f"{month_result.relative_damage:.5f}" if month_result.relative_damage is not None else "—",
            ]
            for row_index, text in enumerate(values, start=1):
                item = self.modulus_table.item(row_index, col_index + 1)
                if item is None:
                    item = modulus_table_item()
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    self.modulus_table.setItem(row_index, col_index + 1, item)
                item.setText(text)

        fit_modulus_table_height(self.modulus_table)
        self.summary_label.setText(
            modulus_summary_html(result.average_relative_damage, result.effective_mr_psi)
        )

        self._notify_changed()

    def get_inputs(self) -> dict[str, float]:
        return {
            "esal_million": float(self.esal_spin.value()),
            "pt": float(self.pt_spin.value()),
            "p0": float(self.p0_spin.value()),
            "s0": float(self.s0_spin.value()),
            "r0": float(self.r0_spin.value()),
            "h4_cm": float(self.h4_spin.value()),
            "e1_mpa": float(self.e1_spin.value()),
            "e2_mpa": float(self.e2_spin.value()),
            "e3_mpa": float(self.e3_spin.value()),
            "subgrade_cbr_percent": float(self.subgrade_cbr_spin.value()),
        }
