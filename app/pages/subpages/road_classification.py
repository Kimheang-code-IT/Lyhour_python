"""Road Classification subpage."""
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app.pages.subpages.common import result_card

_PLACEHOLDER = "____"


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

        self._description = QLabel()
        self._description.setWordWrap(True)
        self._description.setStyleSheet("""
            color: #1f5eff;
            font-family: 'Segoe Print', 'Comic Sans MS';
            font-size: 26px;
            line-height: 1.6;
        """)
        note_layout.addWidget(self._description)
        note_layout.addStretch()

        card_layout.addWidget(note, 1)
        layout.addWidget(card, 1)
        self.set_road_classification(None, None, None)

    def set_road_classification(
        self,
        design_year: str | None,
        total_aadt: int | None,
        total_pcu: int | None,
    ) -> None:
        year = design_year.strip() if design_year else _PLACEHOLDER
        aadt = f"{total_aadt:,}" if total_aadt else _PLACEHOLDER
        pcu = f"{total_pcu:,}" if total_pcu else _PLACEHOLDER
        self._description.setText(
            f"- The design year is {year}\n\n"
            f"- So the projected AADT in {year}\n\n"
            f"  is {aadt} and projected PCU in {pcu}"
        )
