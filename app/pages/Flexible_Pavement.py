"""Pavement and Material Design > Flexible Pavement."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QShowEvent
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import SegmentedWidget

from app.core.ui_scale import UiScale
from app.core.theme import theme_tokens
from app.core.ui_style import section_title_style, title_style
from app.data.aashto_resilient_modulus import MONTH_LABELS, compute_effective_resilient_modulus
from app.layouts import BasePage, define_page
from app.widgets.button import secondary_button
from app.widgets.form_controls import make_double_spin
from app.widgets.labeled_input import add_labeled_row
from app.widgets.scroll_utils import configure_hidden_scrollbars

ROW_HEIGHT = 36
BLOCK_SPACING = 24
SECTION_TITLE_STYLE = section_title_style(18)
MODULUS_TABLE_FONT_SIZE = 10
MODULUS_TABLE_ROW_HEIGHT = 40
MODULUS_LABEL_COLUMN_WIDTH = 100
MODULUS_SUMMARY_FONT_SIZE = 13

TAB_CATALOG = 0
TAB_AASHTO = 1


def _set_input_height(widget) -> None:
    widget.setMinimumHeight(ROW_HEIGHT)
    widget.setMaximumHeight(ROW_HEIGHT)


def _modulus_table_font() -> QFont:
    font = QFont()
    font.setPointSizeF(UiScale.pt(MODULUS_TABLE_FONT_SIZE))
    return font


def _modulus_table_item(text: str = "") -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFont(_modulus_table_font())
    return item


def _modulus_row_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    font_pt = UiScale.pt(MODULUS_TABLE_FONT_SIZE)
    label.setStyleSheet(
        f"color: #cccccc; font-size: {font_pt}pt; padding: 2px 4px; font-weight: 500;"
    )
    label.setFont(_modulus_table_font())
    return label


def _apply_modulus_row_heights(table: QTableWidget) -> None:
    row_height = UiScale.px(MODULUS_TABLE_ROW_HEIGHT)
    table.verticalHeader().setDefaultSectionSize(row_height)
    for row_index in range(table.rowCount()):
        table.setRowHeight(row_index, row_height)


def _fit_modulus_table_height(table: QTableWidget) -> None:
    """Size the modulus table to fit its rows without extra empty space."""
    _apply_modulus_row_heights(table)
    header_height = table.horizontalHeader().height() or UiScale.px(34)
    row_height = UiScale.px(MODULUS_TABLE_ROW_HEIGHT)
    total_height = header_height + max(table.rowCount(), 1) * row_height + UiScale.px(2)
    table.setFixedHeight(total_height)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def _modulus_summary_html(
    average_uf: float | None,
    effective_mr_psi: float | None,
) -> str:
    accent = theme_tokens().accent
    font_pt = UiScale.pt(MODULUS_SUMMARY_FONT_SIZE)
    avg_value = f"{average_uf:.3f}" if average_uf is not None else "—"
    mr_value = f"{effective_mr_psi:.0f} psi" if effective_mr_psi is not None else "— psi"
    value_style = f"color: {accent}; font-weight: 700;"
    return (
        f"<ul style=\"margin: 0; padding-left: 18px; color: #cccccc; font-size: {font_pt}pt;\">"
        f"<li style=\"margin: 4px 0;\">Average relative damage uf = "
        f"<span style=\"{value_style}\">{avg_value}</span></li>"
        f"<li style=\"margin: 4px 0;\">Effective roadbed soil resilient modulus MR = "
        f"<span style=\"{value_style}\">{mr_value}</span></li>"
        f"</ul>"
    )


def _set_modulus_spin_height(widget) -> None:
    spin_height = max(UiScale.px(MODULUS_TABLE_ROW_HEIGHT) - 10, UiScale.px(36))
    widget.setMinimumHeight(spin_height)
    widget.setMaximumHeight(spin_height)


def _configure_modulus_table(table: QTableWidget) -> None:
    table.verticalHeader().setVisible(False)
    table.setWordWrap(True)
    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    font_pt = UiScale.pt(MODULUS_TABLE_FONT_SIZE)
    table.setStyleSheet(
        f"""
        QTableWidget {{
            font-size: {font_pt}pt;
        }}
        QTableWidget::item {{
            font-size: {font_pt}pt;
            padding: 6px 4px;
        }}
        QHeaderView::section {{
            font-size: {font_pt}pt;
            padding: 8px 4px;
        }}
        """
    )
    _apply_modulus_row_heights(table)


def _section_frame(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("flexPavementSectionFrame")
    frame.setStyleSheet(
        "#flexPavementSectionFrame { background-color: transparent; border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    section_layout = QVBoxLayout(frame)
    section_layout.setContentsMargins(16, 12, 16, 16)
    section_layout.setSpacing(12)

    title_label = QLabel(title)
    title_label.setStyleSheet(SECTION_TITLE_STYLE)
    section_layout.addWidget(title_label)
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return frame, section_layout


def _layer_band(text: str, color: str, *, min_height: int = 44) -> QLabel:
    band = QLabel(text)
    band.setAlignment(Qt.AlignmentFlag.AlignCenter)
    band.setMinimumHeight(min_height)
    band.setStyleSheet(
        f"background-color: {color}; color: #111111; font-weight: 600; "
        "border: 1px solid #555555; border-radius: 2px; padding: 4px;"
    )
    return band


def _thickness_marker(label: str) -> QLabel:
    marker = QLabel(label)
    marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
    marker.setStyleSheet("color: #cccccc; font-size: 13px; font-weight: 600; padding: 4px;")
    marker.setMinimumWidth(36)
    return marker


class CatalogAnalysisTabPage(QWidget):
    """Catalog / Analysis tab placeholder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        frame, section_layout = _section_frame("Catalog / Analysis")
        message = QLabel("Catalog and analysis tools will be added here.")
        message.setStyleSheet("color: #888888; font-size: 14px; padding: 24px;")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        section_layout.addWidget(message)
        layout.addWidget(frame)


class AashtoTabPage(QWidget):
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
        configure_hidden_scrollbars(scroll)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(BLOCK_SPACING)
        content_layout.addWidget(self._build_input_block())
        content_layout.addWidget(self._build_modulus_block(), 1)

        scroll.setWidget(content)
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
        frame, section_layout = _section_frame("1. Given Parameters")

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
        _set_input_height(self.esal_spin)
        add_labeled_row(grid, row, "Total traffic, ESAL (80kN) =", self.esal_spin, ROW_HEIGHT)
        row += 1

        self.pt_spin = make_double_spin()
        self.pt_spin.setRange(0.0, 5.0)
        self.pt_spin.setDecimals(2)
        self.pt_spin.setValue(2.5)
        _set_input_height(self.pt_spin)
        add_labeled_row(grid, row, "Terminal serviceability Pt =", self.pt_spin, ROW_HEIGHT)
        row += 1

        self.p0_spin = make_double_spin()
        self.p0_spin.setRange(0.0, 5.0)
        self.p0_spin.setDecimals(2)
        self.p0_spin.setValue(4.4)
        _set_input_height(self.p0_spin)
        add_labeled_row(grid, row, "Initial serviceability P0 =", self.p0_spin, ROW_HEIGHT)
        row += 1

        self.s0_spin = make_double_spin()
        self.s0_spin.setRange(0.0, 2.0)
        self.s0_spin.setDecimals(2)
        self.s0_spin.setValue(0.45)
        _set_input_height(self.s0_spin)
        add_labeled_row(grid, row, "Standard deviation S0 =", self.s0_spin, ROW_HEIGHT)
        row += 1

        self.r0_spin = make_double_spin()
        self.r0_spin.setRange(0.0, 100.0)
        self.r0_spin.setDecimals(0)
        self.r0_spin.setValue(75.0)
        _set_input_height(self.r0_spin)
        add_labeled_row(grid, row, "Reliability design R0 =", self.r0_spin, ROW_HEIGHT)
        row += 1

        self.h4_spin = make_double_spin()
        self.h4_spin.setRange(0.0, 500.0)
        self.h4_spin.setDecimals(0)
        self.h4_spin.setSuffix(" cm")
        self.h4_spin.setValue(0.0)
        _set_input_height(self.h4_spin)
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

        row_layout.addWidget(_layer_band(layer_name, band_color), 2)

        param_row = QHBoxLayout()
        param_row.setSpacing(6)
        param_row.addWidget(spin, 1)
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #cccccc; font-size: 13px;")
            param_row.addWidget(unit_label)
        row_layout.addLayout(param_row, 2)

        row_layout.addWidget(_thickness_marker(thickness_label), 0)
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
        _set_input_height(self.e1_spin)

        self.e2_spin = make_double_spin()
        self.e2_spin.setRange(1.0, 50_000.0)
        self.e2_spin.setDecimals(0)
        self.e2_spin.setValue(350.0)
        _set_input_height(self.e2_spin)

        self.e3_spin = make_double_spin()
        self.e3_spin.setRange(1.0, 50_000.0)
        self.e3_spin.setDecimals(0)
        self.e3_spin.setValue(200.0)
        _set_input_height(self.e3_spin)

        self.subgrade_cbr_spin = make_double_spin()
        self.subgrade_cbr_spin.setRange(0.0, 100.0)
        self.subgrade_cbr_spin.setDecimals(2)
        self.subgrade_cbr_spin.setSuffix(" %")
        _set_input_height(self.subgrade_cbr_spin)

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
        frame, section_layout = _section_frame("2. Effective Roadbed Soil Resilient Modulus")

        self.modulus_table = QTableWidget(4, len(MONTH_LABELS) + 1)
        self.modulus_table.setHorizontalHeaderLabels(["Month", *MONTH_LABELS])
        self.modulus_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.modulus_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.modulus_table.setAlternatingRowColors(True)
        _configure_modulus_table(self.modulus_table)

        row_labels = ["CBR(%)", "CBR_eff(%)", "MR (psi)", "uf"]
        self._monthly_cbr_spins: list = []

        for row_index, row_label in enumerate(row_labels):
            self.modulus_table.setCellWidget(row_index, 0, _modulus_row_label(row_label))

            for col_index in range(len(MONTH_LABELS)):
                if row_index == 0:
                    spin = make_double_spin()
                    spin.setRange(0.0, 100.0)
                    spin.setDecimals(2)
                    spin.setValue(4.0)
                    _set_modulus_spin_height(spin)
                    spin.valueChanged.connect(self._refresh_modulus_table)
                    self._monthly_cbr_spins.append(spin)
                    self.modulus_table.setCellWidget(row_index, col_index + 1, spin)
                else:
                    self.modulus_table.setItem(row_index, col_index + 1, _modulus_table_item("—"))

        self.modulus_table.setColumnWidth(0, UiScale.px(MODULUS_LABEL_COLUMN_WIDTH))
        header = self.modulus_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        for col_index in range(1, self.modulus_table.columnCount()):
            header.setSectionResizeMode(col_index, QHeaderView.ResizeMode.Stretch)
        _fit_modulus_table_height(self.modulus_table)
        section_layout.addWidget(self.modulus_table)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        self.summary_label.setText(_modulus_summary_html(None, None))
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
                    item = _modulus_table_item()
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    self.modulus_table.setItem(row_index, col_index + 1, item)
                item.setText(text)

        _fit_modulus_table_height(self.modulus_table)
        self.summary_label.setText(
            _modulus_summary_html(result.average_relative_damage, result.effective_mr_psi)
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


@define_page("blank", title="Flexible Pavement")
class FlexiblePavementPage(BasePage):
    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._page_title = QLabel("Flexible Pavement")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        content.addLayout(title_row)

        self.segmented = SegmentedWidget(self)
        self.segmented.setObjectName("flexiblePavementSegmented")
        self.stack = QStackedWidget(self)
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.catalog_page = CatalogAnalysisTabPage()
        self.aashto_page = AashtoTabPage()

        tabs = [
            ("catalog_analysis", "Catalog/Analysis", self.catalog_page),
            ("aashto", "AASHTO", self.aashto_page),
        ]

        for index, (route_key, text, page) in enumerate(tabs):
            self.segmented.addItem(
                route_key,
                text,
                onClick=lambda _=None, tab_index=index: self._set_tab(tab_index),
            )
            self.stack.addWidget(page)

        self.segmented.setCurrentItem("catalog_analysis")
        self.stack.setCurrentIndex(0)

        content.addWidget(self.segmented)
        content.addWidget(self.stack, 1)

        self.aashto_page.connect_inputs_changed(self._push_quick_results)
        self._push_quick_results()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def activate_page(self) -> None:
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def _set_tab(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self._setup_quick_panel()

    def _results(self) -> dict[str, str]:
        if self.stack.currentIndex() == TAB_AASHTO:
            return self.aashto_page.quick_results()
        return {}

    def _setup_quick_panel(self) -> None:
        mw = self.window()
        if not hasattr(mw, "quick_panel"):
            return
        if hasattr(mw.quick_panel, "set_flexible_pavement_schema"):
            mw.quick_panel.set_flexible_pavement_schema()
        mw.quick_panel.set_results(self._results())

    def _push_quick_results(self) -> None:
        self._setup_quick_panel()

    def _toggle_quick_panel(self) -> None:
        mw = self.window()
        if hasattr(mw, "toggle_quick_panel"):
            self.sync_quick_panel_button(mw.toggle_quick_panel())

    def sync_quick_panel_button(self, visible: bool | None = None) -> None:
        if visible is None:
            mw = self.window()
            visible = hasattr(mw, "is_quick_panel_visible") and mw.is_quick_panel_visible()
        self.quick_panel_btn.setText("Hide Quick Result" if visible else "Show Quick Result")

    def _sync_quick_panel_button(self) -> None:
        self.sync_quick_panel_button()
