"""Theme: gray backgrounds and white text only."""
from pathlib import Path

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect

# From app/core, assets are at app/assets
_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_ARROW_DOWN_ASSET = _ASSETS / "arrow-down.png"

# Gray shades (backgrounds)
_GRAY_DARK = QColor(45, 45, 48)   # #2d2d30
_GRAY_BASE = QColor(62, 62, 64)   # #3e3e40
_GRAY_MID = QColor(80, 80, 80)    # #505050
_GRAY_DISABLED = QColor(136, 136, 136)  # #888888
_WHITE = QColor(255, 255, 255)


def get_palette() -> QPalette:
    """Palette: gray backgrounds, white text only."""
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, _GRAY_DARK)
    p.setColor(QPalette.ColorRole.WindowText, _WHITE)
    p.setColor(QPalette.ColorRole.Base, _GRAY_BASE)
    p.setColor(QPalette.ColorRole.AlternateBase, _GRAY_DARK)
    p.setColor(QPalette.ColorRole.Button, _GRAY_BASE)
    p.setColor(QPalette.ColorRole.ButtonText, _WHITE)
    p.setColor(QPalette.ColorRole.Text, _WHITE)
    p.setColor(QPalette.ColorRole.PlaceholderText, _GRAY_MID)
    p.setColor(QPalette.ColorRole.Highlight, _GRAY_BASE)
    p.setColor(QPalette.ColorRole.HighlightedText, _WHITE)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, _GRAY_DISABLED)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, _GRAY_DISABLED)
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, _GRAY_DISABLED)
    return p


def get_stylesheet() -> str:
    """Stylesheet: gray backgrounds and white text only. No focus/selection border."""
    base = """
    QMainWindow, QWidget { background-color: #2d2d30; color: #ffffff; outline: none; }
    QMenuBar { background-color: #2d2d30; color: #ffffff; }
    QMenuBar::item:selected { background-color: #3e3e40; color: #ffffff; }
    QMenu { background-color: #2d2d30; color: #ffffff; }
    QMenu::item:selected { background-color: #3e3e40; color: #ffffff; }
    QPushButton {
        background-color: #3e3e40;
        color: #ffffff;
        border: none;
        outline: none;
        padding: 6px 12px;
        min-height: 20px;
    }
    QPushButton:hover { background-color: #505050; color: #ffffff; }
    QPushButton:pressed { background-color: #505050; color: #ffffff; }
    QPushButton:focus { border: none; outline: none; }
    QPushButton:disabled { background-color: #2d2d30; color: #888888; }
    QLineEdit, QSpinBox, QDoubleSpinBox {
        background-color: #3e3e40;
        color: #ffffff;
        border: none;
        outline: none;
        padding: 4px 8px;
        selection-background-color: #3e3e40;
        selection-color: #ffffff;
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: none; outline: none; color: #ffffff; }
    QComboBox {
        background-color: #3e3e40;
        color: #ffffff;
        border: none;
        outline: none;
        padding: 4px 8px;
    }
    QComboBox:focus { border: none; outline: none; }
    """
    if _ARROW_DOWN_ASSET.exists():
        try:
            arrow_uri = _ARROW_DOWN_ASSET.resolve().as_uri()
        except Exception:
            arrow_uri = _ARROW_DOWN_ASSET.as_uri()
        base += f"""
    QComboBox::down-arrow {{
        image: url({arrow_uri});
        width: 16px;
        height: 16px;
    }}
    """
    base += """
    QComboBox QAbstractItemView { background-color: #2d2d30; }
    QComboBox QAbstractItemView::item { color: #ffffff; background-color: transparent; }
    QComboBox QAbstractItemView::item:hover { background-color: #3e3e40; color: #ffffff; }
    QComboBox QAbstractItemView::item:selected { background-color: #3e3e40; color: #ffffff; }
    QComboBox QAbstractItemView::item:selected:hover { background-color: #3e3e40; color: #ffffff; }
    QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button {
        width: 0; height: 0; border: none; background: transparent;
    }
    QScrollArea { border: none; outline: none; background-color: transparent; color: #ffffff; }
    QScrollBar:vertical {
        background: #2d2d30;
        width: 12px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #505050;
        min-height: 24px;
    }
    QScrollBar::handle:vertical:hover { background: #3e3e40; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QLabel { color: #ffffff; }
    QGroupBox {
        color: #ffffff;
        border: none;
        outline: none;
        margin-top: 8px;
        padding-top: 8px;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
    QToolTip {
        background-color: #3e3e40;
        color: #ffffff;
        padding: 6px 10px;
        border: none;
        outline: none;
    }
    QTabBar::tab { background-color: #2d2d30; color: #ffffff; padding: 6px 12px; border: none; outline: none; }
    QTabBar::tab:selected { background-color: #3e3e40; color: #ffffff; }
    QTabBar::tab:hover:!selected { background-color: #3e3e40; color: #ffffff; }
    """
    return base


def apply_drop_shadow(widget: QWidget, blur_radius: int = 10, x_offset: int = 0, y_offset: int = 2):
    """Apply IDE-like drop shadow to a panel (e.g. nav, preview)."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur_radius)
    effect.setXOffset(x_offset)
    effect.setYOffset(y_offset)
    effect.setColor(QColor(0, 0, 0, 80))
    widget.setGraphicsEffect(effect)
