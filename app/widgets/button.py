"""Reusable buttons using qfluentwidgets + optional qtawesome (Font Awesome) icons."""
from PyQt6.QtCore import QSize

try:
    from qfluentwidgets import PushButton, PrimaryPushButton  # type: ignore[import-untyped]
    _HAS_FLUENT = True
except ImportError:
    from PyQt6.QtWidgets import QPushButton
    _HAS_FLUENT = False

try:
    import qtawesome as qta  # type: ignore[import-untyped]
    _HAS_QTAWESOME = True
except ImportError:
    _HAS_QTAWESOME = False

_ICON_SIZE = 20
_ICON_COLOR = "#ffffff"


def _apply_icon(btn, icon_name: str | None) -> None:
    """Set Font Awesome icon on button when qtawesome available. icon_name e.g. 'fa5s.calculator', 'fa5s.file-pdf'."""
    if not icon_name or not _HAS_QTAWESOME:
        return
    try:
        btn.setIcon(qta.icon(icon_name, color=_ICON_COLOR))
        btn.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
    except Exception:
        pass


def primary_button(text: str, min_height: int = 40, icon: str | None = None):
    """Primary action button (e.g. Calculate). Optional icon: qtawesome name e.g. 'fa5s.calculator'."""
    if _HAS_FLUENT:
        btn = PrimaryPushButton(text)
    else:
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton { background-color: #3e3e40; color: #ffffff; border: none; outline: none; }
            QPushButton:hover { background-color: #505050; }
            QPushButton:pressed { background-color: #505050; }
        """)
    btn.setMinimumHeight(min_height)
    _apply_icon(btn, icon)
    return btn


def secondary_button(text: str, min_height: int = 40, icon: str | None = None):
    """Secondary action button (e.g. Preview PDF). Optional icon: qtawesome name e.g. 'fa5s.file-pdf'."""
    if _HAS_FLUENT:
        btn = PushButton(text)
    else:
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton { background-color: #3e3e40; color: #ffffff; border: none; outline: none; }
            QPushButton:hover { background-color: #505050; }
            QPushButton:pressed { background-color: #505050; }
        """)
    btn.setMinimumHeight(min_height)
    _apply_icon(btn, icon)
    return btn
