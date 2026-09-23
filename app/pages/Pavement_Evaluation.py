"""Pavement and Material Design > Pavement Evaluation."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.theme import theme_tokens
from app.data.pavement_catalog import MATERIAL_COLORS, MATERIAL_HATCHES
from app.data.pavement_evaluation import (
    LAYER_DEFS,
    TRAFFIC_CLASSES,
    TRAFFIC_MSA_RANGES,
    compute_pavement_evaluation,
)
from app.layouts import BasePage, define_page
from app.widgets.form_controls import make_combo

TABLE_HEADERS = ("Layer", "Thickness (mm)", "Section", "FWD (MPa)", "LWD (MPa)", "B_Beam (mm)")
SECTION_COLUMN = 2
ROW_HEIGHT = 58

# Catalog hatch strings → Qt brush styles (so the section column matches the
# catalog cross-section drawing without embedding matplotlib).
_HATCH_TO_QT: dict[str, Qt.BrushStyle] = {
    "": Qt.BrushStyle.SolidPattern,
    "..": Qt.BrushStyle.Dense6Pattern,
    "xx": Qt.BrushStyle.DiagCrossPattern,
    "///": Qt.BrushStyle.BDiagPattern,
    "\\\\\\": Qt.BrushStyle.FDiagPattern,
    "---": Qt.BrushStyle.HorPattern,
    "|||": Qt.BrushStyle.VerPattern,
}


class HatchSwatch(QWidget):
    """Small layer-section swatch painted with the catalog material hatch."""

    def __init__(self, material: str, parent=None):
        super().__init__(parent)
        self._face = QColor(MATERIAL_COLORS.get(material, "#dddddd"))
        self._style = _HATCH_TO_QT.get(MATERIAL_HATCHES.get(material, ""), Qt.BrushStyle.SolidPattern)
        self.setMinimumSize(90, 34)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        rect = self.rect().adjusted(3, 4, -3, -4)
        painter.fillRect(rect, self._face)
        if self._style != Qt.BrushStyle.SolidPattern:
            painter.setBrush(QBrush(QColor("#2b2b2b"), self._style))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#111111"), 1))
        painter.drawRect(rect)


@define_page("default", title="Pavement Evaluation")
class PavementEvaluationPage(BasePage):
    def setup(self, content: QVBoxLayout) -> None:
        content.setSpacing(12)

        tokens = theme_tokens()

        top = QHBoxLayout()
        top.setSpacing(10)
        title = QLabel("Traffic Class :")
        title.setStyleSheet("font-weight: 700; font-size: 15px;")
        top.addWidget(title)

        self.traffic_combo = make_combo(list(TRAFFIC_CLASSES))
        self.traffic_combo.setCurrentText("T7")
        self.traffic_combo.setFixedWidth(120)
        self.traffic_combo.currentTextChanged.connect(self._refresh)
        top.addWidget(self.traffic_combo)

        self.msa_label = QLabel("")
        self.msa_label.setStyleSheet(f"color: {tokens.text_muted}; font-size: 13px;")
        top.addWidget(self.msa_label)
        top.addStretch()
        content.addLayout(top)

        self.table = self._build_table()
        content.addWidget(self.table, 1)
        content.addWidget(self._build_notes())

        self._refresh()

    def _build_table(self) -> QTableWidget:
        table = QTableWidget(len(LAYER_DEFS), len(TABLE_HEADERS))
        table.setHorizontalHeaderLabels(list(TABLE_HEADERS))
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.setWordWrap(True)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(SECTION_COLUMN, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(SECTION_COLUMN, 150)

        for row, layer_def in enumerate(LAYER_DEFS):
            table.setRowHeight(row, ROW_HEIGHT)
            table.setCellWidget(row, SECTION_COLUMN, HatchSwatch(layer_def.material))

        return table

    def _build_notes(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("pavementEvalNotes")
        frame.setStyleSheet(
            "#pavementEvalNotes { border: 1px solid #3e3e40; border-radius: 6px; }"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("Notes :")
        title.setStyleSheet("font-weight: 700;")
        layout.addWidget(title)

        note = QLabel(
            "CBR = California Bearing Ratio. Thickness and FWD / LWD / B_Beam values "
            "auto-fill from the selected Traffic Class."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {theme_tokens().text_muted}; font-size: 12px;")
        layout.addWidget(note)
        return frame

    def _refresh(self, *_args) -> None:
        traffic = self.traffic_combo.currentText()
        evaluation = compute_pavement_evaluation(traffic)
        self.msa_label.setText(f"MSA (million): {TRAFFIC_MSA_RANGES.get(traffic, '—')}")

        for row, layer in enumerate(evaluation.layers):
            name = layer.name if not layer.cbr_note else f"{layer.name}\n{layer.cbr_note}"
            self._set_item(row, 0, name, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._set_item(row, 1, self._fmt(layer.thickness_mm, 0))
            self._set_item(row, 3, self._fmt(layer.fwd_mpa, 0))
            self._set_item(row, 4, self._fmt(layer.lwd_mpa, 0))
            self._set_item(row, 5, self._fmt(layer.b_beam_mm, 2))

    def _set_item(
        self,
        row: int,
        column: int,
        text: str,
        *,
        align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
    ) -> None:
        item = self.table.item(row, column)
        if item is None:
            item = QTableWidgetItem()
            self.table.setItem(row, column, item)
        item.setText(text)
        item.setTextAlignment(align)

    @staticmethod
    def _fmt(value: float | None, decimals: int) -> str:
        if value is None:
            return "—"
        return f"{value:.{decimals}f}"
