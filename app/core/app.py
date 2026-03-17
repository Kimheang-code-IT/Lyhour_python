"""Application theme setup: Fluent dark theme + accent color."""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor

try:
    from qfluentwidgets import setTheme, Theme, setThemeColor
    _HAS_FLUENT = True
except ImportError:
    _HAS_FLUENT = False


def setup_theme(app: QApplication) -> None:
    """Apply dark theme and accent color. Safe if qfluentwidgets not installed."""
    if not _HAS_FLUENT:
        return
    try:
        setTheme(Theme.DARK)
        setThemeColor("#0078D4")
    except Exception:
        try:
            setTheme(Theme.DARK)
            setThemeColor(QColor(0, 120, 212))
        except Exception:
            pass
