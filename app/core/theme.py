"""Theme: dark and light palettes, tokens, and stylesheets."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QWidget

_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "icon"
_ARROW_DOWN_ASSET = _ASSETS / "arrow-down.png"


@dataclass(frozen=True)
class ThemeTokens:
    theme: str
    accent: str
    bg_window: str
    bg_panel: str
    bg_card: str
    bg_card_header: str
    bg_input: str
    bg_preview: str
    text_primary: str
    text_muted: str
    text_on_accent: str
    border: str
    border_subtle: str
    hover: str
    pressed: str
    splitter_handle: str
    nav_bg: str
    nav_text: str
    nav_header: str
    table_bg: str
    table_header: str
    table_grid: str
    selection_bg: str
    selection_text: str
    chart_axis: str
    chart_grid: str
    chart_label: str
    chart_value: str
    kbd_bg: str
    kbd_text: str
    kbd_border: str
    scrollbar_bg: str
    scrollbar_handle: str
    tooltip_bg: str
    tooltip_text: str
    disabled_text: str


def current_theme() -> str:
    from app.services.app_settings import AppSettings

    return AppSettings.current().theme


def theme_tokens(theme: str | None = None, accent: str | None = None) -> ThemeTokens:
    from app.services.app_settings import AppSettings

    prefs = AppSettings.current()
    resolved_theme = theme if theme in ("dark", "light") else prefs.theme
    resolved_accent = accent or prefs.accent_color or "#0078D4"
    if resolved_theme == "light":
        return ThemeTokens(
            theme="light",
            accent=resolved_accent,
            bg_window="#f5f5f5",
            bg_panel="#ffffff",
            bg_card="#ffffff",
            bg_card_header="#f0f0f0",
            bg_input="#ffffff",
            bg_preview="#e8e8e8",
            text_primary="#1e1e1e",
            text_muted="#6e6e6e",
            text_on_accent="#ffffff",
            border="#dcdcdc",
            border_subtle="#e8e8e8",
            hover="#efefef",
            pressed="#e0e0e0",
            splitter_handle="#dcdcdc",
            nav_bg="#fafafa",
            nav_text="#1e1e1e",
            nav_header="#6e6e6e",
            table_bg="#ffffff",
            table_header="#f0f0f0",
            table_grid="#dcdcdc",
            selection_bg=resolved_accent,
            selection_text="#ffffff",
            chart_axis="#606060",
            chart_grid="#e0e0e0",
            chart_label="#1e1e1e",
            chart_value="#6e6e6e",
            kbd_bg="#f0f0f0",
            kbd_text="#6e6e6e",
            kbd_border="#dcdcdc",
            scrollbar_bg="#f0f0f0",
            scrollbar_handle="#c8c8c8",
            tooltip_bg="#ffffff",
            tooltip_text="#1e1e1e",
            disabled_text="#a0a0a0",
        )
    return ThemeTokens(
        theme="dark",
        accent=resolved_accent,
        bg_window="#2d2d30",
        bg_panel="#252526",
        bg_card="#2d2d30",
        bg_card_header="#333333",
        bg_input="#3e3e40",
        bg_preview="#1e1e1e",
        text_primary="#ffffff",
        text_muted="#cccccc",
        text_on_accent="#ffffff",
        border="#3e3e40",
        border_subtle="#3a3a3d",
        hover="#3e3e40",
        pressed="#505050",
        splitter_handle="#3e3e40",
        nav_bg="#2d2d30",
        nav_text="#ffffff",
        nav_header="#b5bac8",
        table_bg="#2d2d30",
        table_header="#333333",
        table_grid="#3e3e40",
        selection_bg="#094771",
        selection_text="#ffffff",
        chart_axis="#606060",
        chart_grid="#444444",
        chart_label="#ffffff",
        chart_value="#cccccc",
        kbd_bg="#222222",
        kbd_text="#aaaaaa",
        kbd_border="#444444",
        scrollbar_bg="#2d2d30",
        scrollbar_handle="#505050",
        tooltip_bg="#3e3e40",
        tooltip_text="#ffffff",
        disabled_text="#888888",
    )


def _qcolor(hex_color: str) -> QColor:
    return QColor(hex_color)


def get_palette(theme: str = "dark") -> QPalette:
    """Return palette for ``dark`` or ``light`` theme."""
    t = theme_tokens(theme)
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, _qcolor(t.bg_window))
    p.setColor(QPalette.ColorRole.WindowText, _qcolor(t.text_primary))
    p.setColor(QPalette.ColorRole.Base, _qcolor(t.bg_input))
    p.setColor(QPalette.ColorRole.AlternateBase, _qcolor(t.bg_window))
    p.setColor(QPalette.ColorRole.Button, _qcolor(t.bg_input))
    p.setColor(QPalette.ColorRole.ButtonText, _qcolor(t.text_primary))
    p.setColor(QPalette.ColorRole.Text, _qcolor(t.text_primary))
    p.setColor(QPalette.ColorRole.PlaceholderText, _qcolor(t.text_muted))
    p.setColor(QPalette.ColorRole.Highlight, _qcolor(t.selection_bg))
    p.setColor(QPalette.ColorRole.HighlightedText, _qcolor(t.selection_text))
    if theme != "light":
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, _qcolor(t.disabled_text))
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, _qcolor(t.disabled_text))
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, _qcolor(t.disabled_text))
    return p


def _combo_arrow_css() -> str:
    if not _ARROW_DOWN_ASSET.exists():
        return ""
    try:
        arrow_uri = _ARROW_DOWN_ASSET.resolve().as_uri()
    except Exception:
        arrow_uri = _ARROW_DOWN_ASSET.as_uri()
    return f"""
    QComboBox::down-arrow {{
        image: url({arrow_uri});
        width: 16px;
        height: 16px;
    }}
    """


def card_stylesheet(tokens: ThemeTokens) -> str:
    return f"""
    #resultCard {{
        background-color: {tokens.bg_card};
        border: 1px solid {tokens.border};
        border-radius: 6px;
    }}
    #resultDescriptionNote {{
        border: 1px solid {tokens.border};
        border-radius: 6px;
        background-color: {tokens.bg_panel};
    }}
    #settingsSectionFrame {{
        background-color: transparent;
        border: 1px solid {tokens.border};
        border-radius: 6px;
    }}
    """


def table_stylesheet(tokens: ThemeTokens) -> str:
    return f"""
    QTableWidget {{
        background-color: {tokens.table_bg};
        color: {tokens.text_primary};
        gridline-color: {tokens.table_grid};
        border: 1px solid {tokens.border};
        border-radius: 4px;
    }}
    QTableWidget::item {{
        padding: 4px 8px;
        color: {tokens.text_primary};
    }}
    QTableWidget::item:selected {{
        background-color: {tokens.selection_bg};
        color: {tokens.selection_text};
    }}
    QHeaderView::section {{
        background-color: {tokens.table_header};
        color: {tokens.text_primary};
        border: none;
        border-bottom: 1px solid {tokens.border};
        padding: 6px 8px;
        font-weight: 600;
    }}
    """


def topbar_stylesheet(tokens: ThemeTokens) -> str:
  """Single full-width background for the application top bar."""
  return f"""
    #titleBar {{
        background-color: {tokens.bg_panel};
        border: none;
        border-bottom: 1px solid {tokens.border};
    }}
    #titleBar #topbarLeft,
    #titleBar #topbarRight,
    #titleBar #toolbarButtons {{
        background-color: transparent;
        border: none;
    }}
    """


def shell_stylesheet(tokens: ThemeTokens) -> str:
    return f"""
    #titleBar {{
        background-color: {tokens.bg_panel};
        border: none;
        border-bottom: 1px solid {tokens.border};
    }}
    #titleContainer, #toolbarButtons, #topbarLeft, #topbarRight {{
        background-color: transparent;
        border: none;
    }}
    #centerSearchBar {{
        background-color: {tokens.bg_input};
        border: 1px solid {tokens.border};
        border-radius: 10px;
    }}
    #navPanel {{
        background-color: {tokens.nav_bg};
        border: none;
        border-right: 1px solid {tokens.border_subtle};
    }}
    NavigationInterface, NavigationPanel {{
        background-color: {tokens.nav_bg};
        border: none;
    }}
    NavigationItemHeader {{
        color: {tokens.nav_header};
        font-size: 11px;
        font-weight: 500;
    }}
    NavigationTreeWidget, NavigationTreeItem, NavigationToolButton {{
        color: {tokens.nav_text};
        background-color: transparent;
        border: none;
        border-radius: 4px;
        min-height: 36px;
        max-height: 36px;
        font-size: 14px;
    }}
    #previewPanel {{
        background-color: {tokens.bg_panel};
        border: none;
    }}
    #quickResultsCard {{
        background-color: {tokens.bg_card};
        border: none;
    }}
    #quickResultsCard #cardTitle {{
        font-weight: bold;
        font-size: 15px;
        color: {tokens.text_primary};
        padding: 14px 16px;
        background-color: {tokens.bg_card_header};
        border: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    #quickResultsCard QLabel {{
        padding: 10px 16px;
        color: {tokens.text_muted};
        font-size: 16px;
        border: none;
    }}
    #previewImage {{
        background-color: {tokens.bg_preview};
    }}
    #quickPanel {{
        background-color: {tokens.bg_card};
        border: none;
    }}
    #quickPanel QLabel {{
        background-color: {tokens.bg_card};
        color: {tokens.text_muted};
        font-size: 14px;
        border: none;
        padding: 8px 12px;
    }}
    QLabel#quickPanelTitle {{
        background-color: {tokens.bg_card_header};
        color: {tokens.text_primary};
        font-size: 14px;
        font-weight: bold;
        padding: 12px;
        border: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    #searchPalette {{
        background-color: {tokens.bg_card};
        border: 1px solid {tokens.border};
        border-radius: 7px;
        color: {tokens.text_primary};
    }}
    QLabel#paletteTitle {{
        color: {tokens.text_primary};
    }}
    QLabel#paletteHint {{
        color: {tokens.text_muted};
    }}
    #searchPalette QLineEdit {{
        background-color: {tokens.bg_input};
        color: {tokens.text_primary};
        border: 1px solid {tokens.border};
        border-radius: 8px;
    }}
    #searchPalette QListWidget {{
        background-color: transparent;
        color: {tokens.text_primary};
        border: none;
    }}
    #searchPalette QListWidget::item:hover {{
        background-color: {tokens.hover};
    }}
    #searchPalette QListWidget::item:selected {{
        background-color: {tokens.selection_bg};
        color: {tokens.selection_text};
    }}
    #centerStack {{
        background-color: {tokens.bg_window};
    }}
    QSplitter::handle {{
        background-color: {tokens.splitter_handle};
    }}
    """


def topbar_button_stylesheet(tokens: ThemeTokens) -> str:
    return f"""
    QPushButton {{
        background-color: transparent;
        color: {tokens.text_primary};
        font-size: 13px;
        border: none;
        border-radius: 4px;
        outline: none;
        padding: 4px 10px;
    }}
    QPushButton:hover {{
        background-color: {tokens.hover};
        color: {tokens.text_primary};
    }}
    QPushButton:pressed {{
        background-color: {tokens.pressed};
        color: {tokens.text_primary};
    }}
    """


def search_field_stylesheet(tokens: ThemeTokens) -> str:
    return f"""
    QLineEdit {{
        background: transparent;
        color: {tokens.text_muted};
        border: none;
        padding: 2px 0;
        font-size: 13px;
        selection-background-color: {tokens.hover};
    }}
    QLineEdit::placeholder {{
        color: {tokens.text_muted};
    }}
    """


def kbd_hint_stylesheet(tokens: ThemeTokens) -> str:
    return f"""
    QLabel#searchShortcutHint {{
        background: {tokens.kbd_bg};
        color: {tokens.kbd_text};
        border-radius: 4px;
        border: 1px solid {tokens.kbd_border};
        font-size: 10px;
        margin-left: 8px;
        font-family: Consolas, monospace;
        padding: 0px 5px;
        min-height: 16px;
        max-height: 18px;
    }}
    """


def hidden_scrollbar_stylesheet() -> str:
    """QSS snippet to hide scrollbar tracks and arrow buttons."""
    return """
    QScrollBar:vertical {
        background: transparent;
        width: 0px;
        margin: 0;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 0px;
        margin: 0;
    }
    QScrollBar::handle:vertical,
    QScrollBar::handle:horizontal {
        background: transparent;
    }
    QScrollBar::add-line,
    QScrollBar::sub-line,
    QScrollBar::add-page,
    QScrollBar::sub-page {
        background: none;
        border: none;
        width: 0;
        height: 0;
    }
    """


def get_stylesheet(theme: str = "dark", *, accent: str | None = None) -> str:
    """Return global stylesheet for ``dark`` or ``light`` theme."""
    t = theme_tokens(theme, accent)
    if theme == "light":
        base = f"""
    QMainWindow, QWidget {{ background-color: {t.bg_window}; color: {t.text_primary}; outline: none; }}
    QMenuBar {{ background-color: {t.bg_panel}; color: {t.text_primary}; border-bottom: 1px solid {t.border}; }}
    QMenuBar::item:selected {{ background-color: {t.hover}; }}
    QMenu {{ background-color: {t.bg_panel}; color: {t.text_primary}; border: 1px solid {t.border}; }}
    QMenu::item:selected {{ background-color: {t.hover}; }}
    QPushButton {{
        background-color: {t.bg_panel};
        color: {t.text_primary};
        border: 1px solid {t.border};
        outline: none;
        padding: 6px 12px;
        min-height: 20px;
        border-radius: 4px;
    }}
    QPushButton:hover {{ background-color: {t.hover}; }}
    QPushButton:pressed {{ background-color: {t.pressed}; }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {t.bg_input};
        color: {t.text_primary};
        border: 1px solid {t.border};
        outline: none;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    QComboBox QAbstractItemView {{ background-color: {t.bg_panel}; color: {t.text_primary}; }}
    QScrollArea {{ border: none; background-color: transparent; color: {t.text_primary}; }}
    {hidden_scrollbar_stylesheet()}
    QLabel {{ color: {t.text_primary}; }}
    QGroupBox {{ color: {t.text_primary}; border: 1px solid {t.border}; border-radius: 6px; margin-top: 10px; padding-top: 10px; }}
    QToolTip {{ background-color: {t.tooltip_bg}; color: {t.tooltip_text}; border: 1px solid {t.border}; padding: 6px 10px; }}
    QTabBar::tab {{ background-color: {t.hover}; color: {t.text_primary}; padding: 6px 12px; border: none; }}
    QTabBar::tab:selected {{ background-color: {t.bg_panel}; }}
    """
    else:
        base = f"""
    QMainWindow, QWidget {{ background-color: {t.bg_window}; color: {t.text_primary}; outline: none; }}
    QMenuBar {{ background-color: {t.bg_window}; color: {t.text_primary}; }}
    QMenuBar::item:selected {{ background-color: {t.hover}; color: {t.text_primary}; }}
    QMenu {{ background-color: {t.bg_window}; color: {t.text_primary}; }}
    QMenu::item:selected {{ background-color: {t.hover}; color: {t.text_primary}; }}
    QPushButton {{
        background-color: {t.bg_input};
        color: {t.text_primary};
        border: none;
        outline: none;
        padding: 6px 12px;
        min-height: 20px;
    }}
    QPushButton:hover {{ background-color: {t.pressed}; color: {t.text_primary}; }}
    QPushButton:pressed {{ background-color: {t.pressed}; color: {t.text_primary}; }}
    QPushButton:focus {{ border: none; outline: none; }}
    QPushButton:disabled {{ background-color: {t.bg_window}; color: {t.disabled_text}; }}
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {t.bg_input};
        color: {t.text_primary};
        border: none;
        outline: none;
        padding: 4px 8px;
        selection-background-color: {t.selection_bg};
        selection-color: {t.selection_text};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: none; outline: none; color: {t.text_primary}; }}
    QComboBox {{
        background-color: {t.bg_input};
        color: {t.text_primary};
        border: none;
        outline: none;
        padding: 4px 8px;
    }}
    QComboBox:focus {{ border: none; outline: none; }}
  """
    base += _combo_arrow_css()
    if theme != "light":
        base += f"""
    QComboBox QAbstractItemView {{ background-color: {t.bg_window}; }}
    QComboBox QAbstractItemView::item {{ color: {t.text_primary}; background-color: transparent; }}
    QComboBox QAbstractItemView::item:hover {{ background-color: {t.hover}; color: {t.text_primary}; }}
    QComboBox QAbstractItemView::item:selected {{ background-color: {t.hover}; color: {t.text_primary}; }}
    QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button {{
        width: 0; height: 0; border: none; background: transparent;
    }}
    QScrollArea {{ border: none; outline: none; background-color: transparent; color: {t.text_primary}; }}
    {hidden_scrollbar_stylesheet()}
    QLabel {{ color: {t.text_primary}; }}
    QGroupBox {{ color: {t.text_primary}; border: none; outline: none; margin-top: 8px; padding-top: 8px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
    QToolTip {{ background-color: {t.tooltip_bg}; color: {t.tooltip_text}; padding: 6px 10px; border: none; outline: none; }}
    QTabBar::tab {{ background-color: {t.bg_window}; color: {t.text_primary}; padding: 6px 12px; border: none; outline: none; }}
    QTabBar::tab:selected {{ background-color: {t.hover}; color: {t.text_primary}; }}
    QTabBar::tab:hover:!selected {{ background-color: {t.hover}; color: {t.text_primary}; }}
    """
    base += table_stylesheet(t)
    base += card_stylesheet(t)
    return base


def apply_theme_to_app(app: QApplication, *, theme: str = "dark", accent: str = "#0078D4") -> None:
    """Apply palette, stylesheet, and Fluent theme."""
    app.setPalette(get_palette(theme))
    app.setStyleSheet(get_stylesheet(theme, accent=accent))
    try:
        from qfluentwidgets import Theme, setTheme, setThemeColor

        setTheme(Theme.LIGHT if theme == "light" else Theme.DARK)
        setThemeColor(accent)
    except Exception:
        pass


def apply_drop_shadow(widget: QWidget, blur_radius: int = 10, x_offset: int = 0, y_offset: int = 2):
    """Apply IDE-like drop shadow to a panel (e.g. nav, preview)."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur_radius)
    effect.setXOffset(x_offset)
    effect.setYOffset(y_offset)
    effect.setColor(QColor(0, 0, 0, 80))
    widget.setGraphicsEffect(effect)
