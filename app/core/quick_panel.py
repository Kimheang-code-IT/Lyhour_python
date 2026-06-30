"""Quick panel: compact results/actions. Currently served by Quick Results card in preview_panel."""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel


class QuickPanel(QFrame):
    """Optional separate quick panel. Main window may use preview_panel's Quick Results card instead."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quickPanel")
        self.setMinimumWidth(400)
        self.setMaximumWidth(430)
        self.setStyleSheet("""
            #quickPanel {
                background-color: #2d2d30;
                border: none;
                padding: 0;
            }
            #quickPanel QLabel {
                background-color: #2d2d30;
                color: #cccccc;
                font-size: 16px;
                border: none;
                padding: 10px 16px;
            }
            QLabel#quickPanelTitle {
                background-color: #333333;
                color: #ffffff;
                font-size: 15px;
                font-weight: bold;
                padding: 14px 16px;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QLabel#quickPanelRow {
                color: #cccccc;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Quick Results")
        title.setObjectName("quickPanelTitle")
        layout.addWidget(title)

        for text in (
            "AADT =",
            "PCU =",
            "Road classification =",
            "Number of lane =",
            "Capacity ratio =",
            "ESAL =",
        ):
            row = QLabel(text)
            row.setObjectName("quickPanelRow")
            layout.addWidget(row)

        layout.addStretch()
