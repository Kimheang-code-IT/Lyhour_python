"""ESAL subpage."""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QAbstractItemView,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.widgets.form_controls import make_combo, make_radio
from app.core.theme import theme_tokens
from app.utils.result_html import result_highlight_style, wrap_result_description_lines
from app.core.ui_scale import UiScale
from app.core.ui_style import card_title_style, label_style, section_title_style, subtitle_style
from app.widgets.traffic_results import (
    BarChart,
    configure_result_description_note_layout,
    highlight_result_table_row,
    refresh_theme_widgets,
    result_card,
    result_description_label,
    result_description_note,
    scrollable_result_table,
)
from app.services.traffic_esal import (
    EsalResult,
    build_design_period_description_html,
    chart_bars_from_esal,
)
from app.services.traffic_tld_excel import read_tld_workbook
from app.widgets.button import secondary_button

ESAL_LOAD_MODE_STANDARD = "standard_load"
ESAL_LOAD_MODE_TLD = "tld"
STANDARD_LANE_OPTIONS = ["1", "2", "3"]

_ESAL_IMAGE_FILES = {
    "single_tire": "Single Axle Sing Tire.png",
    "tandem_single_tire": "Tamdem Axle signle tire.png",
    "dual_tire": "Single Axle Dual Tire.png",
    "tandem_dual_tire": "Tandem Axle Dual tire.png",
    "tridem_dual_tire": "Tridem Axle Dual Tire.png",
}

_HEADER_ROW_HEIGHT = 34
_BODY_ROW_WEIGHTS = (1.0, 1.15, 1.35)
_COLUMN_WEIGHTS = (3.0, 3.5, 1.2, 3.0, 3.5, 1.2)

_EMPTY_DESCRIPTION_YEARS = (15, 20, 25)


def _empty_description(*, panel_width: int | None = None) -> str:
    highlight = result_highlight_style()
    placeholder = f'<span style="{highlight}">____</span>'
    lines = [
        f"- Design period in {years} year is {placeholder}"
        for years in _EMPTY_DESCRIPTION_YEARS
    ]
    return wrap_result_description_lines(lines, panel_width=panel_width)


def _image_assets_dir() -> Path:
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS) / "app" / "assets" / "image"
    return Path(__file__).resolve().parent.parent.parent / "assets" / "image"


def _format_number(value: int) -> str:
    return f"{value:,}" if value else "-"


class RemarqueImageLabel(QLabel):
    """Scales an axle diagram to fill the Remarque table cell."""

    def __init__(self, filename: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._source = QPixmap()
        path = _image_assets_dir() / filename
        if path.is_file():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self._source = pixmap
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #ffffff; border: none;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(1, 1)
        self._refresh_pixmap()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self) -> None:
        if self._source.isNull():
            self.clear()
            return
        available = self.size().expandedTo(self.minimumSize())
        margin = 6
        target_w = max(1, available.width() - margin * 2)
        target_h = max(1, available.height() - margin * 2)
        self.setPixmap(
            self._source.scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class DescriptionCell(QLabel):
    """Wrapped description text for ESAL table cells."""

    def __init__(self, text: str, *, background: str = "#ffffff", parent: QWidget | None = None):
        super().__init__(text, parent)
        self._background = background
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.apply_ui_scale(table_width=0)

    def apply_ui_scale(self, *, table_width: int) -> None:
        padding = UiScale.px_local(8, table_width, reference=900)
        font_pt = UiScale.pt_local(10, table_width, reference=900)
        self.setStyleSheet(
            f"background-color: {self._background}; color: #111111; "
            f"padding: {padding}px; font-size: {font_pt}pt;"
        )


class EsalAxleTable(QTableWidget):
    """ESAL axle summary table that expands to fill available space."""

    _NUMBER_CELLS: tuple[tuple[int, int, str], ...] = (
        (1, 2, "steering_sast"),
        (1, 5, "sadt"),
        (2, 2, "tast"),
        (2, 5, "tadt"),
        (3, 5, "trdt"),
    )

    def __init__(self, parent: QWidget | None = None):
        super().__init__(4, 6, parent)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustIgnored)
        self.verticalHeader().setMinimumSectionSize(1)
        self.horizontalHeader().setMinimumSectionSize(1)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: #d8d8dc;
                color: #111111;
                border: 1px solid #606060;
                gridline-color: #606060;
            }}
            QTableWidget::item {{
                padding: {UiScale.px(6)}px;
            }}
        """)
        self._populate()
        self._configure_resize_modes()

    def apply_ui_scale(self) -> None:
        table_width = max(self.viewport().width(), self.width(), 1)
        padding = UiScale.px_local(6, table_width, reference=900)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: #d8d8dc;
                color: #111111;
                border: 1px solid #606060;
                gridline-color: #606060;
            }}
            QTableWidget::item {{
                padding: {padding}px;
            }}
        """)

        header_pt = UiScale.pt_local(10, table_width, reference=900)
        number_pt = UiScale.pt_local(11, table_width, reference=900)
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                item = self.item(row, column)
                if item is None:
                    continue
                font = item.font()
                if row == 0:
                    font.setPointSizeF(header_pt)
                    font.setBold(True)
                elif column in (2, 5):
                    font.setPointSizeF(number_pt)
                    font.setBold(True)
                item.setFont(font)

        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                widget = self.cellWidget(row, column)
                if isinstance(widget, DescriptionCell):
                    widget.apply_ui_scale(table_width=table_width)

        self._fit_table_layout()

    def _configure_resize_modes(self) -> None:
        vertical_header = self.verticalHeader()
        horizontal_header = self.horizontalHeader()
        for row_index in range(self.rowCount()):
            vertical_header.setSectionResizeMode(row_index, QHeaderView.ResizeMode.Fixed)
        for column_index in range(self.columnCount()):
            horizontal_header.setSectionResizeMode(column_index, QHeaderView.ResizeMode.Fixed)

    def _populate(self) -> None:
        header_brush = QBrush(QColor("#f2f2f2"))
        body_brush = QBrush(QColor("#ffffff"))
        empty_brush = QBrush(QColor("#d8d8dc"))

        def set_header(row: int, column: int, text: str) -> None:
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(header_brush)
            font = item.font()
            font.setPointSizeF(UiScale.pt(10))
            font.setBold(True)
            item.setFont(font)
            self.setItem(row, column, item)

        def set_number(row: int, column: int, text: str = "-") -> None:
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(body_brush)
            font = item.font()
            font.setPointSizeF(UiScale.pt(11))
            font.setBold(True)
            item.setFont(font)
            self.setItem(row, column, item)

        def set_description(row: int, column: int, text: str) -> None:
            self.setCellWidget(row, column, DescriptionCell(text))

        def set_remarque(row: int, column: int, image_key: str) -> None:
            filename = _ESAL_IMAGE_FILES[image_key]
            self.setCellWidget(row, column, RemarqueImageLabel(filename))

        def set_empty(row: int, column: int) -> None:
            item = QTableWidgetItem("")
            item.setBackground(empty_brush)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(row, column, item)

        for offset in (0, 3):
            set_header(0, offset, "Descriptions")
            set_header(0, offset + 1, "Remarque")
            set_header(0, offset + 2, "Number")

        set_description(1, 0, "SAST")
        set_remarque(1, 1, "single_tire")
        set_number(1, 2)

        set_description(1, 3, "SADT")
        set_remarque(1, 4, "dual_tire")
        set_number(1, 5)

        set_description(2, 0, "TAST")
        set_remarque(2, 1, "tandem_single_tire")
        set_number(2, 2)

        set_description(2, 3, "TADT")
        set_remarque(2, 4, "tandem_dual_tire")
        set_number(2, 5)

        for column in range(3):
            set_empty(3, column)

        set_description(3, 3, "TRDT")
        set_remarque(3, 4, "tridem_dual_tire")
        set_number(3, 5)

    def update_numbers(self, axle_numbers: dict[str, int] | None) -> None:
        numbers = axle_numbers or {}
        for row, column, key in self._NUMBER_CELLS:
            item = self.item(row, column)
            if item is None:
                continue
            item.setText(_format_number(numbers.get(key, 0)))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_table_layout()
        self.apply_ui_scale()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._fit_table_layout()

    def _fit_table_layout(self) -> None:
        viewport_height = self.viewport().height()
        viewport_width = self.viewport().width()
        if viewport_height <= 0 or viewport_width <= 0:
            return

        header_height = min(UiScale.px(_HEADER_ROW_HEIGHT), max(UiScale.px(20), viewport_height // 8))
        self.setRowHeight(0, header_height)

        body_height = max(1, viewport_height - header_height)
        weight_total = sum(_BODY_ROW_WEIGHTS)
        assigned_height = 0
        for row_index, weight in enumerate(_BODY_ROW_WEIGHTS, start=1):
            if row_index == self.rowCount() - 1:
                row_height = max(1, body_height - assigned_height)
            else:
                row_height = max(1, int(body_height * weight / weight_total))
                assigned_height += row_height
            self.setRowHeight(row_index, row_height)

        column_widths = self._column_widths_for_viewport(viewport_width)
        for column_index, width in enumerate(column_widths):
            self.setColumnWidth(column_index, width)

        row_delta = viewport_height - sum(self.rowHeight(row) for row in range(self.rowCount()))
        if row_delta:
            last_row = self.rowCount() - 1
            self.setRowHeight(last_row, max(1, self.rowHeight(last_row) + row_delta))

        column_delta = viewport_width - sum(self.columnWidth(column) for column in range(self.columnCount()))
        if column_delta:
            last_column = self.columnCount() - 1
            self.setColumnWidth(last_column, max(1, self.columnWidth(last_column) + column_delta))

        self.verticalScrollBar().setValue(0)
        self.horizontalScrollBar().setValue(0)

    @staticmethod
    def _column_widths_for_viewport(viewport_width: int) -> list[int]:
        weight_total = sum(_COLUMN_WEIGHTS)
        widths = [max(1, int(viewport_width * weight / weight_total)) for weight in _COLUMN_WEIGHTS]
        width_delta = viewport_width - sum(widths)
        widths[-1] += width_delta
        return widths


class EsalPage(QWidget):
    _ESAL_TABLE_MAX_VISIBLE_ROWS = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: EsalResult | None = None
        self._tld_excel_path: str | None = None

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        options_row = QWidget()
        options_layout = QHBoxLayout(options_row)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(UiScale.px(20))

        self._standard_load_radio = make_radio("Assume Standard Load", checked=True)
        self._use_tld_radio = make_radio("Use TLD")
        self._load_mode_group = QButtonGroup(self)
        self._load_mode_group.addButton(self._standard_load_radio)
        self._load_mode_group.addButton(self._use_tld_radio)
        options_layout.addWidget(self._standard_load_radio)
        options_layout.addWidget(self._use_tld_radio)
        options_layout.addStretch(1)

        self._lane_row = QWidget()
        lane_row_layout = QHBoxLayout(self._lane_row)
        lane_row_layout.setContentsMargins(0, 0, 0, 0)
        lane_row_layout.setSpacing(8)
        self._lane_label = QLabel("Lane =")
        self._lane_combo = make_combo(STANDARD_LANE_OPTIONS)
        lane_row_layout.addWidget(self._lane_label)
        lane_row_layout.addWidget(self._lane_combo)
        options_layout.addWidget(self._lane_row)

        self._tld_row = QWidget()
        tld_row_layout = QHBoxLayout(self._tld_row)
        tld_row_layout.setContentsMargins(0, 0, 0, 0)
        tld_row_layout.setSpacing(8)
        self._read_tld_btn = secondary_button("Read Excel", min_height=36)
        self._tld_path_label = QLabel("")
        self._tld_path_label.setWordWrap(True)
        self._tld_path_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tld_row_layout.addWidget(self._tld_path_label)
        tld_row_layout.addWidget(self._read_tld_btn)
        options_layout.addWidget(self._tld_row)
        self._tld_row.hide()

        layout.addWidget(options_row)

        self._standard_load_radio.toggled.connect(self._on_load_mode_changed)
        self._lane_combo.currentTextChanged.connect(self._on_lane_changed)
        self._read_tld_btn.clicked.connect(self._on_read_tld_excel)

        axle_card = result_card()
        axle_layout = QVBoxLayout(axle_card)
        axle_layout.setContentsMargins(12, 12, 12, 12)
        axle_layout.setSpacing(8)

        self._table_title = QLabel("ESAL Axle per day")
        axle_layout.addWidget(self._table_title)

        self._axle_table = EsalAxleTable()
        self._axle_table.setMinimumHeight(UiScale.px(180))
        axle_layout.addWidget(self._axle_table, 1)
        layout.addWidget(axle_card)

        chart_card = result_card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        chart_layout.setSpacing(8)

        self._chart_title = QLabel("ESAL by Design Period")
        chart_layout.addWidget(self._chart_title)

        self._chart_slot = QVBoxLayout()
        self._chart_slot.setContentsMargins(0, 0, 0, 0)
        self._chart = BarChart([], y_step=100_000, show_values=True)
        self._chart_slot.addWidget(self._chart)
        chart_layout.addLayout(self._chart_slot)
        layout.addWidget(chart_card)

        details_row = QHBoxLayout()
        details_row.setContentsMargins(0, 0, 0, 0)
        details_row.setSpacing(16)

        esal_card = result_card()
        esal_layout = QVBoxLayout(esal_card)
        esal_layout.setContentsMargins(12, 12, 12, 12)
        esal_layout.setSpacing(8)

        self._esal_table_title = QLabel("Design Period")
        esal_layout.addWidget(self._esal_table_title)

        self._esal_table_slot = QVBoxLayout()
        self._esal_table_slot.setContentsMargins(0, 0, 0, 0)
        self._esal_table = scrollable_result_table(
            ["Year", "ESAL"],
            [],
            max_visible_rows=self._ESAL_TABLE_MAX_VISIBLE_ROWS,
        )
        self._esal_table_slot.addWidget(self._esal_table)
        esal_layout.addLayout(self._esal_table_slot)
        details_row.addWidget(esal_card, 1)

        description_card = result_card()
        description_layout = QVBoxLayout(description_card)
        description_layout.setContentsMargins(12, 12, 12, 12)
        description_layout.setSpacing(8)
        description_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._description_title = QLabel("Design Period Description")
        description_layout.addWidget(self._description_title, 0, Qt.AlignmentFlag.AlignTop)

        note = result_description_note(dark_background=False)
        note_layout = QVBoxLayout(note)
        note_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._description = result_description_label()
        configure_result_description_note_layout(note_layout, self._description)
        description_layout.addWidget(note, 1, Qt.AlignmentFlag.AlignTop)
        details_row.addWidget(description_card, 1)

        layout.addLayout(details_row)
        layout.addStretch()

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)
        self._sync_load_mode_controls()
        self.refresh_ui_scale()

    def active_esal_load_mode(self) -> str:
        if self._use_tld_radio.isChecked():
            return ESAL_LOAD_MODE_TLD
        return ESAL_LOAD_MODE_STANDARD

    def active_standard_lane_count(self) -> int:
        try:
            return max(1, min(3, int(self._lane_combo.currentText())))
        except ValueError:
            return 1

    def tld_excel_path(self) -> str | None:
        return self._tld_excel_path

    def _sync_load_mode_controls(self) -> None:
        use_tld = self._use_tld_radio.isChecked()
        self._lane_row.setVisible(not use_tld)
        self._tld_row.setVisible(use_tld)

    def _on_load_mode_changed(self, _checked: bool = False) -> None:
        self._sync_load_mode_controls()
        self._request_esal_refresh()

    def _on_lane_changed(self, _text: str = "") -> None:
        if self.active_esal_load_mode() == ESAL_LOAD_MODE_STANDARD:
            self._request_esal_refresh()

    def _on_read_tld_excel(self) -> None:
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Read TLD Excel",
            "",
            "Excel (*.xlsx *.xlsm *.xls);;All Files (*)",
        )
        if not path:
            return

        try:
            tld_data = read_tld_workbook(path)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Read TLD Excel",
                f"Selected Excel file:\n{path}\n\nCould not read TLD data:\n{exc}",
            )
            return

        self._tld_excel_path = tld_data.get("source_path", path)
        self._tld_path_label.setText(Path(self._tld_excel_path).name)

        mw = self.window()
        if hasattr(mw, "set_tld_excel_data"):
            mw.set_tld_excel_data(tld_data)

        parsed_text = (
            "Axle values were loaded from the workbook."
            if tld_data.get("has_parsed_values")
            else "File accepted. ESAL will use session traffic data until axle values are found in the workbook."
        )
        QMessageBox.information(
            self,
            "Read TLD Excel",
            f"Selected Excel file:\n{self._tld_excel_path}\n\n{parsed_text}",
        )

    def _request_esal_refresh(self) -> None:
        mw = self.window()
        if hasattr(mw, "refresh_esal"):
            mw.refresh_esal()

    def _apply_options_style(self) -> None:
        option_pt = UiScale.pt(16)
        option_px = UiScale.px(16)
        tokens = theme_tokens()
        radio_style = (
            f"QRadioButton {{ color: {tokens.text_primary}; font-size: {option_px}px; "
            f"margin: 0; padding: 0; spacing: {UiScale.px(8)}px; }}"
        )
        self._standard_load_radio.setStyleSheet(radio_style)
        self._use_tld_radio.setStyleSheet(radio_style)
        label_font = self._lane_label.font()
        label_font.setPointSizeF(option_pt)
        self._lane_label.setFont(label_font)
        self._lane_label.setStyleSheet(label_style(16))

        path_font = self._tld_path_label.font()
        path_font.setPointSizeF(UiScale.pt(14))
        self._tld_path_label.setFont(path_font)
        self._tld_path_label.setStyleSheet(subtitle_style(14))

        combo_height = UiScale.px(30)
        self._lane_combo.setMinimumHeight(combo_height)
        self._lane_combo.setMaximumHeight(combo_height)
        self._lane_combo.setFixedWidth(UiScale.px(56))
        combo_font = self._lane_combo.font()
        combo_font.setPointSizeF(UiScale.pt(14))
        self._lane_combo.setFont(combo_font)

        self._read_tld_btn.setMinimumHeight(UiScale.px(36))

    def refresh_ui_scale(self) -> None:
        self._apply_options_style()
        self._table_title.setStyleSheet(section_title_style(18))
        self._esal_table_title.setStyleSheet(card_title_style(14))
        self._chart_title.setStyleSheet(card_title_style(14))
        self._description_title.setStyleSheet(card_title_style(14))
        self._axle_table.setMinimumHeight(UiScale.px(180))
        self._axle_table.apply_ui_scale()
        self._refresh()

    def refresh_theme(self) -> None:
        refresh_theme_widgets(self)
        self.refresh_ui_scale()

    def set_esal_result(self, result: EsalResult | None) -> None:
        self._result = result
        self._refresh()

    def _description_panel_width(self) -> int:
        width = self._description.width()
        if width > 0:
            return width
        note = self._description.parentWidget()
        if note is not None and note.width() > 0:
            return note.width()
        return UiScale.width() // 4

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._axle_table._fit_table_layout()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._axle_table._fit_table_layout()
        self._axle_table.apply_ui_scale()
        panel_width = self._description_panel_width()
        if self._result is not None and self._result.has_data:
            description = build_design_period_description_html(
                self._result.design_periods,
                panel_width=panel_width,
            )
        else:
            description = _empty_description(panel_width=panel_width)
        self._description.setText(description)

    def _refresh(self) -> None:
        panel_width = self._description_panel_width()
        if self._result is not None and self._result.has_data:
            self._axle_table.update_numbers(self._result.axle_numbers)
            bars = chart_bars_from_esal(self._result)
            esal_table_rows = self._result.esal_table_rows
            highlight_row = self._result.esal_table_highlight_row
            description = build_design_period_description_html(
                self._result.design_periods,
                panel_width=panel_width,
            )
        else:
            self._axle_table.update_numbers(None)
            bars = []
            esal_table_rows = []
            highlight_row = None
            description = _empty_description(panel_width=panel_width)

        self._description.setText(description)

        y_step = self._chart_y_step(bars)
        chart_height = self._chart_height(len(bars))
        self._chart_slot.removeWidget(self._chart)
        self._chart.deleteLater()
        self._chart = BarChart(bars, y_step=y_step, show_values=True)
        self._chart.setMinimumHeight(chart_height)
        self._chart.setFixedHeight(chart_height)
        self._chart_slot.addWidget(self._chart, 1)

        self._esal_table_slot.removeWidget(self._esal_table)
        self._esal_table.deleteLater()
        self._esal_table = scrollable_result_table(
            ["Year", "ESAL"],
            esal_table_rows,
            max_visible_rows=self._ESAL_TABLE_MAX_VISIBLE_ROWS,
        )
        highlight_result_table_row(self._esal_table, highlight_row)
        if highlight_row is not None:
            item = self._esal_table.item(highlight_row, 0)
            if item is not None:
                self._esal_table.scrollToItem(
                    item,
                    QAbstractItemView.ScrollHint.PositionAtCenter,
                )
        self._esal_table_slot.addWidget(self._esal_table)

    def _chart_height(self, bar_count: int) -> int:
        base = UiScale.px(320)
        if bar_count <= 4:
            return base
        return base + (bar_count - 4) * UiScale.px(28)

    @staticmethod
    def _chart_y_step(bars: list[tuple[str, float, str]]) -> int:
        if not bars:
            return 100_000
        max_value = max(value for _label, value, _color in bars)
        if max_value <= 1_000:
            return 100
        if max_value <= 10_000:
            return 1_000
        if max_value <= 100_000:
            return 10_000
        if max_value <= 1_000_000:
            return 100_000
        return max(100_000, int(math.ceil(max_value / 5 / 100_000)) * 100_000)
