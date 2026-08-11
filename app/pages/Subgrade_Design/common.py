"""Shared helpers for Subgrade Design pages (DCP / CBR / FWD)."""
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
    QWidget,
)

from app.core.ui_scale import UiScale
from app.core.ui_style import section_title_style

BLOCK_SPACING = 24
SECTION_TITLE_STYLE = section_title_style(18)
ROW_HEIGHT = 36
TABLE_FONT_SIZE = 10
TABLE_ROW_HEIGHT = 38
CHART_MIN_HEIGHT = 340

TAB_DCP = 0
TAB_CBR_EQUIVALENT = 1
TAB_FWD = 2  # FWD/BB


def format_number(value: float | None, *, decimals: int = 2) -> str:
    if value is None:
        return "—"
    if decimals == 0:
        return f"{int(round(value))}"
    return f"{value:.{decimals}f}"


def section_frame(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("subgradeSectionFrame")
    frame.setStyleSheet(
        "#subgradeSectionFrame { background-color: transparent; border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    section_layout = QVBoxLayout(frame)
    section_layout.setContentsMargins(16, 12, 16, 16)
    section_layout.setSpacing(12)

    title_label = QLabel(title)
    title_label.setStyleSheet(SECTION_TITLE_STYLE)
    section_layout.addWidget(title_label)
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return frame, section_layout


def subgrade_table_font() -> QFont:
    font = QFont()
    font.setPointSizeF(UiScale.pt(TABLE_FONT_SIZE))
    return font


def subgrade_table_item(text: str = "") -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFont(subgrade_table_font())
    return item


def style_subgrade_table_item(item: QTableWidgetItem) -> None:
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    item.setFont(subgrade_table_font())


def apply_subgrade_row_heights(table: QTableWidget) -> None:
    row_height = UiScale.px(TABLE_ROW_HEIGHT)
    table.verticalHeader().setDefaultSectionSize(row_height)
    for row_index in range(table.rowCount()):
        table.setRowHeight(row_index, row_height)


def configure_subgrade_table(table: QTableWidget) -> None:
    """Hide row numbers, stretch columns, center data, and style table cells."""
    table.verticalHeader().setVisible(False)
    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    font_pt = UiScale.pt(TABLE_FONT_SIZE)
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
    apply_subgrade_row_heights(table)

    footer_row = table.footer_row_index() if hasattr(table, "footer_row_index") else None
    data_rows = table.data_row_count() if hasattr(table, "data_row_count") else table.rowCount()

    table.blockSignals(True)
    try:
        for row_index in range(data_rows):
            for col_index in range(table.columnCount()):
                item = table.item(row_index, col_index)
                if item is None:
                    table.setItem(row_index, col_index, subgrade_table_item())
                else:
                    style_subgrade_table_item(item)
    finally:
        table.blockSignals(False)

    if footer_row is not None and hasattr(table, "_refresh_footer_row"):
        table._refresh_footer_row()

    if table.editTriggers() != QTableWidget.EditTrigger.NoEditTriggers:
        def _on_item_changed(changed: QTableWidgetItem) -> None:
            if footer_row is not None and changed.row() == footer_row:
                return
            style_subgrade_table_item(changed)

        table.itemChanged.connect(_on_item_changed)


def expand_vertical(widget: QWidget) -> QWidget:
    """Let a widget grow with available page height."""
    policy = widget.sizePolicy()
    widget.setSizePolicy(policy.horizontalPolicy(), QSizePolicy.Policy.Expanding)
    return widget
