"""Subgrade Design > CBR Equivalent page."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.theme import theme_tokens
from app.core.ui_scale import UiScale
from app.data.cbr_equivalent import (
    build_dcp_cbr_display_rows,
    compute_cbr_equivalent,
    compute_cbr_equivalent_from_user_layers,
    format_cbr_equivalent_result,
    summarize_cbr_equivalent,
)
from app.data.dcp_analysis import analyze_dcp_rows
from app.pages.Subgrade_Design.common import (
    BLOCK_SPACING,
    apply_subgrade_row_heights,
    configure_subgrade_table,
    expand_vertical,
    format_number,
    section_frame,
    subgrade_table_item,
)
from app.widgets.excel_paste_table import ExcelPasteTable
from app.widgets.form_controls import make_radio
from app.widgets.scroll_utils import configure_page_scroll

if TYPE_CHECKING:
    from app.pages.Subgrade_Design.dcp import DcpPage

MODE_DCP = 0
MODE_USER = 1

DCP_TABLE_HEADERS = [
    "Depth (mm)",
    "Thickness (mm)",
    "Total Blows",
    "Penetration Rate (mm/blow)",
    "Layered-CBR (%)",
    "Evaluation",
]

USER_TABLE_HEADERS = ["CBR (%)", "Hi (mm)"]

REFERENCE_IMAGE_NAME = "image.png"
_PAIR_MIN_HEIGHT = 180


def _assets_image_path(filename: str) -> Path:
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        base = Path(sys._MEIPASS) / "app"
    else:
        base = Path(__file__).resolve().parents[2]
    return base / "assets" / "image" / filename


class ReferenceImageLabel(QLabel):
    """Scales the layered CBR/h reference diagram while keeping aspect ratio."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._source = QPixmap()
        path = _assets_image_path(REFERENCE_IMAGE_NAME)
        if path.is_file():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self._source = pixmap

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(180)
        self.setMaximumWidth(280)
        self.setMinimumHeight(_PAIR_MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #3e3e40; border-radius: 6px; padding: 6px;"
        )
        self._refresh_pixmap()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self) -> None:
        if self._source.isNull():
            self.setText("Reference diagram\nnot found")
            self.setStyleSheet(
                "color: #888888; background-color: transparent; "
                "border: 1px dashed #555555; border-radius: 6px; padding: 12px;"
            )
            return
        margin = 10
        target_w = max(1, self.width() - margin * 2)
        target_h = max(1, self.height() - margin * 2)
        self.setPixmap(
            self._source.scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class CbrPage(QWidget):
    """CBR Equivalent: Use DCP data or user-defined CBR / Hi layers."""

    results_changed = pyqtSignal()

    def __init__(self, dcp_page: DcpPage, parent=None):
        super().__init__(parent)
        expand_vertical(self)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._dcp_page = dcp_page
        self._mode = MODE_DCP

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)
        layout.addWidget(self._build_input_block(), 3)
        layout.addWidget(self._build_result_block(), 1)

        self._apply_mode_visibility()
        self._refresh_analysis()

    def sizeHint(self):  # noqa: N802
        # Prefer filling the viewport; avoid forcing page scroll.
        return self.minimumSizeHint()

    def minimumSizeHint(self):  # noqa: N802
        from PyQt6.QtCore import QSize

        return QSize(640, 360)

    def quick_results(self) -> dict[str, str]:
        return summarize_cbr_equivalent(self._current_result())

    def refresh_analysis(self) -> None:
        self._refresh_analysis()

    def _current_result(self):
        if self._mode == MODE_USER:
            return compute_cbr_equivalent_from_user_layers(
                self._read_user_layers(),
                design_depth_mm=None,
            )
        rows = analyze_dcp_rows(self._dcp_page.read_input_rows())
        return compute_cbr_equivalent(rows, design_depth_mm=None)

    def _build_input_block(self) -> QFrame:
        frame, section_layout = section_frame("Input")
        expand_vertical(frame)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(18)
        self.use_dcp_radio = make_radio("Use DCP data", checked=True)
        self.user_define_radio = make_radio("User define", checked=False)
        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self.use_dcp_radio, MODE_DCP)
        self._mode_group.addButton(self.user_define_radio, MODE_USER)
        self._mode_group.idClicked.connect(self._on_mode_changed)
        mode_row.addWidget(self.use_dcp_radio)
        mode_row.addWidget(self.user_define_radio)
        mode_row.addStretch()
        section_layout.addLayout(mode_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(16)
        content_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.reference_image = ReferenceImageLabel()
        content_row.addWidget(self.reference_image, 0)

        self.table_stack = QStackedWidget()
        self.dcp_table = self._build_dcp_table()
        self.user_table = self._build_user_table()
        self.table_stack.addWidget(self.dcp_table)
        self.table_stack.addWidget(self.user_table)
        self.table_stack.setMinimumHeight(_PAIR_MIN_HEIGHT)
        self.table_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_row.addWidget(self.table_stack, 1)

        section_layout.addLayout(content_row, 1)
        return frame

    def _build_result_block(self) -> QFrame:
        frame, section_layout = section_frame("Result")
        expand_vertical(frame)
        frame.setMinimumHeight(88)

        self.result_label = QLabel("Result = —")
        self.result_label.setWordWrap(True)
        self.result_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.result_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._style_result_label()
        section_layout.addWidget(self.result_label, 1)
        return frame

    def _style_result_label(self) -> None:
        accent = theme_tokens().accent
        font_pt = UiScale.pt(16)
        self.result_label.setStyleSheet(
            f"color: {accent}; font-size: {font_pt}pt; font-weight: 700; padding: 8px 4px;"
        )

    def _build_dcp_table(self) -> QTableWidget:
        table = QTableWidget(0, len(DCP_TABLE_HEADERS))
        table.setHorizontalHeaderLabels(DCP_TABLE_HEADERS)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(_PAIR_MIN_HEIGHT)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        configure_page_scroll(table)
        configure_subgrade_table(table)
        return table

    def _build_user_table(self) -> ExcelPasteTable:
        table = ExcelPasteTable(
            USER_TABLE_HEADERS,
            initial_rows=6,
            min_rows=4,
            use_add_row_footer=True,
            add_row_label="+ Add row",
        )
        table.setMinimumHeight(_PAIR_MIN_HEIGHT)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        configure_page_scroll(table)
        configure_subgrade_table(table)
        table.data_changed.connect(self._refresh_analysis)
        return table

    def _on_mode_changed(self, mode_id: int) -> None:
        self._mode = mode_id
        self._apply_mode_visibility()
        self._refresh_analysis()

    def _apply_mode_visibility(self) -> None:
        self.table_stack.setCurrentIndex(MODE_USER if self._mode == MODE_USER else MODE_DCP)

    def _read_user_layers(self) -> list[tuple[float, float]]:
        layers: list[tuple[float, float]] = []
        for values in self.user_table.read_numeric_rows():
            cbr = values[0]
            hi = values[1]
            if cbr is None and hi is None:
                continue
            if cbr is None or hi is None or hi <= 0:
                continue
            layers.append((float(cbr), float(hi)))
        return layers

    def _populate_dcp_table(self) -> None:
        rows = analyze_dcp_rows(self._dcp_page.read_input_rows())
        display_rows = build_dcp_cbr_display_rows(rows)
        self.dcp_table.setRowCount(len(display_rows))

        for row_index, row in enumerate(display_rows):
            values = [
                format_number(row.depth_mm, decimals=0),
                format_number(row.thickness_mm, decimals=0),
                format_number(row.total_blows, decimals=0),
                format_number(row.penetration_rate_mm_per_blow),
                format_number(row.layered_cbr_percent),
                row.evaluation or "—",
            ]
            for col_index, text in enumerate(values):
                self.dcp_table.setItem(row_index, col_index, subgrade_table_item(text))

        apply_subgrade_row_heights(self.dcp_table)

    def _refresh_analysis(self) -> None:
        if self._mode == MODE_DCP:
            self._populate_dcp_table()

        result = self._current_result()
        self.result_label.setText(format_cbr_equivalent_result(result))
        self._style_result_label()
        self.results_changed.emit()
