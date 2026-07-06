"""Application theme setup: Fluent theme + accent color."""
from PyQt6.QtWidgets import QApplication

from app.core.theme import apply_theme_to_app
from app.services.app_settings import AppSettings


def setup_theme(app: QApplication) -> None:
    """Apply saved theme preferences. Safe if qfluentwidgets is not installed."""
    prefs = AppSettings.instance().load()
    apply_theme_to_app(app, theme=prefs.theme, accent=prefs.accent_color)
