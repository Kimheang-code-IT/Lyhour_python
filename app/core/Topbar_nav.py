"""Tab/title bar: menus, search input, toggle sidebar/preview; Fluent widgets when available."""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QShortcut, QKeySequence, QColor, QAction

from app.core.theme import (
    kbd_hint_stylesheet,
    search_field_stylesheet,
    theme_tokens,
    topbar_button_stylesheet,
    topbar_stylesheet,
)
from app.config.topbar_actions import TOPBAR_BUTTONS
from app.config.shortcuts import APP_SHORTCUTS
from app.core.i18n import tr
from app.core.search import SearchPalette
from app.services.app_settings import AppSettings

try:
    import qtawesome as qta  # type: ignore[import-untyped]
    _HAS_QTAWESOME = True
except ImportError:
    qta = None  # type: ignore[assignment]
    _HAS_QTAWESOME = False

try:
    from qfluentwidgets import (  # type: ignore[import-untyped]
        Action,
        FluentIcon,
        RoundMenu,
        Theme,
        TransparentPushButton,
        TransparentToolButton,
    )
    _HAS_FLUENT = True
except ImportError:
    Action = None  # type: ignore[assignment,misc]
    FluentIcon = None  # type: ignore[assignment,misc]
    RoundMenu = None  # type: ignore[assignment,misc]
    Theme = None  # type: ignore[assignment,misc]
    TransparentPushButton = None  # type: ignore[assignment,misc]
    TransparentToolButton = None  # type: ignore[assignment,misc]
    _HAS_FLUENT = False

_BTN_STYLE = ""


def _fluent_theme():
    if not _HAS_FLUENT:
        return None
    from app.core.theme import current_theme

    return Theme.LIGHT if current_theme() == "light" else Theme.DARK


def _icon_color() -> str:
    return theme_tokens().text_primary


def _icon_btn(icon: str, tooltip: str, size=32) -> QPushButton:
    fluent_theme = _fluent_theme()
    if _HAS_FLUENT and fluent_theme is not None:
        if icon == "\u2630":
            btn = TransparentToolButton(FluentIcon.MENU, parent=None)
        elif icon == "\u25A6":
            btn = TransparentToolButton(FluentIcon.VIEW, parent=None)
        else:
            btn = TransparentToolButton(FluentIcon.MENU, parent=None)
        btn.setFixedSize(size, 32)
        btn.setIconSize(QSize(20, 20))
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    btn = QPushButton()
    color = _icon_color()
    try:
        if _HAS_QTAWESOME and qta and icon == "\u2630":
            btn.setIcon(qta.icon("fa5s.bars", color=color))
        elif _HAS_QTAWESOME and qta and icon == "\u25A6":
            btn.setIcon(qta.icon("fa5s.columns", color=color))
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
    if _HAS_FLUENT:
        btn = TransparentPushButton(text)
        btn.setMinimumHeight(28)
        btn.setToolTip(tooltip or text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    btn = QPushButton(text)
    btn.setToolTip(tooltip or text)
    btn.setFlat(True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(_BTN_STYLE)
    btn.setMinimumHeight(28)
    return btn


class TopbarNav(QFrame):
    """Title bar: menus | centered search | toggle sidebar."""

    toggleSidebarRequested = pyqtSignal()
    togglePreviewRequested = pyqtSignal()
    settingsRequested = pyqtSignal()
    helpRequested = pyqtSignal()
    importExcelRequested = pyqtSignal()
    exportExcelRequested = pyqtSignal()
    exportPdfRequested = pyqtSignal()
    recentImportRequested = pyqtSignal(str)
    recentImportsDialogRequested = pyqtSignal()
    clearImportHistoryRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setObjectName("titleBar")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAutoFillBackground(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 2, 0)
        layout.setSpacing(0)

        left_container = QFrame()
        left_container.setObjectName("topbarLeft")
        left_container.setAutoFillBackground(False)
        left_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._build_toolbar_buttons(left_layout)
        layout.addWidget(left_container, 1)

        search_bar = QFrame()
        search_bar.setObjectName("centerSearchBar")
        search_bar.setFixedHeight(28)
        search_bar.setMinimumWidth(400)
        search_bar.setMaximumWidth(420)
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(10, 0, 10, 0)
        search_layout.setSpacing(6)
        search_icon = QLabel("\u2315")
        self._search_icon = search_icon
        search_layout.addWidget(search_icon)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("search.placeholder"))
        self.search_input.setClearButtonEnabled(False)
        self.search_input.setCursor(Qt.CursorShape.PointingHandCursor)
        search_layout.addWidget(self.search_input, 1)
        kbd_label = QLabel("Ctrl + K")
        kbd_label.setObjectName("searchShortcutHint")
        search_layout.addWidget(kbd_label)
        self._search_kbd_label = kbd_label
        shadow = QGraphicsDropShadowEffect(search_bar)
        shadow.setBlurRadius(6)
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(0, 0, 0, 50))
        search_bar.setGraphicsEffect(shadow)
        layout.addWidget(search_bar, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        right_container = QFrame()
        right_container.setObjectName("topbarRight")
        right_container.setAutoFillBackground(False)
        right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._search_palette: SearchPalette | None = None
        self.search_input.setReadOnly(True)
        self.search_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.search_input.mousePressEvent = lambda e: self._show_search_palette()

        self.toggle_sidebar_btn = _icon_btn("\u2630", tr("menu.view.toggle_sidebar"), size=36)
        self.toggle_sidebar_btn.clicked.connect(self.toggleSidebarRequested.emit)
        right_layout.addWidget(self.toggle_sidebar_btn)
        layout.addWidget(right_container, 1)

        self._shortcuts: dict[str, QShortcut] = {}
        self._search_bar = search_bar
        self.apply_theme()

    def apply_theme(self) -> None:
        tokens = theme_tokens()
        btn_style = topbar_button_stylesheet(tokens)
        self.setStyleSheet(topbar_stylesheet(tokens))
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(tokens.bg_panel))
        self.setPalette(palette)
        self._search_bar.setStyleSheet(
            f"#centerSearchBar {{"
            f"background-color: {tokens.bg_input};"
            f"border: 1px solid {tokens.border};"
            f"border-radius: 10px;"
            f"}}"
            f"#centerSearchBar:focus-within {{ border: 1px solid {tokens.border}; }}"
        )
        self.search_input.setStyleSheet(search_field_stylesheet(tokens))
        self._search_kbd_label.setStyleSheet(kbd_hint_stylesheet(tokens))
        self._search_icon.setStyleSheet(
            f"color: {tokens.text_muted}; font-size: 14px; background: transparent; border: none;"
        )
        for btn in self._toolbar_buttons.values():
            if not _HAS_FLUENT:
                btn.setStyleSheet(btn_style)
        if not _HAS_FLUENT:
            self.toggle_sidebar_btn.setStyleSheet(btn_style)
        color = tokens.text_primary
        fluent_theme = _fluent_theme()
        if not _HAS_FLUENT:
            try:
                if _HAS_QTAWESOME and qta:
                    self.toggle_sidebar_btn.setIcon(qta.icon("fa5s.bars", color=color))
            except Exception:
                pass
        if self._search_palette is not None:
            self._search_palette.apply_theme()

    def _shortcut_tooltip(self, label: str, shortcut: str | None) -> str:
        if not shortcut or not AppSettings.current().show_shortcut_hints:
            return label
        return f"{label} ({shortcut})"

    def _build_toolbar_buttons(self, layout: QHBoxLayout):
        self._file_actions: dict[str, QAction | Action] = {}
        self._toolbar_buttons: dict[str, QPushButton] = {}
        self._menus: dict[str, QMenu | RoundMenu] = {}

        btn_container = QFrame()
        btn_container.setObjectName("toolbarButtons")
        btn_container.setStyleSheet("#toolbarButtons { background: transparent; border: none; }")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 8, 0)
        btn_layout.setSpacing(2)

        for spec in TOPBAR_BUTTONS:
            label = tr(spec.label_key)
            tooltip = self._shortcut_tooltip(label, spec.shortcut)
            button = _toolbar_btn(label, tooltip)
            menu = self._build_menu(spec.menu or spec.id)
            self._menus[spec.id] = menu
            self._toolbar_buttons[spec.id] = button
            if spec.id == "file":
                self._file_menu_btn = button
                self._file_menu = menu
            button.clicked.connect(lambda checked=False, b=button: self._show_menu_for_button(b))
            btn_layout.addWidget(button)

        layout.addWidget(btn_container)

    def _build_menu(self, menu_id: str) -> QMenu | RoundMenu:
        if menu_id == "file":
            return self._build_file_menu() if _HAS_FLUENT else self._build_file_menu_qt_widget()
        if menu_id == "edit":
            return self._build_edit_menu() if _HAS_FLUENT else self._build_edit_menu_qt()
        if menu_id == "view":
            return self._build_view_menu() if _HAS_FLUENT else self._build_view_menu_qt()
        if menu_id == "settings":
            return self._build_settings_menu() if _HAS_FLUENT else self._build_settings_menu_qt()
        if menu_id == "help":
            return self._build_help_menu() if _HAS_FLUENT else self._build_help_menu_qt()
        return self._build_empty_menu_qt()

    def _build_empty_menu_qt(self) -> QMenu:
        return QMenu(self)

    def _build_file_menu_qt_widget(self) -> QMenu:
        menu = QMenu(self)
        self._build_file_menu_qt(menu)
        return menu

    def _build_edit_menu(self) -> RoundMenu:
        menu = RoundMenu(parent=self)
        action = Action(FluentIcon.SEARCH, tr("menu.edit.search"))
        action.setShortcut(QKeySequence("Ctrl+K"))
        action.triggered.connect(self._show_search_palette)
        menu.addAction(action)
        return menu

    def _build_edit_menu_qt(self) -> QMenu:
        menu = QMenu(self)
        action = QAction(tr("menu.edit.search"), menu)
        action.setShortcut(QKeySequence("Ctrl+K"))
        action.triggered.connect(self._show_search_palette)
        menu.addAction(action)
        return menu

    def _build_view_menu(self) -> RoundMenu:
        menu = RoundMenu(parent=self)
        sidebar = Action(FluentIcon.MENU, tr("menu.view.toggle_sidebar"))
        sidebar.setShortcut(QKeySequence("Ctrl+B"))
        sidebar.triggered.connect(self.toggleSidebarRequested.emit)
        preview = Action(FluentIcon.VIEW, tr("menu.view.toggle_preview"))
        preview.triggered.connect(self.togglePreviewRequested.emit)
        menu.addAction(sidebar)
        menu.addAction(preview)
        return menu

    def _build_view_menu_qt(self) -> QMenu:
        menu = QMenu(self)
        sidebar = QAction(tr("menu.view.toggle_sidebar"), menu)
        sidebar.setShortcut(QKeySequence("Ctrl+B"))
        sidebar.triggered.connect(self.toggleSidebarRequested.emit)
        preview = QAction(tr("menu.view.toggle_preview"), menu)
        preview.triggered.connect(self.togglePreviewRequested.emit)
        menu.addAction(sidebar)
        menu.addAction(preview)
        return menu

    def _build_settings_menu(self) -> RoundMenu:
        menu = RoundMenu(parent=self)
        action = Action(FluentIcon.SETTING, tr("menu.settings.open"))
        action.setShortcut(QKeySequence("Ctrl+,"))
        action.triggered.connect(self.settingsRequested.emit)
        menu.addAction(action)
        return menu

    def _build_settings_menu_qt(self) -> QMenu:
        menu = QMenu(self)
        action = QAction(tr("menu.settings.open"), menu)
        action.setShortcut(QKeySequence("Ctrl+,"))
        action.triggered.connect(self.settingsRequested.emit)
        menu.addAction(action)
        return menu

    def _build_help_menu(self) -> RoundMenu:
        menu = RoundMenu(parent=self)
        action = Action(FluentIcon.HELP, tr("menu.help.open"))
        action.setShortcut(QKeySequence("F1"))
        action.triggered.connect(self.helpRequested.emit)
        menu.addAction(action)
        return menu

    def _build_help_menu_qt(self) -> QMenu:
        menu = QMenu(self)
        action = QAction(tr("menu.help.open"), menu)
        action.setShortcut(QKeySequence("F1"))
        action.triggered.connect(self.helpRequested.emit)
        menu.addAction(action)
        return menu

    def _build_file_menu(self) -> RoundMenu:
        menu = RoundMenu(parent=self)
        self._file_actions.clear()
        items = [
            ("recent", FluentIcon.HISTORY, tr("menu.file.recent"), self.recentImportsDialogRequested.emit),
            ("clear_history", FluentIcon.DELETE, tr("menu.file.clear_history"), self.clearImportHistoryRequested.emit),
        ]
        for aid, icon, text, handler in items:
            action = Action(icon, text)
            action.triggered.connect(handler)
            menu.addAction(action)
            self._file_actions[aid] = action
        return menu

    def _build_file_menu_qt(self, menu: QMenu) -> None:
        self._file_actions.clear()
        items = [
            ("recent", tr("menu.file.recent"), self.recentImportsDialogRequested.emit),
            ("clear_history", tr("menu.file.clear_history"), self.clearImportHistoryRequested.emit),
        ]
        for aid, text, handler in items:
            action = QAction(text, menu)
            if handler is not None:
                action.triggered.connect(handler)
            menu.addAction(action)
            self._file_actions[aid] = action

    def _show_menu_for_button(self, button: QPushButton) -> None:
        menu = None
        for spec in TOPBAR_BUTTONS:
            toolbar_button = self._toolbar_buttons.get(spec.id)
            if toolbar_button is button:
                menu = self._menus.get(spec.id)
                break
        if menu is None:
            return

        pos = button.mapToGlobal(QPoint(0, button.height()))
        if _HAS_FLUENT and isinstance(menu, RoundMenu):
            if hasattr(menu, "view"):
                menu.view.setMinimumWidth(max(button.width(), 200))
                menu.view.adjustSize()
            menu.adjustSize()
        menu.popup(pos)

    def _rebuild_menus(self) -> None:
        for spec in TOPBAR_BUTTONS:
            menu_id = spec.menu or spec.id
            self._menus[spec.id] = self._build_menu(menu_id)
            if spec.id == "file":
                self._file_menu = self._menus[spec.id]

    def _rebuild_file_menu(self) -> None:
        self._rebuild_menus()

    def retranslate_ui(self) -> None:
        self.search_input.setPlaceholderText(tr("search.placeholder"))
        self.apply_shortcut_settings()
        for spec in TOPBAR_BUTTONS:
            btn = self._toolbar_buttons.get(spec.id)
            if btn is None:
                continue
            label = tr(spec.label_key)
            btn.setText(label)
            btn.setToolTip(self._shortcut_tooltip(label, spec.shortcut))
        self.toggle_sidebar_btn.setToolTip(
            self._shortcut_tooltip(tr("shortcuts.toggle_sidebar"), "Ctrl+B")
        )
        self._rebuild_file_menu()

    def apply_shortcut_settings(self) -> None:
        prefs = AppSettings.current()
        disabled = set(prefs.disabled_shortcuts)
        for shortcut_id, shortcut in self._shortcuts.items():
            shortcut.setEnabled(shortcut_id not in disabled)
        if hasattr(self, "_search_kbd_label"):
            self._search_kbd_label.setVisible(prefs.show_shortcut_hints)

    def _show_search_palette(self):
        if self._search_palette is None:
            self._search_palette = SearchPalette(self.window())
        self._search_palette.show_at_top(self)

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
        self.importExcelRequested.connect(main_window.import_excel_dialog)
        self.exportExcelRequested.connect(main_window.export_excel_summary_dialog)
        self.exportPdfRequested.connect(main_window.export_pdf)
        self.recentImportsDialogRequested.connect(main_window.open_recent_imports_dialog)
        self.recentImportRequested.connect(main_window.activate_excel_session)
        self.clearImportHistoryRequested.connect(main_window.clear_excel_history)

    def connect_shortcuts(self, main_window):
        self._shortcuts.clear()
        handlers = {
            "search": self._show_search_palette,
            "toggle_sidebar": main_window.toggle_sidebar,
            "settings": main_window.open_settings_dialog,
            "help": main_window.open_help_dialog,
        }
        for spec in APP_SHORTCUTS:
            if not spec.toggleable:
                continue
            handler = handlers.get(spec.id)
            if handler is None:
                continue
            shortcut = QShortcut(QKeySequence(spec.sequence), main_window, handler)
            self._shortcuts[spec.id] = shortcut
        self.apply_shortcut_settings()
