"""Skeleton placeholder blocks for page and full-screen loading states."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from app.core.theme import theme_tokens
from app.core.ui_scale import UiScale


def _skeleton_stylesheet() -> str:
    tokens = theme_tokens()
    base = tokens.bg_card_header
    highlight = tokens.hover
    return (
        f"background-color: {base}; border: 1px solid {tokens.border_subtle}; "
        "border-radius: 6px;"
    ), highlight


class SkeletonBlock(QFrame):
    """Single skeleton bar."""

    def __init__(
        self,
        *,
        height: int = 16,
        width: int | None = None,
        stretch: int = 0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("skeletonBlock")
        self._stretch = stretch
        self.setFixedHeight(UiScale.px(height))
        if width is not None:
            self.setFixedWidth(UiScale.px(width))
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if width is not None:
            policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setSizePolicy(policy)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        style, _highlight = _skeleton_stylesheet()
        self.setStyleSheet(f"#skeletonBlock {{ {style} }}")


class SkeletonCard(QFrame):
    """Skeleton card with a few content bars."""

    def __init__(self, *, bar_count: int = 3, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("skeletonCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        for index in range(bar_count):
            layout.addWidget(SkeletonBlock(height=14 if index else 18, stretch=1))
        self.refresh_theme()

    def refresh_theme(self) -> None:
        tokens = theme_tokens()
        self.setStyleSheet(
            f"#skeletonCard {{ background-color: {tokens.bg_card}; "
            f"border: 1px solid {tokens.border}; border-radius: 8px; }}"
        )
        for block in self.findChildren(SkeletonBlock):
            block.refresh_theme()


class SkeletonTable(QFrame):
    """Skeleton table with header and rows."""

    def __init__(self, *, rows: int = 4, columns: int = 4, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("skeletonTable")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        for _ in range(columns):
            header_row.addWidget(SkeletonBlock(height=18), 1)
        layout.addLayout(header_row)

        for _ in range(rows):
            row = QHBoxLayout()
            row.setSpacing(8)
            for _ in range(columns):
                row.addWidget(SkeletonBlock(height=14), 1)
            layout.addLayout(row)

        self.refresh_theme()

    def refresh_theme(self) -> None:
        tokens = theme_tokens()
        self.setStyleSheet(
            f"#skeletonTable {{ background-color: {tokens.bg_card}; "
            f"border: 1px solid {tokens.border}; border-radius: 8px; }}"
        )
        for block in self.findChildren(SkeletonBlock):
            block.refresh_theme()


class SkeletonPage(QWidget):
    """Page-sized skeleton used while lazy-loading a screen."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("skeletonPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(SkeletonBlock(height=28, width=280))
        layout.addWidget(SkeletonBlock(height=16, width=180))
        layout.addSpacing(8)
        layout.addWidget(SkeletonCard(bar_count=3), 1)
        layout.addWidget(SkeletonTable(rows=5, columns=5), 2)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        tokens = theme_tokens()
        self.setStyleSheet(f"#skeletonPage {{ background-color: {tokens.bg_window}; }}")
        for widget in self.findChildren((SkeletonBlock, SkeletonCard, SkeletonTable)):
            if hasattr(widget, "refresh_theme"):
                widget.refresh_theme()


class SkeletonPanel(QWidget):
    """Compact skeleton panel for full-screen loading overlays."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("skeletonPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(SkeletonBlock(height=24, width=240))
        layout.addWidget(SkeletonBlock(height=14, width=160))
        layout.addSpacing(6)
        layout.addWidget(SkeletonCard(bar_count=2))
        layout.addWidget(SkeletonTable(rows=4, columns=4), 1)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet("background: transparent;")
        for widget in self.findChildren((SkeletonBlock, SkeletonCard, SkeletonTable)):
            if hasattr(widget, "refresh_theme"):
                widget.refresh_theme()
