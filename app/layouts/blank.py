"""Blank layout: full-area content slot with no chrome."""
from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout

from app.layouts.base import BaseLayout


class BlankLayout(BaseLayout):
    """Content only — use for fully custom pages (calculators, tabbed views)."""

    name = "blank"

    def _build_chrome(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._content_host, 1)
