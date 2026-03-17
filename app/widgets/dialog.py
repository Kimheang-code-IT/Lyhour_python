"""Reusable dialogs using qfluentwidgets MessageBox when available; file dialogs stay Qt standard."""
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QWidget

try:
    from qfluentwidgets import MessageBox  # type: ignore[import-untyped]
    _HAS_FLUENT = True
except ImportError:
    _HAS_FLUENT = False


def info(parent: QWidget | None, title: str, message: str) -> None:
    """Show information message. Uses Fluent MessageBox when available."""
    if _HAS_FLUENT:
        w = MessageBox(title, message, parent)
        w.cancelButton.hide()
        w.yesButton.setText("OK")
        w.exec()
    else:
        QMessageBox.information(parent, title, message)


def warning(parent: QWidget | None, title: str, message: str) -> None:
    """Show warning message. Uses Fluent MessageBox when available."""
    if _HAS_FLUENT:
        w = MessageBox(title, message, parent)
        w.cancelButton.hide()
        w.yesButton.setText("OK")
        w.exec()
    else:
        QMessageBox.warning(parent, title, message)


def open_file(
    parent: QWidget | None,
    caption: str = "Open",
    directory: str = "",
    filter: str = "All Files (*)",
) -> tuple[str, str]:
    """Returns (path, selected_filter). path is empty if cancelled. Uses standard QFileDialog."""
    return QFileDialog.getOpenFileName(parent, caption, directory, filter)


def save_file(
    parent: QWidget | None,
    caption: str = "Save As",
    directory: str = "",
    filter: str = "All Files (*)",
) -> tuple[str, str]:
    """Returns (path, selected_filter). path is empty if cancelled. Uses standard QFileDialog."""
    return QFileDialog.getSaveFileName(parent, caption, directory, filter)
