"""Dialog to pick or manage recent Excel imports (Fluent list when available)."""
from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.core.i18n import tr
from app.core.theme import card_stylesheet, theme_tokens
from app.services.file_history import FileHistoryEntry, format_recent_import_label

try:
    from qfluentwidgets import (  # type: ignore[import-untyped]
        FluentIcon,
        PrimaryPushButton,
        PushButton,
        SubtitleLabel,
        TransparentToolButton,
    )
    _HAS_FLUENT = True
except ImportError:
    FluentIcon = None  # type: ignore[assignment,misc]
    PrimaryPushButton = None  # type: ignore[assignment,misc]
    PushButton = None  # type: ignore[assignment,misc]
    SubtitleLabel = None  # type: ignore[assignment,misc]
    TransparentToolButton = None  # type: ignore[assignment,misc]
    _HAS_FLUENT = False


class _RecentImportRow(QFrame):
    """Single recent-import row with filename and remove control."""

    activated = pyqtSignal(str)
    remove_requested = pyqtSignal(str)

    def __init__(self, entry: FileHistoryEntry, *, selected: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session_id = entry.session_id
        self.setObjectName("recentImportRow")
        self.setProperty("selectedRow", selected)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(8)

        self._accent = QFrame(self)
        self._accent.setObjectName("recentImportAccent")
        self._accent.setFixedWidth(3)
        layout.addWidget(self._accent)

        self._label = QLabel(format_recent_import_label(entry), self)
        self._label.setToolTip(entry.path)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._label, 1)

        if _HAS_FLUENT and TransparentToolButton is not None and FluentIcon is not None:
            self._remove_btn = TransparentToolButton(FluentIcon.DELETE, parent=self)
            self._remove_btn.setFixedSize(28, 28)
            self._remove_btn.setIconSize(QSize(14, 14))
        else:
            self._remove_btn = QToolButton(self)
            self._remove_btn.setText("\u00d7")
            self._remove_btn.setFixedSize(28, 28)
        self._remove_btn.setToolTip(tr("file.recent.remove"))
        self._remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._remove_btn.clicked.connect(self._on_remove_clicked)
        layout.addWidget(self._remove_btn)

        self.set_selected(selected)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selectedRow", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.session_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def _on_remove_clicked(self) -> None:
        self.remove_requested.emit(self.session_id)


class RecentImportsDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        get_entries: Callable[[], list[FileHistoryEntry]],
        *,
        on_remove: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("menu.file.recent"))
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(360)
        self._get_entries = get_entries
        self._on_remove = on_remove
        self._selected_session_id: str | None = None
        self._row_widgets: dict[str, _RecentImportRow] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        if _HAS_FLUENT and SubtitleLabel is not None:
            title = SubtitleLabel(tr("menu.file.recent"))
        else:
            title = QLabel(tr("menu.file.recent"))
        layout.addWidget(title)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._rows_host = QWidget(self)
        self._rows_layout = QVBoxLayout(self._rows_host)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(6)
        self._rows_layout.addStretch()
        self._scroll.setWidget(self._rows_host)
        layout.addWidget(self._scroll, 1)

        self._empty_label = QLabel(tr("file.recent.empty"), self)
        self._empty_label.setWordWrap(True)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        if _HAS_FLUENT and PushButton is not None and PrimaryPushButton is not None:
            cancel_btn = PushButton(tr("settings.cancel"), self)
            self._apply_btn = PrimaryPushButton(tr("settings.apply"), self)
        else:
            from PyQt6.QtWidgets import QPushButton

            cancel_btn = QPushButton(tr("settings.cancel"), self)
            self._apply_btn = QPushButton(tr("settings.apply"), self)
        cancel_btn.clicked.connect(self.reject)
        self._apply_btn.clicked.connect(self._accept_current)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(self._apply_btn)
        layout.addLayout(buttons)

        tokens = theme_tokens()
        remove_selector = "TransparentToolButton" if _HAS_FLUENT else "QToolButton"
        self.setStyleSheet(
            card_stylesheet(tokens)
            + f"""
            #recentImportRow {{
                background-color: {tokens.bg_panel};
                border: 1px solid {tokens.border_subtle};
                border-radius: 8px;
                min-height: 44px;
            }}
            #recentImportRow:hover {{
                background-color: {tokens.hover};
            }}
            #recentImportRow[selectedRow="true"] {{
                background-color: {tokens.bg_window};
                border-color: {tokens.border};
            }}
            #recentImportAccent {{
                background: transparent;
                border: none;
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
            }}
            #recentImportRow[selectedRow="true"] #recentImportAccent {{
                background-color: {tokens.accent};
            }}
            #recentImportRow QLabel {{
                color: {tokens.text_primary};
                background: transparent;
                padding: 8px 0;
            }}
            #recentImportRow {remove_selector} {{
                color: {tokens.text_muted};
                border: none;
                background: transparent;
            }}
            #recentImportRow {remove_selector}:hover {{
                color: {tokens.text_primary};
                background-color: {tokens.pressed};
                border-radius: 6px;
            }}
            """
        )

        self._rebuild_rows()

    def _rebuild_rows(self) -> None:
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._row_widgets.clear()

        entries = self._get_entries()
        if not entries:
            self._selected_session_id = None
            self._empty_label.show()
            self._scroll.hide()
            self._apply_btn.setEnabled(False)
            return

        self._empty_label.hide()
        self._scroll.show()
        self._apply_btn.setEnabled(True)

        if self._selected_session_id not in {entry.session_id for entry in entries}:
            self._selected_session_id = entries[0].session_id

        for entry in entries:
            row = _RecentImportRow(
                entry,
                selected=entry.session_id == self._selected_session_id,
                parent=self._rows_host,
            )
            row.activated.connect(self._select_row)
            row.remove_requested.connect(self._remove_row)
            insert_index = max(0, self._rows_layout.count() - 1)
            self._rows_layout.insertWidget(insert_index, row)
            self._row_widgets[entry.session_id] = row

    def _select_row(self, session_id: str) -> None:
        self._selected_session_id = session_id
        for sid, row in self._row_widgets.items():
            row.set_selected(sid == session_id)

    def _remove_row(self, session_id: str) -> None:
        if self._on_remove is not None:
            self._on_remove(session_id)
        self._rebuild_rows()

    def _accept_current(self) -> None:
        if not self._selected_session_id:
            return
        self.accept()

    def selected_session_id(self) -> str | None:
        return self._selected_session_id


def pick_recent_import(
    parent: QWidget | None,
    get_entries: Callable[[], list[FileHistoryEntry]],
    *,
    on_remove: Callable[[str], None] | None = None,
) -> str | None:
    """Show recent-import picker; return session id or None if cancelled."""
    dialog = RecentImportsDialog(parent, get_entries, on_remove=on_remove)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.selected_session_id()
