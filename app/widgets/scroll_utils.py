"""Shared scroll-area configuration: hidden bars + smooth page wheel scrolling."""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QWidget,
)

# Pixels to move per mouse-wheel notch (120 angle units).
_WHEEL_STEP_PX = 80
# Animation length for page scroll-area wheel scrolling.
_SMOOTH_MS = 160


def _wheel_delta_y(event) -> int:
    pixel = event.pixelDelta().y()
    if pixel:
        return -int(pixel)
    notches = event.angleDelta().y() / 120.0
    if notches == 0:
        return 0
    return -int(notches * _WHEEL_STEP_PX)


def _is_descendant(child: QWidget | None, ancestor: QWidget) -> bool:
    w = child
    while w is not None:
        if w is ancestor:
            return True
        w = w.parentWidget()
    return False


def _is_editable_wheel_target(widget: QWidget | None) -> bool:
    """Combos / spins should keep their own wheel behavior."""
    w = widget
    while w is not None:
        if isinstance(w, (QComboBox, QAbstractSpinBox)):
            return True
        w = w.parentWidget()
    return False


def _nested_scroll_area(start: QWidget | None, page: QAbstractScrollArea) -> QAbstractScrollArea | None:
    """Nearest inner scroll area between the wheel target and the page scroller."""
    w = start
    while w is not None and w is not page and w is not page.viewport():
        if isinstance(w, QAbstractScrollArea) and w is not page:
            return w
        w = w.parentWidget()
    return None


def _can_scroll(bar, delta: int) -> bool:
    if bar.maximum() <= bar.minimum():
        return False
    if delta > 0:
        return bar.value() < bar.maximum()
    if delta < 0:
        return bar.value() > bar.minimum()
    return False


class _PageWheelFilter(QObject):
    """App-level filter: wheel over any block scrolls the page QScrollArea.

    Scrollbar chrome stays hidden; wheel / trackpad still moves the page.
    Nested tables keep the wheel while they still have room to scroll.
    """

    def __init__(self, scroll_area: QScrollArea):
        super().__init__(scroll_area)
        self._area = scroll_area
        bar = scroll_area.verticalScrollBar()
        self._anim = QPropertyAnimation(bar, b"value", self)
        self._anim.setDuration(_SMOOTH_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._target = bar.value()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() != QEvent.Type.Wheel:
            return False
        if not isinstance(obj, QWidget):
            return False
        if not _is_descendant(obj, self._area):
            return False
        if _is_editable_wheel_target(obj):
            return False

        delta = _wheel_delta_y(event)
        if delta == 0:
            return False

        nested = _nested_scroll_area(obj, self._area)
        if nested is not None and _can_scroll(nested.verticalScrollBar(), delta):
            return False

        bar = self._area.verticalScrollBar()
        if not _can_scroll(bar, delta):
            return False

        if self._anim.state() == QPropertyAnimation.State.Running:
            base = int(self._target)
        else:
            base = bar.value()

        self._target = max(bar.minimum(), min(bar.maximum(), base + delta))
        self._anim.stop()
        self._anim.setStartValue(bar.value())
        self._anim.setEndValue(self._target)
        self._anim.start()
        return True


def fit_scroll_content(widget: QWidget) -> QWidget:
    """Let content grow taller than the viewport so the page can scroll."""
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    return widget


class ScrollStackWidget(QStackedWidget):
    """Stacked widget that sizes to the current page (needed inside QScrollArea)."""

    def sizeHint(self):  # noqa: N802
        current = self.currentWidget()
        if current is not None:
            return current.sizeHint()
        return super().sizeHint()

    def minimumSizeHint(self):  # noqa: N802
        current = self.currentWidget()
        if current is not None:
            return current.minimumSizeHint()
        return super().minimumSizeHint()

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        super().setCurrentIndex(index)
        self.updateGeometry()


def _attach_page_wheel(scroll_area: QScrollArea) -> None:
    if getattr(scroll_area, "_page_wheel_filter", None) is not None:
        return
    app = QApplication.instance()
    if app is None:
        return
    filt = _PageWheelFilter(scroll_area)
    app.installEventFilter(filt)
    scroll_area._page_wheel_filter = filt  # type: ignore[attr-defined]


def _hide_scrollbar_ui(widget: QAbstractScrollArea) -> None:
    """Hide scrollbar chrome; scrolling still works via wheel / code."""
    widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


def configure_page_scroll(widget: QScrollArea | QAbstractScrollArea | QWidget) -> None:
    """Hide scrollbar UI; enable smooth wheel scrolling on page areas."""
    if isinstance(widget, QScrollArea):
        _hide_scrollbar_ui(widget)
        widget.setWidgetResizable(True)
        widget.verticalScrollBar().setSingleStep(24)
        _attach_page_wheel(widget)
        content = widget.widget()
        if content is not None:
            fit_scroll_content(content)
        return

    if isinstance(widget, QAbstractScrollArea):
        # Tables / inner lists: no bar UI; wheel still scrolls the view.
        _hide_scrollbar_ui(widget)
        if isinstance(widget, QAbstractItemView):
            widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            widget.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        widget.verticalScrollBar().setSingleStep(20)
        return

    if hasattr(widget, "setHorizontalScrollBarPolicy"):
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    if hasattr(widget, "setVerticalScrollBarPolicy"):
        widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


def configure_hidden_scrollbars(widget: QScrollArea | QWidget) -> None:
    """Alias for configure_page_scroll (hidden bars + wheel scroll)."""
    configure_page_scroll(widget)


def scrollbar_stylesheet(*, track: str = "transparent", handle: str = "transparent", handle_hover: str = "transparent") -> str:
    """Global QSS: hide scrollbar tracks / handles (wheel scroll still works)."""
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


def hidden_scrollbar_stylesheet() -> str:
    """Hide scrollbar chrome app-wide."""
    return scrollbar_stylesheet()
