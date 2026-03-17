"""Quick panel: compact results/actions. Currently served by Quick Results card in preview_panel."""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel


class QuickPanel(QFrame):
    """Optional separate quick panel. Main window may use preview_panel's Quick Results card instead."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quickPanel")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Quick"))
        # Can be extended with compact result list or action buttons
