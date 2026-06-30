"""Number of Lane subpage."""
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.pages.subpages.common import BarChart, result_card


class NumberOfLanePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = result_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.addWidget(QLabel("Number of Lane"))
        card_layout.addWidget(BarChart(
            [],
            y_step=1,
            show_values=True,
        ), 1)
        layout.addWidget(card, 1)
