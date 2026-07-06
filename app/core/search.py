"""
Search palette (Fluent upgrade)
- Fluent LineEdit + ListWidget when available
- Better layout: header + search + list
- Keyboard: Up/Down, Enter, Esc
- Filtering: keeps first visible selected
- Same show_at_top() behavior
"""

from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QGraphicsDropShadowEffect,
    QApplication,
    QWidget,
    QStyle,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QKeyEvent, QColor, QIcon

from app.core.i18n import nav_label, tr
from app.core.page_registry import SEARCH_PAGES as _REGISTRY_SEARCH_PAGES
from app.core.theme import shell_stylesheet, theme_tokens

# (page_route_key, section_route_key, page_index)
SEARCH_PAGES = [
    (entry.route_key, entry.section_route_key, entry.index)
    for entry in _REGISTRY_SEARCH_PAGES
]

# Fluent widgets (safe fallback)
try:
    from qfluentwidgets import LineEdit as FluentLineEdit
    from qfluentwidgets import ListWidget as FluentListWidget
    from qfluentwidgets import FluentIcon, Theme

    _HAS_FLUENT = True
except Exception:
    FluentLineEdit = None  # type: ignore[assignment]
    FluentListWidget = None  # type: ignore[assignment]
    FluentIcon = None  # type: ignore[assignment]
    Theme = None  # type: ignore[assignment]
    _HAS_FLUENT = False


class SearchPalette(QFrame):
    """Popup: search input + pages only. Location: top-0."""

    pageSelected = pyqtSignal(int)  # page index

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setObjectName("searchPalette")

        self.setMinimumWidth(560)
        self.setMinimumHeight(340)
        self.setMaximumHeight(380)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setXOffset(0)
        shadow.setYOffset(18)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)

        app = QApplication.instance()
        style = app.style() if app else None

        # Icons
        icon_file = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon) if style else QIcon()
        icon_search = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView) if style else QIcon()
        if _HAS_FLUENT and FluentIcon is not None:
            try:
                icon_search = FluentIcon.SEARCH.icon(theme=Theme.DARK)
                icon_file = FluentIcon.DOCUMENT.icon(theme=Theme.DARK)
            except Exception:
                pass

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header row
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)

        title = QLabel(tr("search.palette_title"))
        title.setObjectName("paletteTitle")
        self._title_label = title

        hint = QLabel(tr("search.palette_hint"))
        hint.setObjectName("paletteHint")
        self._hint_label = hint
        hint.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(hint)
        layout.addLayout(header)

        # Search input (Fluent if available)
        if _HAS_FLUENT and FluentLineEdit is not None:
            self.search_edit = FluentLineEdit()
            try:
                self.search_edit.setPrefixIcon(icon_search)
            except Exception:
                pass
        else:
            self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("search.placeholder"))
        try:
            self.search_edit.setClearButtonEnabled(True)
        except Exception:
            pass
        layout.addWidget(self.search_edit)

        # List (Fluent if available)
        if _HAS_FLUENT and FluentListWidget is not None:
            self.page_list = FluentListWidget()
        else:
            self.page_list = QListWidget()

        self.page_list.setObjectName("pageList")
        self.page_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._populate_page_list(icon_file)

        layout.addWidget(self.page_list, 1)

        # Signals
        self.search_edit.textChanged.connect(self._filter_pages)
        self.page_list.itemActivated.connect(self._on_page_activated)

        if self.page_list.count() > 0:
            self.page_list.setCurrentRow(0)
        self.apply_theme()

    def apply_theme(self) -> None:
        tokens = theme_tokens()
        extra = f"""
            QLabel#paletteTitle {{ font-size: 14px; font-weight: 600; }}
            QLabel#paletteHint {{ font-size: 12px; }}
            #searchPalette QLineEdit {{
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
            }}
            #searchPalette QLineEdit:focus {{
                border: 1px solid {tokens.selection_bg};
            }}
            #searchPalette QListWidget::item {{
                padding: 4px 6px;
                border-radius: 8px;
            }}
        """
        self.setStyleSheet(shell_stylesheet(tokens) + extra)

    def _page_list_label(self, route_key: str, section_route_key: str) -> str:
        name = nav_label(route_key)
        section = nav_label(section_route_key)
        return f"{name}    ·    {section}"

    def _populate_page_list(self, icon: QIcon) -> None:
        self.page_list.clear()
        for route_key, section_route_key, idx in SEARCH_PAGES:
            label = self._page_list_label(route_key, section_route_key)
            item = QListWidgetItem(icon, label)
            item.setData(
                Qt.ItemDataRole.UserRole,
                ("page", idx, route_key, section_route_key),
            )
            self.page_list.addItem(item)

    def retranslate_ui(self) -> None:
        self.apply_theme()
        self._title_label.setText(tr("search.palette_title"))
        self._hint_label.setText(tr("search.palette_hint"))
        self.search_edit.setPlaceholderText(tr("search.placeholder"))
        for i in range(self.page_list.count()):
            item = self.page_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data:
                continue
            _, _idx, route_key, section_route_key = data
            item.setText(self._page_list_label(route_key, section_route_key))

    def _first_visible_row(self) -> int:
        for i in range(self.page_list.count()):
            if not self.page_list.item(i).isHidden():
                return i
        return -1

    def _filter_pages(self, text: str):
        q = text.strip().lower()

        for i in range(self.page_list.count()):
            item = self.page_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data:
                continue
            _, _idx, route_key, section_route_key = data
            name = nav_label(route_key)
            section = nav_label(section_route_key)
            match = (not q) or (q in name.lower()) or (q in section.lower())
            item.setHidden(not match)

        # keep selection on a visible item
        row = self._first_visible_row()
        if row >= 0:
            self.page_list.setCurrentRow(row)

    def _on_page_activated(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and data[0] == "page":
            self.pageSelected.emit(int(data[1]))
        self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cur = self.page_list.currentItem()
            if cur and not cur.isHidden():
                self._on_page_activated(cur)
                return

            # if current hidden, open first visible
            row = self._first_visible_row()
            if row >= 0:
                self._on_page_activated(self.page_list.item(row))
                return

        if key == Qt.Key.Key_Escape:
            self.hide()
            return

        # Up/Down skips hidden items
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            step = -1 if key == Qt.Key.Key_Up else 1
            r = self.page_list.currentRow()
            if r < 0:
                r = 0
            n = self.page_list.count()

            for _ in range(n):
                r = (r + step) % n
                if not self.page_list.item(r).isHidden():
                    self.page_list.setCurrentRow(r)
                    break
            return

        super().keyPressEvent(event)

    def _topbar_widget(self, anchor: QWidget) -> QWidget | None:
        widget = anchor
        while widget is not None:
            if widget.objectName() == "titleBar":
                return widget
            widget = widget.parentWidget()
        return None

    def show_at_top(self, anchor: QWidget):
        """Show palette centered on the navbar, directly below it."""
        topbar = self._topbar_widget(anchor)
        if topbar is not None:
            origin = topbar.mapToGlobal(QPoint(0, 0))
            x = origin.x() + max(0, (topbar.width() - self.width()) // 2)
            y = origin.y() + topbar.height()
            self.setGeometry(x, y, self.width(), self.height())
        else:
            win = anchor.window()
            if win is None:
                return
            geometry = win.geometry()
            x = geometry.x() + max(0, (geometry.width() - self.width()) // 2)
            y = geometry.y()
            self.setGeometry(x, y, self.width(), self.height())

        self.show()
        self.raise_()
        self.activateWindow()
        self.search_edit.setFocus()
        self.search_edit.clear()