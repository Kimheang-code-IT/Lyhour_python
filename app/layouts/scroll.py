"""Scroll layout: page title + scrollable content slot."""
from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QScrollArea, QVBoxLayout

from app.layouts.base import BaseLayout, make_page_title
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content


class ScrollLayout(BaseLayout):
    """Title header and vertically scrollable content (long forms)."""

    name = "scroll"

    def _build_chrome(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        if self._title:
            root.addWidget(make_page_title(self._title, self))

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        fit_scroll_content(self._content_host)
        scroll.setWidget(self._content_host)
        configure_page_scroll(scroll)
        root.addWidget(scroll, 1)
