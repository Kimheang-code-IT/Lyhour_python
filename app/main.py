"""App entry point: QApplication, PyQt6-Fluent-Widgets theme/style/icons, MainWindow."""
import os
import sys

# Suppress libpng iCCP warning when loading PNGs (e.g. KIEC_logo.png with old sRGB profile)
os.environ.setdefault("QT_LOGGING_RULES", "qt.gui.imageio.warning=false")

from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from app.core.main_window import MainWindow
from app.core.app import setup_theme
from app.config.settings import APP_NAME, APP_DISPLAY_NAME

try:
    from loguru import logger
except ImportError:
    logger = None  # type: ignore[assignment,misc]


def _app_icon_path() -> Path | None:
    """Path to app icon for window/taskbar. Uses KIEC_logo.png, fallback to Logo.ico. Works from source or PyInstaller exe."""
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    assets = base / "app" / "assets"
    # Prefer KIEC_logo.png (PNG with transparency); fallback to Logo.ico
    for name in ("KIEC_logo.png", "Logo.ico"):
        path = assets / name
        if path.is_file():
            return path
    return None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)

    # Use KIEC_logo.png (or Logo.ico) for taskbar and window icon
    logo_path = _app_icon_path()
    if logo_path is not None:
        app.setWindowIcon(QIcon(str(logo_path)))

    setup_theme(app)

    from app.core.theme import get_palette, get_stylesheet
    app.setPalette(get_palette())
    app.setStyleSheet(get_stylesheet())

    window = MainWindow()
    if logo_path is not None:
        window.setWindowIcon(QIcon(str(logo_path)))
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
