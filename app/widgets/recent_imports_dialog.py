"""Dialog to pick a recent Excel import (Fluent list when available)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.i18n import tr
from app.core.theme import card_stylesheet, theme_tokens
from app.services.file_history import FileHistoryEntry

try:
    from qfluentwidgets import (  # type: ignore[import-untyped]
        ListWidget as FluentListWidget,
        PrimaryPushButton,
        PushButton,
        SubtitleLabel,
    )
    _HAS_FLUENT = True
except ImportError:
    FluentListWidget = None  # type: ignore[assignment,misc]
    PrimaryPushButton = None  # type: ignore[assignment,misc]
    PushButton = None  # type: ignore[assignment,misc]
    SubtitleLabel = None  # type: ignore[assignment,misc]
    _HAS_FLUENT = False


class RecentImportsDialog(QDialog):
    def __init__(self, parent: QWidget | None, entries: list[FileHistoryEntry]) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("menu.file.recent"))
        self.setModal(True)
        self.setMinimumWidth(480)
        self._selected_session_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        if _HAS_FLUENT and SubtitleLabel is not None:
            title = SubtitleLabel(tr("menu.file.recent"))
        else:
            from PyQt6.QtWidgets import QLabel

            title = QLabel(tr("menu.file.recent"))
        layout.addWidget(title)

        if _HAS_FLUENT and FluentListWidget is not None:
            self._list = FluentListWidget(self)
        else:
            self._list = QListWidget(self)
        self._list.setMinimumHeight(240)
        for entry in entries:
            item = QListWidgetItem(entry.file_name)
            item.setToolTip(entry.path)
            item.setData(Qt.ItemDataRole.UserRole, entry.session_id)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)
        self._list.itemDoubleClicked.connect(self._accept_current)
        layout.addWidget(self._list, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        if _HAS_FLUENT and PushButton is not None and PrimaryPushButton is not None:
            cancel_btn = PushButton(tr("settings.cancel"), self)
            ok_btn = PrimaryPushButton(tr("settings.apply"), self)
        else:
            from PyQt6.QtWidgets import QPushButton

            cancel_btn = QPushButton(tr("settings.cancel"), self)
            ok_btn = QPushButton(tr("settings.apply"), self)
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self._accept_current)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(ok_btn)
        layout.addLayout(buttons)

        tokens = theme_tokens()
        self.setStyleSheet(card_stylesheet(tokens))

    def _accept_current(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if not session_id:
            return
        self._selected_session_id = str(session_id)
        self.accept()

    def selected_session_id(self) -> str | None:
        return self._selected_session_id


def pick_recent_import(parent: QWidget | None, entries: list[FileHistoryEntry]) -> str | None:
    """Show recent-import picker; return session id or None if cancelled."""
    if not entries:
        from app.widgets.dialog import info

        info(parent, tr("menu.file.recent"), tr("file.session.missing"))
        return None
    dialog = RecentImportsDialog(parent, entries)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.selected_session_id()
