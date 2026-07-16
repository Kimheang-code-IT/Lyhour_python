"""Editable table with Excel-style copy / cut / paste / delete and optional add-row footer."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QApplication,
    QHeaderView,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
)


class ExcelPasteTable(QTableWidget):
    """Spreadsheet-like table: TSV copy/paste, clear/delete rows, optional add-row footer."""

    data_changed = pyqtSignal()

    def __init__(
        self,
        headers: list[str],
        *,
        initial_rows: int = 20,
        min_rows: int = 20,
        use_add_row_footer: bool = False,
        add_row_label: str = "+ Add row",
        auto_fit_height: bool = False,
        show_row_numbers: bool = False,
        parent=None,
    ) -> None:
        self._headers = headers
        self._min_rows = max(1, min_rows)
        self._use_add_row_footer = use_add_row_footer
        self._add_row_label = add_row_label
        self._auto_fit_height = auto_fit_height
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
        self.verticalHeader().setVisible(show_row_numbers)
        if show_row_numbers:
            self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            self.verticalHeader().setDefaultSectionSize(28)
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        if auto_fit_height:
            self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.itemChanged.connect(self._on_item_changed)
        if use_add_row_footer:
            self.cellClicked.connect(self._on_cell_clicked)
            self._refresh_footer_row()
        if auto_fit_height:
            self.fit_height_to_rows()

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

    def fit_height_to_rows(self) -> None:
        """Size the table so every row is visible (no inner vertical scroll)."""
        if not self._auto_fit_height:
            return
        header_h = max(28, self.horizontalHeader().height())
        body_h = 0
        for row in range(self.rowCount()):
            body_h += max(28, self.rowHeight(row))
        frame = self.frameWidth() * 2
        self.setFixedHeight(header_h + body_h + frame + 4)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selection_to_clipboard()
            event.accept()
            return
        if event.matches(QKeySequence.StandardKey.Cut):
            self.copy_selection_to_clipboard()
            self.clear_selection_cells()
            event.accept()
            return
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste_from_clipboard()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.delete_selected_rows()
            else:
                self.clear_selection_cells()
            event.accept()
            return
        super().keyPressEvent(event)

    def copy_selection_to_clipboard(self) -> None:
        ranges = self.selectedRanges()
        if not ranges:
            item = self.currentItem()
            if item is None:
                return
            QApplication.clipboard().setText(item.text())
            return

        # Use bounding box of all selected ranges (Excel-like).
        top = min(r.topRow() for r in ranges)
        bottom = max(r.bottomRow() for r in ranges)
        left = min(r.leftColumn() for r in ranges)
        right = max(r.rightColumn() for r in ranges)
        footer = self.footer_row_index()

        lines: list[str] = []
        for row in range(top, bottom + 1):
            if footer is not None and row == footer:
                continue
            cells: list[str] = []
            for col in range(left, right + 1):
                cells.append(self._cell_text(row, col))
            lines.append("\t".join(cells))
        QApplication.clipboard().setText("\n".join(lines))

    def clear_selection_cells(self) -> None:
        footer = self.footer_row_index()
        items = self.selectedItems()
        if not items:
            item = self.currentItem()
            if item is None:
                return
            if footer is not None and item.row() == footer:
                return
            items = [item]

        self.blockSignals(True)
        try:
            for item in items:
                if footer is not None and item.row() == footer:
                    continue
                item.setText("")
        finally:
            self.blockSignals(False)

        if self._use_add_row_footer:
            self._refresh_footer_row()
        self.fit_height_to_rows()
        self.data_changed.emit()

    def delete_selected_rows(self) -> None:
        """Remove fully/partially selected data rows (Shift+Delete)."""
        footer = self.footer_row_index()
        rows = sorted({index.row() for index in self.selectedIndexes()}, reverse=True)
        if not rows:
            row = self.currentRow()
            if row >= 0:
                rows = [row]

        removed = False
        self.blockSignals(True)
        try:
            for row in rows:
                if footer is not None and row == footer:
                    continue
                if self.data_row_count() <= self._min_rows:
                    # Clear instead of going below min_rows.
                    for col in range(self.columnCount()):
                        item = self.item(row, col)
                        if item is not None:
                            item.setText("")
                    removed = True
                    continue
                self.removeRow(row)
                removed = True
                if footer is not None:
                    footer = self.footer_row_index()
        finally:
            self.blockSignals(False)

        if not removed:
            return
        if self._use_add_row_footer:
            self._refresh_footer_row()
        self.fit_height_to_rows()
        self.data_changed.emit()

    def paste_from_clipboard(self) -> None:
        text = QApplication.clipboard().text()
        if not text.strip():
            return

        start_row = self.currentRow()
        if start_row < 0:
            start_row = 0
        footer = self.footer_row_index()
        if footer is not None and start_row >= footer:
            start_row = max(0, footer)  # paste grows rows above footer

        start_col = self.currentColumn()
        if start_col < 0:
            start_col = 0

        lines = [
            line
            for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            if line != ""
        ]
        # Keep trailing blank Excel rows only if they carry tabs (empty cells).
        while lines and not lines[-1].strip() and "\t" not in lines[-1]:
            lines.pop()
        if not lines:
            return

        required_data_end = start_row + len(lines)
        self._ensure_data_rows(required_data_end)
        footer = self.footer_row_index()

        self.blockSignals(True)
        try:
            for row_offset, line in enumerate(lines):
                target_row = start_row + row_offset
                if footer is not None and target_row >= footer:
                    break
                if "\t" in line:
                    values = line.split("\t")
                elif ";" in line and "," not in line:
                    values = line.split(";")
                else:
                    values = line.split(",") if ("," in line and "\t" not in line) else [line]
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
        self.fit_height_to_rows()
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
            self.fit_height_to_rows()
            self.data_changed.emit()
            return self.rowCount() - 1

        footer = self.footer_row_index()
        if footer is None:
            self.setRowCount(self.rowCount() + 1)
            self._refresh_footer_row()
            self.fit_height_to_rows()
            self.data_changed.emit()
            return self.rowCount() - 2

        self.insertRow(footer)
        for col_index in range(self.columnCount()):
            if self.item(footer, col_index) is None:
                self.setItem(footer, col_index, QTableWidgetItem(""))
        self._refresh_footer_row()
        self.fit_height_to_rows()
        self.data_changed.emit()
        return footer

    def _on_cell_clicked(self, row: int, _col: int) -> None:
        if self._use_add_row_footer and row == self.footer_row_index():
            new_row = self.append_data_row()
            self.setCurrentCell(new_row, 0)
            item = self.item(new_row, 0)
            if item is not None:
                self.editItem(item)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._use_add_row_footer and item.row() == self.footer_row_index():
            self._refresh_footer_row()
            return
        if self._use_add_row_footer:
            self._refresh_footer_row()
        else:
            self._ensure_trailing_blank_rows()
        self.fit_height_to_rows()
        self.data_changed.emit()

    def _ensure_trailing_blank_rows(self) -> None:
        last_used = -1
        for row_index in range(self.rowCount()):
            if any(self._cell_text(row_index, col_index) for col_index in range(self.columnCount())):
                last_used = row_index

        target_rows = max(self._min_rows, last_used + 3)
        if self.rowCount() < target_rows:
            self.setRowCount(target_rows)

    def _ensure_data_rows(self, needed_data_rows: int) -> None:
        """Grow data rows so ``needed_data_rows`` indices exist (footer stays last)."""
        needed = max(self._min_rows, needed_data_rows)
        if self._use_add_row_footer:
            while self.data_row_count() < needed:
                footer = self.footer_row_index()
                if footer is None:
                    self.setRowCount(needed + 1)
                    break
                self.insertRow(footer)
            return

        if self.rowCount() < needed:
            self.setRowCount(needed)

    def _refresh_footer_row(self) -> None:
        if not self._use_add_row_footer or self.rowCount() == 0:
            return

        footer = self.footer_row_index()
        if footer is None:
            return

        self.blockSignals(True)
        try:
            for col_index in range(1, self.columnCount()):
                self.takeItem(footer, col_index)

            self.setSpan(footer, 0, 1, self.columnCount())
            item = self.item(footer, 0)
            if item is None:
                item = QTableWidgetItem()
                self.setItem(footer, 0, item)
            item.setText(self._add_row_label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item.setForeground(QColor("#888888"))
            item.setBackground(QColor(0, 0, 0, 0))
        finally:
            self.blockSignals(False)

    def _cell_text(self, row: int, col: int) -> str:
        item = self.item(row, col)
        return item.text().strip() if item is not None else ""
