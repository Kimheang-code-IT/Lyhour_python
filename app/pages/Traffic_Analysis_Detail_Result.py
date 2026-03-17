"""Traffic Analysis > Detail Result placeholder page."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class TrafficAnalysisDetailResultPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        lbl = QLabel("Detail Result")
        lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl)
        desc = QLabel("Traffic analysis detail results.")
        desc.setStyleSheet("color: #888;")
        layout.addWidget(desc)
        layout.addStretch()
