"""Base layout shell: wraps page content in a named layout (Nuxt-style slot)."""
from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    from qfluentwidgets import SubtitleLabel

    _HAS_FLUENT = True
except Exception:
    SubtitleLabel = None  # type: ignore[assignment]
    _HAS_FLUENT = False


from app.core.theme import theme_tokens
from app.core.ui_style import title_style


def make_page_title(title: str, parent: QWidget | None = None) -> QWidget:
    if _HAS_FLUENT and SubtitleLabel is not None:
        heading = SubtitleLabel(title, parent)
    else:
        heading = QLabel(title, parent)
        heading.setStyleSheet(title_style(22))
    return heading


class BaseLayout(QWidget):
    """Layout shell with a content slot, similar to Nuxt ``<slot />``."""

    name = "base"

    def __init__(self, *, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._content_host = QWidget(self)
        self.content_layout = QVBoxLayout(self._content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self._build_chrome()

    def _build_chrome(self) -> None:
        raise NotImplementedError

    def set_content(self, widget: QWidget) -> None:
        """Replace slot content with a single child widget."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.content_layout.addWidget(widget)

    def activate_page(self) -> None:
        """Called when the sidebar selects this page."""

    def refresh_ui_scale(self) -> None:
        content = self._content_host
        if hasattr(content, "refresh_ui_scale"):
            content.refresh_ui_scale()

    def refresh_theme(self) -> None:
        content = self._content_host
        if hasattr(content, "refresh_theme"):
            content.refresh_theme()
