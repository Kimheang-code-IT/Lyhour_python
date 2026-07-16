"""Reusable DCP analysis charts."""
from __future__ import annotations

from typing import Any

from app.chart.base import apply_axes_theme, draw_empty_message
from app.core.theme import theme_tokens
from app.data.dcp_analysis import DcpAnalysisRow


def draw_dcp_depth_vs_blows(ax: Any, rows: list[DcpAnalysisRow]) -> None:
    """Depth (inverted) vs cumulative blows."""
    plot_rows = [row for row in rows if row.total_blow_number > 0 or row.total_penetration_mm > 0]
    if len(plot_rows) < 2:
        draw_empty_message(ax, "Enter DCP data to plot")
        return

    tokens = theme_tokens()
    x = [row.total_blow_number for row in plot_rows]
    y = [row.total_penetration_mm for row in plot_rows]

    apply_axes_theme(ax)
    ax.plot(x, y, color=tokens.accent, marker="o", markerfacecolor="white", linewidth=1.8)
    ax.set_xlabel("Total Blow Number")
    ax.set_ylabel("Total Penetration (mm)")
    ax.set_title("Depth vs Total Blows", pad=10)
    ax.invert_yaxis()


def draw_dcp_depth_vs_cbr(ax: Any, rows: list[DcpAnalysisRow]) -> None:
    """Depth (inverted) vs CBR%."""
    plot_rows = [
        row
        for row in rows
        if row.cbr_percent is not None and row.total_penetration_mm > 0
    ]
    if len(plot_rows) < 2:
        draw_empty_message(ax, "Enter DCP data to plot")
        return

    x = [row.cbr_percent for row in plot_rows]
    y = [row.total_penetration_mm for row in plot_rows]

    apply_axes_theme(ax)
    ax.plot(x, y, color="#d62728", marker="D", markerfacecolor="white", linewidth=1.8)
    ax.set_xlabel("CBR (%)")
    ax.set_ylabel("Total Penetration (mm)")
    ax.set_title("Depth vs CBR", pad=10)
    ax.invert_yaxis()
