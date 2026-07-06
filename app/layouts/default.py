"""Default layout: page title + content area."""
from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout

from app.layouts.base import BaseLayout, make_page_title


class DefaultLayout(BaseLayout):
    """Title header and flexible content slot (most sidebar pages)."""

    name = "default"

    def _build_chrome(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        if self._title:
            root.addWidget(make_page_title(self._title, self))

        root.addWidget(self._content_host, 1)
