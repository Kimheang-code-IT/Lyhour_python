"""Reusable matplotlib chart helpers shared across pages."""
from __future__ import annotations

from typing import Any

from app.core.theme import theme_tokens
from app.widgets.chart_ui import MatplotlibChartWidget, make_matplotlib_chart

__all__ = (
    "MatplotlibChartWidget",
    "make_matplotlib_chart",
    "apply_axes_theme",
    "draw_empty_message",
)


def apply_axes_theme(ax: Any) -> None:
    """Apply current app theme colors to a matplotlib axes."""
    tokens = theme_tokens()
    ax.set_facecolor(tokens.bg_card)
    ax.tick_params(colors=tokens.chart_value)
    ax.xaxis.label.set_color(tokens.chart_label)
    ax.yaxis.label.set_color(tokens.chart_label)
    ax.title.set_color(tokens.chart_label)
    for spine in ax.spines.values():
        spine.set_color(tokens.chart_axis)
    ax.grid(True, color=tokens.chart_grid, alpha=0.45, linewidth=0.6)


def draw_empty_message(ax: Any, message: str) -> None:
    """Show a centered placeholder when chart data is not ready."""
    tokens = theme_tokens()
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        transform=ax.transAxes,
        color=tokens.chart_value,
        fontsize=10,
    )
    ax.set_axis_off()
