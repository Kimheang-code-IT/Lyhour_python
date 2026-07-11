"""Shared scroll-area configuration."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QScrollArea, QWidget


def configure_hidden_scrollbars(widget: QScrollArea | QWidget) -> None:
    """Hide scrollbar UI while keeping wheel / touch-pad scrolling."""
    if isinstance(widget, QScrollArea):
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return

    if hasattr(widget, "setHorizontalScrollBarPolicy"):
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    if hasattr(widget, "setVerticalScrollBarPolicy"):
        widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


def hidden_scrollbar_stylesheet() -> str:
    """Global QSS snippet to hide scrollbar tracks and arrow buttons."""
    return """
    QScrollBar:vertical {
        background: transparent;
        width: 0px;
        margin: 0;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 0px;
        margin: 0;
    }
    QScrollBar::handle:vertical,
    QScrollBar::handle:horizontal {
        background: transparent;
    }
    QScrollBar::add-line,
    QScrollBar::sub-line,
    QScrollBar::add-page,
    QScrollBar::sub-page {
        background: none;
        border: none;
        width: 0;
        height: 0;
    }
    """
