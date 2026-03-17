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
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QColor, QIcon

# Pages: (display_name, section_name, page_index) — same order as sidebar
SEARCH_PAGES = [
    ("Input", "Traffic Analysis", 0),
    ("Detail Result", "Traffic Analysis", 1),
    ("Horizontal Curvature", "Road Geometry Design", 2),
    ("Superelevation Design", "Road Geometry Design", 3),
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

    pageSelected = pyqtSignal(int)  # page index (0..3)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setObjectName("searchPalette")

        self.setMinimumWidth(560)
        self.setMinimumHeight(340)
        self.setMaximumHeight(380)

        self.setStyleSheet("""
            #searchPalette {
                background-color: #252526;
                border: 1px solid #3e3e40;
                border-radius: 10px;
            }

            /* Header */
            QLabel#paletteTitle {
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#paletteHint {
                color: #9aa0a6;
                font-size: 12px;
            }

            /* Qt fallback widgets */
            QLineEdit {
                background-color: #3c3c3c;
                color: #e6e6e6;
                border: 1px solid #3e3e40;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                selection-background-color: #094771;
            }
            QLineEdit:focus {
                border: 1px solid #094771;
            }
            QLineEdit::placeholder { color: #888; }

            QListWidget {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                outline: none;
                padding: 6px;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 8px;
            }
            QListWidget::item:hover { background-color: #2a2d2e; }
            QListWidget::item:selected { background-color: #094771; color: #ffffff; }
        """)

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

        title = QLabel("Search")
        title.setObjectName("paletteTitle")

        hint = QLabel("Enter: open   Esc: close")
        hint.setObjectName("paletteHint")
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
        self.search_edit.setPlaceholderText("Search pages...")
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

        # Add items
        for name, section, idx in SEARCH_PAGES:
            item = QListWidgetItem(icon_file, f"{name}    ·    {section}")
            item.setData(Qt.ItemDataRole.UserRole, ("page", idx, name, section))
            self.page_list.addItem(item)

        layout.addWidget(self.page_list, 1)

        # Signals
        self.search_edit.textChanged.connect(self._filter_pages)
        self.page_list.itemActivated.connect(self._on_page_activated)

        if self.page_list.count() > 0:
            self.page_list.setCurrentRow(0)

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
            _, _idx, name, section = data
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

    def show_at_top(self, anchor: QWidget):
        """Show palette at top-0 of window, centered horizontally."""
        win = anchor.window()
        if not win:
            return

        gw = win.geometry()
        x = gw.x() + max(0, (gw.width() - self.width()) // 2)
        y = gw.y() + 0

        self.setGeometry(x, y, self.width(), self.height())
        self.show()
        self.raise_()
        self.activateWindow()
        self.search_edit.setFocus()
        self.search_edit.clear()