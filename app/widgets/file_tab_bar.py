"""VS Code-style horizontal tabs for open Excel imports."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from app.core.theme import theme_tokens
from app.services.file_history import FileHistoryEntry

try:
    from qfluentwidgets import (  # type: ignore[import-untyped]
        BodyLabel,
        FluentIcon,
        TransparentToolButton,
    )
    _HAS_FLUENT = True
except ImportError:
    BodyLabel = None  # type: ignore[assignment,misc]
    FluentIcon = None  # type: ignore[assignment,misc]
    TransparentToolButton = None  # type: ignore[assignment,misc]
    _HAS_FLUENT = False


class _HorizontalTabScroll(QScrollArea):
    """Horizontal tab strip scroll without scrollbar arrow buttons."""

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta == 0:
            super().wheelEvent(event)
            return
        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() - delta)
        event.accept()


class _FileTab(QWidget):
    def __init__(self, entry: FileHistoryEntry, *, active: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session_id = entry.session_id
        self.entry = entry
        self.setObjectName("fileTabItem")
        self.setProperty("activeTab", active)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(4)

        if _HAS_FLUENT:
            self._label = BodyLabel(entry.file_name)
        else:
            self._label = QLabel(entry.file_name)
        self._label.setToolTip(entry.path)
        self._label.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._label)

        if _HAS_FLUENT:
            self._close = TransparentToolButton(FluentIcon.CLOSE, parent=self)
            self._close.setFixedSize(18, 18)
            self._close.setIconSize(QSize(12, 12))
        else:
            self._close = QToolButton()
            self._close.setText("\u00d7")
            self._close.setFixedSize(18, 18)
        self._close.setToolTip("Close")
        self._close.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._close)

        self.set_active(active)

    def set_active(self, active: bool) -> None:
        self.setProperty("activeTab", active)
        self.style().unpolish(self)
        self.style().polish(self)


class FileTabBar(QFrame):
    """Scrollable tab strip for temporary Excel sessions."""

    tabActivated = pyqtSignal(str)
    tabClosed = pyqtSignal(str)
    importRequested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fileTabBar")
        self.setFixedHeight(32)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(4, 0, 4, 0)
        outer.setSpacing(4)

        if _HAS_FLUENT:
            self._import_btn = TransparentToolButton(FluentIcon.FOLDER_ADD, parent=self)
            self._import_btn.setFixedSize(28, 28)
            self._import_btn.setIconSize(QSize(16, 16))
        else:
            self._import_btn = QPushButton("+")
            self._import_btn.setFixedSize(28, 28)
            self._import_btn.setObjectName("fileTabImport")
        self._import_btn.setToolTip("Import Excel")
        self._import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._import_btn.clicked.connect(self.importRequested.emit)
        outer.addWidget(self._import_btn)

        self._scroll = _HorizontalTabScroll(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setMaximumHeight(32)

        self._tab_host = QWidget()
        self._tab_layout = QHBoxLayout(self._tab_host)
        self._tab_layout.setContentsMargins(0, 0, 0, 0)
        self._tab_layout.setSpacing(0)
        self._tab_layout.addStretch()
        self._scroll.setWidget(self._tab_host)
        outer.addWidget(self._scroll, 1)

        self._tabs: dict[str, _FileTab] = {}
        self._active_session: str | None = None
        self.apply_theme()

    def apply_theme(self) -> None:
        tokens = theme_tokens()
        label_selector = "BodyLabel" if _HAS_FLUENT else "QLabel"
        close_selector = "TransparentToolButton" if _HAS_FLUENT else "QToolButton"
        import_selector = "TransparentToolButton" if _HAS_FLUENT else "QPushButton"
        self.setStyleSheet(
            f"""
            #fileTabBar {{
                background-color: {tokens.bg_panel};
                border-bottom: 1px solid {tokens.border};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            #fileTabItem {{
                background: transparent;
                border-right: 1px solid {tokens.border_subtle};
                min-height: 28px;
                max-height: 28px;
            }}
            #fileTabItem:hover {{
                background-color: {tokens.hover};
            }}
            #fileTabItem[activeTab="true"] {{
                background-color: {tokens.bg_window};
                border-top: 2px solid {tokens.accent};
            }}
            #fileTabItem {label_selector} {{
                color: {tokens.text_muted};
                font-size: 12px;
                background: transparent;
            }}
            #fileTabItem[activeTab="true"] {label_selector} {{
                color: {tokens.text_primary};
            }}
            #fileTabItem {close_selector} {{
                color: {tokens.text_muted};
                border: none;
                background: transparent;
                font-size: 12px;
            }}
            #fileTabItem {close_selector}:hover {{
                color: {tokens.text_primary};
                background-color: {tokens.pressed};
                border-radius: 3px;
            }}
            {import_selector}#fileTabImport {{
                color: {tokens.text_primary};
                border: 1px solid {tokens.border};
                border-radius: 4px;
                font-weight: bold;
                background: transparent;
            }}
            {import_selector}#fileTabImport:hover {{
                background-color: {tokens.hover};
            }}
            """
        )
        if not _HAS_FLUENT:
            self._import_btn.setObjectName("fileTabImport")

    def set_tabs(self, entries: list[FileHistoryEntry], *, active_session_id: str | None) -> None:
        self._active_session = active_session_id
        while self._tab_layout.count() > 1:
            item = self._tab_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._tabs.clear()

        for entry in entries:
            tab = _FileTab(entry, active=entry.session_id == active_session_id)
            tab._label.mousePressEvent = lambda e, sid=entry.session_id: self.tabActivated.emit(sid)
            tab._close.clicked.connect(lambda checked=False, sid=entry.session_id: self.tabClosed.emit(sid))
            self._tab_layout.insertWidget(self._tab_layout.count() - 1, tab)
            self._tabs[entry.session_id] = tab

        self.setVisible(bool(entries))

    def set_active(self, session_id: str | None) -> None:
        self._active_session = session_id
        for sid, tab in self._tabs.items():
            tab.set_active(sid == session_id)
