"""Reusable label + input row using qfluentwidgets BodyLabel + optional qtawesome (Font Awesome) icon."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

try:
    from qfluentwidgets import BodyLabel  # type: ignore[import-untyped]
    _HAS_FLUENT = True
except ImportError:
    _HAS_FLUENT = False

try:
    import qtawesome as qta  # type: ignore[import-untyped]
    _HAS_QTAWESOME = True
except ImportError:
    _HAS_QTAWESOME = False

_LABEL_ICON_SIZE = 18
_LABEL_ICON_COLOR = "#ffffff"


def _make_label(text: str, row_height: int, icon_name: str | None = None):
    if icon_name and _HAS_QTAWESOME:
        wrap = QWidget()
        wrap.setFixedHeight(row_height)
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        try:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon(icon_name, color=_LABEL_ICON_COLOR).pixmap(_LABEL_ICON_SIZE, _LABEL_ICON_SIZE))
            h.addWidget(icon_lbl)
        except Exception:
            pass
        if _HAS_FLUENT:
            lbl = BodyLabel(text)
        else:
            lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(lbl, 1)
        return wrap
    if _HAS_FLUENT:
        lbl = BodyLabel(text)
    else:
        lbl = QLabel(text)
    lbl.setFixedHeight(row_height)
    lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return lbl


def add_labeled_row(
    grid, row: int, label_text: str, widget: QWidget, row_height: int = 36, icon: str | None = None
) -> None:
    """Add a label (col 0) and widget (col 1) to grid. Optional icon: qtawesome name e.g. 'fa5s.tachometer-alt'."""
    widget.setMinimumHeight(row_height)
    widget.setMaximumHeight(row_height)
    lbl = _make_label(label_text, row_height, icon)
    grid.addWidget(lbl, row, 0)
    grid.addWidget(widget, row, 1)


class LabeledInput(QWidget):
    """Single row: label + input widget. Optional Font Awesome icon next to label."""

    def __init__(
        self,
        label_text: str,
        widget: QWidget,
        row_height: int = 36,
        parent=None,
        icon: str | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setMinimumHeight(row_height)
        widget.setMaximumHeight(row_height)
        lbl = _make_label(label_text, row_height, icon)
        layout.addWidget(lbl)
        layout.addWidget(widget, 1)
        self._widget = widget

    @property
    def widget(self):
        return self._widget
