"""Semi-transparent busy overlay with spinner for long-running UI updates."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from app.core.theme import current_theme

try:
    from qfluentwidgets import BodyLabel, IndeterminateProgressRing

    _HAS_FLUENT = True
except Exception:
    BodyLabel = None  # type: ignore[assignment,misc]
    IndeterminateProgressRing = None  # type: ignore[assignment,misc]
    _HAS_FLUENT = False


class LoadingOverlay(QWidget):
    """Covers its parent widget with a dimmed backdrop and loading indicator."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("loadingOverlay")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addStretch(1)

        if _HAS_FLUENT and IndeterminateProgressRing is not None:
            self._spinner = IndeterminateProgressRing(self, start=False)
            self._spinner.setFixedSize(48, 48)
            layout.addWidget(self._spinner, 0, Qt.AlignmentFlag.AlignHCenter)
        else:
            self._spinner = QProgressBar(self)
            self._spinner.setRange(0, 0)
            self._spinner.setFixedSize(160, 8)
            layout.addWidget(self._spinner, 0, Qt.AlignmentFlag.AlignHCenter)

        if _HAS_FLUENT and BodyLabel is not None:
            self._message = BodyLabel("")
        else:
            self._message = QLabel("")
            self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setWordWrap(True)
        layout.addWidget(self._message, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

        self._apply_style()
        parent.installEventFilter(self)

    def _apply_style(self) -> None:
        if current_theme() == "light":
            backdrop = "rgba(255, 255, 255, 0.72)"
            text = "#1e1e1e"
        else:
            backdrop = "rgba(0, 0, 0, 0.55)"
            text = "#f0f0f0"
        self.setStyleSheet(
            f"#loadingOverlay {{ background-color: {backdrop}; }}"
            f"QLabel {{ color: {text}; font-size: 13px; }}"
        )

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:  # noqa: N802
        if watched is self.parentWidget() and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.ShowToParent,
        ):
            self._sync_geometry()
        return super().eventFilter(watched, event)

    def _sync_geometry(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())

    def show_busy(self, message: str = "") -> None:
        self._apply_style()
        self._message.setText(message)
        self._message.setVisible(bool(message))
        self._sync_geometry()
        if hasattr(self._spinner, "start"):
            self._spinner.start()
        self.show()
        self.raise_()

    def hide_busy(self) -> None:
        if hasattr(self._spinner, "stop"):
            self._spinner.stop()
        self.hide()
