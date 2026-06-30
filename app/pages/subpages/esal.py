"""ESAL subpage."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.pages.subpages.common import BarChart, result_card


def _esal_axle_table() -> QTableWidget:
    table = QTableWidget(5, 6)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setMinimumHeight(250)
    table.setStyleSheet("""
        QTableWidget {
            background-color: #d8d8dc;
            color: #111111;
            border: 1px solid #606060;
            gridline-color: #606060;
        }
        QTableWidget::item {
            padding: 6px;
        }
    """)

    header_brush = QBrush(QColor("#f2f2f2"))
    body_brush = QBrush(QColor("#ffffff"))
    empty_brush = QBrush(QColor("#d8d8dc"))

    def set_item(row: int, column: int, text: str, brush: QBrush, bold: bool = False) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setBackground(brush)
        font = item.font()
        font.setPointSize(9)
        font.setBold(bold)
        item.setFont(font)
        table.setItem(row, column, item)

    for offset in (0, 3):
        set_item(0, offset, "Descriptions", header_brush, bold=True)
        set_item(0, offset + 1, "Remarque", header_brush, bold=True)
        set_item(0, offset + 2, "Number", header_brush, bold=True)

    set_item(1, 0, "Single Axle Steering\nWheel", body_brush)
    set_item(1, 1, "||      ||", body_brush, bold=True)
    set_item(1, 2, "-", body_brush, bold=True)
    table.setSpan(1, 2, 2, 1)

    set_item(2, 0, "Single Axle\nSingle Tire", body_brush)
    set_item(2, 1, "||  --  ||", body_brush, bold=True)

    for column in range(3, 6):
        set_item(1, column, "", empty_brush)

    set_item(2, 3, "Single Axle\nDual Tire", body_brush)
    set_item(2, 4, "|| || -- || ||", body_brush, bold=True)
    set_item(2, 5, "-", body_brush, bold=True)

    set_item(3, 0, "Tandem Axle\nSingle Tire", body_brush)
    set_item(3, 1, "||  --  ||\n||  --  ||", body_brush, bold=True)
    set_item(3, 2, "-", body_brush, bold=True)

    set_item(3, 3, "Tandem Axle\nDual Tire", body_brush)
    set_item(3, 4, "|| || -- || ||\n|| || -- || ||", body_brush, bold=True)
    set_item(3, 5, "-", body_brush, bold=True)

    for column in range(3):
        set_item(4, column, "", empty_brush)

    set_item(4, 3, "Tridem Axle\nDual Tire", body_brush)
    set_item(4, 4, "|| || -- || ||\n|| || -- || ||\n|| || -- || ||", body_brush, bold=True)
    set_item(4, 5, "-", body_brush, bold=True)

    for row in range(table.rowCount()):
        table.setRowHeight(row, 42 if row == 0 else 50)
    return table


class EsalPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        table_card = result_card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.addWidget(QLabel("ESAL Axle Type Summary"))
        table_layout.addWidget(_esal_axle_table())
        layout.addWidget(table_card)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(16)

        chart_card = result_card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 12, 12, 12)
        chart_layout.addWidget(QLabel("ESAL by Design Period"))
        chart_layout.addWidget(BarChart(
            [],
            y_step=100,
            show_values=True,
        ), 1)
        bottom_row.addWidget(chart_card, 2)

        description_card = result_card()
        description_layout = QVBoxLayout(description_card)
        description_layout.setContentsMargins(12, 12, 12, 12)
        description_layout.addWidget(QLabel("Design Period Description"))

        note = QFrame()
        note.setObjectName("esalDescriptionNote")
        note.setStyleSheet("""
            #esalDescriptionNote {
                border: 1px solid #3e3e40;
                border-radius: 4px;
            }
        """)
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(24, 24, 24, 24)

        description = QLabel(
            "- Desing peroid in 15 year is ____\n\n"
            "- Desing peroid in 20 year is ____\n\n"
            "- Desing peroid in 25 year is ____"
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #1f5eff;
            font-family: 'Segoe Print', 'Comic Sans MS';
            font-size: 15px;
            line-height: 1.4;
        """)
        note_layout.addWidget(description)
        note_layout.addStretch()
        description_layout.addWidget(note, 1)
        description_layout.addStretch()
        bottom_row.addWidget(description_card, 1)
        layout.addLayout(bottom_row, 1)
