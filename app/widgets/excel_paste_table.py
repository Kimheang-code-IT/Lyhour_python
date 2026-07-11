"""Editable table with Excel-style paste and optional add-row footer."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QTableWidget, QTableWidgetItem


class ExcelPasteTable(QTableWidget):
    """Spreadsheet-like table: paste TSV blocks, optional clickable add-row footer."""

    data_changed = pyqtSignal()

    def __init__(
        self,
        headers: list[str],
        *,
        initial_rows: int = 20,
        min_rows: int = 20,
        use_add_row_footer: bool = False,
        add_row_label: str = "+ Add row",
        parent=None,
    ) -> None:
        self._headers = headers
        self._min_rows = min_rows
        self._use_add_row_footer = use_add_row_footer
        self._add_row_label = add_row_label
        row_count = initial_rows + (1 if use_add_row_footer else 0)
        super().__init__(row_count, len(headers), parent)
        self.setHorizontalHeaderLabels(headers)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.verticalHeader().setVisible(False)
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.itemChanged.connect(self._on_item_changed)
        if use_add_row_footer:
            self.cellClicked.connect(self._on_cell_clicked)
            self._refresh_footer_row()

    @property
    def use_add_row_footer(self) -> bool:
        return self._use_add_row_footer

    def footer_row_index(self) -> int | None:
        if not self._use_add_row_footer or self.rowCount() == 0:
            return None
        return self.rowCount() - 1

    def data_row_count(self) -> int:
        if self._use_add_row_footer:
            return max(0, self.rowCount() - 1)
        return self.rowCount()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.matches(QKeyEvent.StandardKey.Paste):
            self.paste_from_clipboard()
            event.accept()
            return
        super().keyPressEvent(event)

    def paste_from_clipboard(self) -> None:
        text = QApplication.clipboard().text()
        if not text.strip():
            return

        start_row = self.currentRow()
        if start_row < 0:
            start_row = 0
        footer = self.footer_row_index()
        if footer is not None and start_row >= footer:
            start_row = footer
        start_col = self.currentColumn()
        if start_col < 0:
            start_col = 0

        lines = [line for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]
        required_rows = start_row + len(lines)
        self._ensure_row_count(required_rows)

        self.blockSignals(True)
        try:
            for row_offset, line in enumerate(lines):
                target_row = start_row + row_offset
                if footer is not None and target_row >= footer:
                    break
                values = line.split("\t")
                if len(values) == 1:
                    values = line.split(",")
                for col_offset, raw in enumerate(values):
                    col = start_col + col_offset
                    if col >= self.columnCount():
                        break
                    item = self.item(target_row, col)
                    if item is None:
                        item = QTableWidgetItem()
                        self.setItem(target_row, col, item)
                    item.setText(raw.strip())
        finally:
            self.blockSignals(False)

        if self._use_add_row_footer:
            self._refresh_footer_row()
        else:
            self._ensure_trailing_blank_rows()
        self.data_changed.emit()

    def read_numeric_rows(self) -> list[list[float | None]]:
        rows: list[list[float | None]] = []
        limit = self.data_row_count()
        for row_index in range(limit):
            values: list[float | None] = []
            empty = True
            for col_index in range(self.columnCount()):
                item = self.item(row_index, col_index)
                text = item.text().strip() if item is not None else ""
                if text:
                    empty = False
                    try:
                        values.append(float(text.replace(",", "")))
                    except ValueError:
                        values.append(None)
                else:
                    values.append(None)
            if not empty:
                rows.append(values)
        return rows

    def append_data_row(self) -> int:
        """Insert one editable row above the add-row footer."""
        if not self._use_add_row_footer:
            self.setRowCount(self.rowCount() + 1)
            self.data_changed.emit()
            return self.rowCount() - 1

        footer = self.footer_row_index()
        if footer is None:
            self.setRowCount(self.rowCount() + 1)
            self._refresh_footer_row()
            self.data_changed.emit()
            return self.rowCount() - 2

        self.insertRow(footer)
        for col_index in range(self.columnCount()):
            if self.item(footer, col_index) is None:
                self.setItem(footer, col_index, QTableWidgetItem(""))
        self._refresh_footer_row()
        self.data_changed.emit()
        return footer

    def _on_cell_clicked(self, row: int, _col: int) -> None:
        if self._use_add_row_footer and row == self.footer_row_index():
            new_row = self.append_data_row()
            self.setCurrentCell(new_row, 0)
            self.editItem(self.item(new_row, 0))

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._use_add_row_footer and item.row() == self.footer_row_index():
            self._refresh_footer_row()
            return
        if self._use_add_row_footer:
            self._refresh_footer_row()
        else:
            self._ensure_trailing_blank_rows()
        self.data_changed.emit()

    def _ensure_trailing_blank_rows(self) -> None:
        last_used = -1
        for row_index in range(self.rowCount()):
            if any(self._cell_text(row_index, col_index) for col_index in range(self.columnCount())):
                last_used = row_index

        target_rows = max(self._min_rows, last_used + 3)
        if self.rowCount() < target_rows:
            self.setRowCount(target_rows)

    def _ensure_row_count(self, count: int) -> None:
        if self._use_add_row_footer:
            footer = self.footer_row_index()
            if footer is None:
                return
            needed_data_rows = max(self._min_rows, count)
            while self.data_row_count() < needed_data_rows:
                self.insertRow(footer)
            return

        if self.rowCount() < count:
            self.setRowCount(max(count, self._min_rows))

    def _refresh_footer_row(self) -> None:
        if not self._use_add_row_footer or self.rowCount() == 0:
            return

        footer = self.footer_row_index()
        if footer is None:
            return

        for col_index in range(1, self.columnCount()):
            self.takeItem(footer, col_index)

        self.setSpan(footer, 0, 1, self.columnCount())
        item = self.item(footer, 0)
        if item is None:
            item = QTableWidgetItem()
            self.setItem(footer, 0, item)
        item.setText(self._add_row_label)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setForeground(QColor("#888888"))
        item.setBackground(QColor(0, 0, 0, 0))

    def _cell_text(self, row: int, col: int) -> str:
        item = self.item(row, col)
        return item.text().strip() if item is not None else ""
