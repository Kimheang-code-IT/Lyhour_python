"""Subgrade Design > FWD page."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.pages.Subgrade_Design.common import section_frame


class FwdPage(QWidget):
    """FWD/BB analysis placeholder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        frame, section_layout = section_frame("FWD/BB")
        message = QLabel("FWD/BB analysis will be added here.")
        message.setStyleSheet("color: #888888; font-size: 14px; padding: 24px;")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        section_layout.addWidget(message)
        layout.addWidget(frame)

    def quick_results(self) -> dict[str, str]:
        return {}
