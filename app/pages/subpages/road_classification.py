"""Road Classification subpage."""
from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QWidget

from app.pages.subpages.common import result_card


class RoadClassificationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = result_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)

        title = QLabel("Road Classification")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        card_layout.addWidget(title)

        note = QFrame()
        note.setObjectName("roadClassificationNote")
        note.setStyleSheet("""
            #roadClassificationNote {
                border: 1px solid #3e3e40;
                border-radius: 4px;
            }
        """)
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(36, 28, 36, 28)

        description = QLabel(
            "- The design year is ____\n\n"
            "- So the projected AADT in ____ year\n\n"
            "  is ____ and projected PCU in ____"
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #1f5eff;
            font-family: 'Segoe Print', 'Comic Sans MS';
            font-size: 26px;
            line-height: 1.6;
        """)
        note_layout.addWidget(description)
        note_layout.addStretch()

        card_layout.addWidget(note, 1)
        layout.addWidget(card, 1)
