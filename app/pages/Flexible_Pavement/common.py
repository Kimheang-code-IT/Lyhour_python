"""Shared helpers for Flexible Pavement pages (Catalog / AASHTO)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.core.theme import theme_tokens
from app.core.ui_scale import UiScale
from app.core.ui_style import section_title_style

ROW_HEIGHT = 36
BLOCK_SPACING = 24
SECTION_TITLE_STYLE = section_title_style(18)
MODULUS_TABLE_FONT_SIZE = 10
MODULUS_TABLE_ROW_HEIGHT = 40
MODULUS_LABEL_COLUMN_WIDTH = 100
MODULUS_SUMMARY_FONT_SIZE = 13

TAB_CATALOG = 0
TAB_AASHTO = 1
TAB_MPWT = 2


def set_input_height(widget) -> None:
    widget.setMinimumHeight(ROW_HEIGHT)
    widget.setMaximumHeight(ROW_HEIGHT)


def modulus_table_font() -> QFont:
    font = QFont()
    font.setPointSizeF(UiScale.pt(MODULUS_TABLE_FONT_SIZE))
    return font


def modulus_table_item(text: str = "") -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFont(modulus_table_font())
    return item


def modulus_row_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    font_pt = UiScale.pt(MODULUS_TABLE_FONT_SIZE)
    label.setStyleSheet(
        f"color: #cccccc; font-size: {font_pt}pt; padding: 2px 4px; font-weight: 500;"
    )
    label.setFont(modulus_table_font())
    return label


def apply_modulus_row_heights(table: QTableWidget) -> None:
    row_height = UiScale.px(MODULUS_TABLE_ROW_HEIGHT)
    table.verticalHeader().setDefaultSectionSize(row_height)
    for row_index in range(table.rowCount()):
        table.setRowHeight(row_index, row_height)


def fit_modulus_table_height(table: QTableWidget) -> None:
    """Size the modulus table to fit its rows without extra empty space."""
    apply_modulus_row_heights(table)
    header_height = table.horizontalHeader().height() or UiScale.px(34)
    row_height = UiScale.px(MODULUS_TABLE_ROW_HEIGHT)
    total_height = header_height + max(table.rowCount(), 1) * row_height + UiScale.px(2)
    table.setFixedHeight(total_height)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def modulus_summary_html(
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


def set_modulus_spin_height(widget) -> None:
    spin_height = max(UiScale.px(MODULUS_TABLE_ROW_HEIGHT) - 10, UiScale.px(36))
    widget.setMinimumHeight(spin_height)
    widget.setMaximumHeight(spin_height)


def configure_modulus_table(table: QTableWidget) -> None:
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
    apply_modulus_row_heights(table)


def section_frame(title: str) -> tuple[QFrame, QVBoxLayout]:
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


def layer_band(text: str, color: str, *, min_height: int = 44) -> QLabel:
    band = QLabel(text)
    band.setAlignment(Qt.AlignmentFlag.AlignCenter)
    band.setMinimumHeight(min_height)
    band.setStyleSheet(
        f"background-color: {color}; color: #111111; font-weight: 600; "
        "border: 1px solid #555555; border-radius: 2px; padding: 4px;"
    )
    return band


def thickness_marker(label: str) -> QLabel:
    marker = QLabel(label)
    marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
    marker.setStyleSheet("color: #cccccc; font-size: 13px; font-weight: 600; padding: 4px;")
    marker.setMinimumWidth(36)
    return marker
