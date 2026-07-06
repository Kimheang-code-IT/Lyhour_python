"""Base page class: picks a layout and fills its content slot."""
from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.layouts.meta import PageMeta
from app.layouts.registry import DEFAULT_LAYOUT, get_layout


class BasePage(QWidget):
    """Page with declarative layout assignment (like Nuxt pages + layouts).

    Subclasses either use ``@define_page(...)`` or set class attributes::

        class MyPage(BasePage):
            layout_name = "scroll"
            title = "Superelevation"

            def setup(self, content: QVBoxLayout) -> None:
                content.addWidget(...)
    """

    layout_name: str = DEFAULT_LAYOUT
    title: str = ""
    page_meta: PageMeta | None = None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        meta = self._resolve_meta()
        layout_cls = get_layout(meta.layout)
        self._layout_shell = layout_cls(title=meta.title, parent=self)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._layout_shell)

        self.setup(self._layout_shell.content_layout)

    @classmethod
    def _resolve_meta(cls) -> PageMeta:
        if getattr(cls, "page_meta", None) is not None:
            return cls.page_meta  # type: ignore[return-value]
        return PageMeta(
            layout=getattr(cls, "layout_name", DEFAULT_LAYOUT),
            title=getattr(cls, "title", ""),
        )

    def setup(self, content: QVBoxLayout) -> None:
        """Build widgets inside the layout content slot."""

    def activate_page(self) -> None:
        if hasattr(self._layout_shell, "activate_page"):
            self._layout_shell.activate_page()

    def refresh_ui_scale(self) -> None:
        if hasattr(self._layout_shell, "refresh_ui_scale"):
            self._layout_shell.refresh_ui_scale()

    def refresh_theme(self) -> None:
        if hasattr(self._layout_shell, "refresh_theme"):
            self._layout_shell.refresh_theme()
