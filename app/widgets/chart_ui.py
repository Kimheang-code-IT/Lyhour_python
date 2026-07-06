"""Theme-aware chart widgets (matplotlib + pyqtgraph) for embedding in pages."""
from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from app.core.theme import theme_tokens

try:
    import matplotlib

    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure

    _HAS_MPL = True
except Exception:
    Figure = None  # type: ignore[assignment,misc]
    FigureCanvasQTAgg = None  # type: ignore[assignment,misc]
    _HAS_MPL = False

try:
    import pyqtgraph as pg

    _HAS_PG = True
except Exception:
    pg = None  # type: ignore[assignment]
    _HAS_PG = False


def _apply_matplotlib_theme(figure: Figure) -> None:
    tokens = theme_tokens()
    figure.patch.set_facecolor(tokens.bg_card)
    for axis in figure.axes:
        axis.set_facecolor(tokens.bg_card)
        axis.tick_params(colors=tokens.chart_value)
        axis.xaxis.label.set_color(tokens.chart_label)
        axis.yaxis.label.set_color(tokens.chart_label)
        axis.title.set_color(tokens.chart_label)
        for spine in axis.spines.values():
            spine.set_color(tokens.chart_axis)
        axis.grid(True, color=tokens.chart_grid, alpha=0.6, linewidth=0.8)


def _apply_pyqtgraph_theme(plot_widget: Any) -> None:
    tokens = theme_tokens()
    plot_widget.setBackground(tokens.bg_card)
    plot_widget.getAxis("left").setPen(tokens.chart_axis)
    plot_widget.getAxis("bottom").setPen(tokens.chart_axis)
    plot_widget.getAxis("left").setTextPen(tokens.chart_value)
    plot_widget.getAxis("bottom").setTextPen(tokens.chart_value)
    plot_widget.showGrid(x=True, y=True, alpha=0.35)


class MatplotlibChartWidget(QWidget):
    """Embeddable matplotlib figure with app theme colors."""

    def __init__(self, parent: QWidget | None = None, *, figsize: tuple[float, float] = (6.0, 4.0)) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if not _HAS_MPL or Figure is None or FigureCanvasQTAgg is None:
            self.figure = None
            self.canvas = None
            return

        self.figure = Figure(figsize=figsize, dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)
        self.apply_theme()

    def apply_theme(self) -> None:
        if self.figure is None or self.canvas is None:
            return
        _apply_matplotlib_theme(self.figure)
        self.canvas.draw()

    def clear(self) -> None:
        if self.figure is None:
            return
        self.figure.clear()
        self.canvas.draw()

    def add_subplot(self, *args: Any, **kwargs: Any):
        if self.figure is None:
            raise RuntimeError("matplotlib is not installed")
        ax = self.figure.add_subplot(*args, **kwargs)
        _apply_matplotlib_theme(self.figure)
        return ax


class PyQtGraphChartWidget(QWidget):
    """Embeddable pyqtgraph plot with app theme colors."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if not _HAS_PG or pg is None:
            self.plot = None
            return

        self.plot = pg.PlotWidget()
        self.plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.plot)
        self.apply_theme()

    def apply_theme(self) -> None:
        if self.plot is None:
            return
        _apply_pyqtgraph_theme(self.plot)

    def plot_bars(self, x: list[float], heights: list[float], *, name: str = "series") -> None:
        if self.plot is None:
            return
        tokens = theme_tokens()
        bar = pg.BarGraphItem(x=x, height=heights, width=0.6, brush=tokens.accent)
        self.plot.clear()
        _apply_pyqtgraph_theme(self.plot)
        self.plot.addItem(bar)
        self.plot.setTitle(name, color=tokens.chart_label)


def make_matplotlib_chart(parent: QWidget | None = None, *, figsize: tuple[float, float] = (6.0, 4.0)) -> MatplotlibChartWidget:
    return MatplotlibChartWidget(parent, figsize=figsize)


def make_pyqtgraph_chart(parent: QWidget | None = None) -> PyQtGraphChartWidget:
    return PyQtGraphChartWidget(parent)
