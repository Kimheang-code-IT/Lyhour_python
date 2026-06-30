"""Tab/title bar: menus, search input, toggle sidebar/preview; qtawesome icons when available."""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QShortcut, QKeySequence, QColor, QIcon, QAction

from app.config.topbar_actions import OTHER_BUTTONS
from app.core.search import SearchPalette

try:
    import qtawesome as qta  # type: ignore[import-untyped]
    _HAS_QTAWESOME = True
except ImportError:
    qta = None  # type: ignore[assignment]
    _HAS_QTAWESOME = False

try:
    from qfluentwidgets import FluentIcon, Theme  # type: ignore[import-untyped]
    _HAS_FLUENT_ICON = True
except ImportError:
    _HAS_FLUENT_ICON = False

_BTN_STYLE = """
    QPushButton { background-color: transparent; color: #ffffff; font-size: 13px; border: none; border-radius: 4px; outline: none; padding: 4px 10px; }
    QPushButton:hover { background-color: #3e3e40; color: #ffffff; }
    QPushButton:pressed { background-color: #505050; color: #ffffff; }
"""


def _icon_btn(icon: str, tooltip: str, size=32) -> QPushButton:
    btn = QPushButton()
    try:
        if _HAS_QTAWESOME and qta and icon == "\u2630":
            btn.setIcon(qta.icon("fa5s.bars", color="#ffffff"))
        elif _HAS_QTAWESOME and qta and icon == "\u25A6":
            btn.setIcon(qta.icon("fa5s.columns", color="#ffffff"))
        elif _HAS_FLUENT_ICON and icon == "\u2630":
            btn.setIcon(FluentIcon.MENU.icon(theme=Theme.DARK))
        elif _HAS_FLUENT_ICON and icon == "\u25A6":
            btn.setIcon(FluentIcon.VIEW.icon(theme=Theme.DARK))
        else:
            btn.setText(icon)
    except Exception:
        btn.setText(icon)
    btn.setMinimumSize(size, 32)
    btn.setMaximumSize(size, 32)
    btn.setIconSize(QSize(20, 20))
    btn.setToolTip(tooltip)
    btn.setFlat(True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(_BTN_STYLE)
    return btn


def _toolbar_btn(text: str, tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    btn.setToolTip(tooltip or text)
    btn.setFlat(True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(_BTN_STYLE)
    btn.setMinimumHeight(28)
    return btn


class TopbarNav(QFrame):
    """Title bar: menus | centered search | toggle sidebar | toggle preview."""

    toggleSidebarRequested = pyqtSignal()
    togglePreviewRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setObjectName("titleBar")
        self.setStyleSheet("#titleBar { background-color: #252526; border: none; border-bottom: 1px solid #3e3e40; border-radius: 0; outline: none; outline-color: transparent; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 2, 0)
        layout.setSpacing(0)

        self._build_toolbar_buttons(layout)

        self.title_container = QFrame()
        self.title_container.setObjectName("titleContainer")
        self.title_container.setStyleSheet("#titleContainer { background-color: transparent; margin-right: 100px; min-width: 120px; border: none; outline: none; outline-color: transparent; }")
        self.title_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        title_inner = QHBoxLayout(self.title_container)
        title_inner.setContentsMargins(0, 4, 0, 4)
        title_inner.setSpacing(10)
        search_bar = QFrame()
        search_bar.setObjectName("centerSearchBar")
        search_bar.setFixedHeight(28)
        search_bar.setMinimumWidth(400)
        search_bar.setMaximumWidth(420)
        search_bar.setStyleSheet("""
            #centerSearchBar { border: 1px solid #3e3e40; border-radius: 10px; outline: none; outline-color: transparent; }
            #centerSearchBar:focus-within { border: 1px solid #3e3e40; }
        """)    
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(10, 0, 10, 0)
        search_layout.setSpacing(6)
        search_icon = QLabel("\u2315")
        search_icon.setStyleSheet("color: #888; font-size: 14px; background: transparent; border: none;")
        search_layout.addWidget(search_icon)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setClearButtonEnabled(False)
        self.search_input.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_input.setStyleSheet("QLineEdit { background: transparent; color: #cccccc; border: none; padding: 2px 0; font-size: 13px; selection-background-color: #3e3e40; outline: none; outline-color: transparent; } QLineEdit::placeholder { color: #888; }")
        search_layout.addWidget(self.search_input, 1)
        # Add kbd-style label for Ctrl + K
        kbd_label = QLabel("Ctrl + K")
        kbd_label.setStyleSheet("QLabel { background: #222; color: #aaa; border-radius: 4px; border: 1px solid #444; font-size: 10px; margin-left: 8px; font-family: 'Consolas', 'monospace'; padding: 0px 5px 0px 5px; min-height: 16px; max-height: 18px; }")
        search_layout.addWidget(kbd_label)
        shadow = QGraphicsDropShadowEffect(search_bar)
        shadow.setBlurRadius(6)
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(0, 0, 0, 50))
        search_bar.setGraphicsEffect(shadow)
        title_inner.addStretch(1)
        title_inner.addWidget(search_bar)
        title_inner.addStretch(1)
        layout.addWidget(self.title_container, 1)

        self._search_palette: SearchPalette | None = None
        self.search_input.setReadOnly(True)
        self.search_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.search_input.mousePressEvent = lambda e: self._show_search_palette()

        self.toggle_sidebar_btn = _icon_btn("\u2630", "Toggle Primary Side Bar (Ctrl+B)", size=36)
        self.toggle_sidebar_btn.clicked.connect(self.toggleSidebarRequested.emit)
        self.toggle_preview_btn = _icon_btn("\u25A6", "Toggle Preview", size=36)
        self.toggle_preview_btn.clicked.connect(self.togglePreviewRequested.emit)
        layout.addWidget(self.toggle_sidebar_btn)
        layout.addWidget(self.toggle_preview_btn)

    def _build_toolbar_buttons(self, layout: QHBoxLayout):
        self._file_actions: dict[str, QAction] = {}
        

        btn_container = QFrame()
        btn_container.setObjectName("toolbarButtons")
        btn_container.setStyleSheet("#toolbarButtons { background: transparent; border: none; }")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 8, 0)
        btn_layout.setSpacing(2)

        def add_btn(action: QAction):
            b = _toolbar_btn(action.text(), action.toolTip())
            b.clicked.connect(action.trigger)
            btn_layout.addWidget(b)


        for name in OTHER_BUTTONS:
            b = _toolbar_btn(name, f"{name} placeholder")
            btn_layout.addWidget(b)

        layout.addWidget(btn_container)

    def _show_search_palette(self):
        if self._search_palette is None:
            self._search_palette = SearchPalette(self.window())
        self._search_palette.show_at_top(self.title_container)

    def connect_search_palette(self, main_window: QWidget):
        """Connect search palette pageSelected so clicking a page navigates to it."""
        if self._search_palette is None:
            self._search_palette = SearchPalette(self.window())
        def go_to_page(index: int):
            if hasattr(main_window, "_on_page_changed"):
                main_window._on_page_changed(index)
            if hasattr(main_window, "nav") and hasattr(main_window.nav, "set_current_index"):
                main_window.nav.set_current_index(index)
        self._search_palette.pageSelected.connect(go_to_page)

    def connect_window(self, window: QWidget):
        pass

    def connect_file_actions(self, main_window):
        _id_to_method = {
            "new": "new_document",
            "open": "open_document",
            "save": "save_document",
            "save_as": "save_document_as",
            "export_pdf": "export_pdf",
            "exit": "close",
        }
        for aid, method_name in _id_to_method.items():
            if aid in self._file_actions and hasattr(main_window, method_name):
                self._file_actions[aid].triggered.connect(getattr(main_window, method_name))

    def connect_shortcuts(self, main_window):
        QShortcut(QKeySequence("Ctrl+K"), main_window, self._show_search_palette)
        QShortcut(QKeySequence("Ctrl+B"), main_window, main_window.toggle_sidebar)
