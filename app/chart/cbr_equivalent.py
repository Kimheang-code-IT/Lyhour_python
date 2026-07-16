"""Reusable CBR Equivalent profile chart."""
from __future__ import annotations

from typing import Any

from app.chart.base import apply_axes_theme, draw_empty_message
from app.data.cbr_equivalent import CbrEquivalentResult


def draw_cbr_equivalent_profile(ax: Any, result: CbrEquivalentResult) -> None:
    """Plot layer CBR values and the equivalent CBR line."""
    if not result.layers:
        draw_empty_message(ax, "Enter DCP data to calculate CBR Equivalent")
        return

    depths: list[float] = [result.layers[0].from_depth_mm]
    cbr_steps: list[float] = [result.layers[0].cbr_percent]
    for layer in result.layers:
        depths.extend([layer.to_depth_mm, layer.to_depth_mm])
        cbr_steps.extend([layer.cbr_percent, layer.cbr_percent])
    depths = depths[:-1]
    cbr_steps = cbr_steps[:-1]

    apply_axes_theme(ax)
    ax.plot(cbr_steps, depths, color="#1f77b4", linewidth=2.0, drawstyle="steps-post")
    if result.cbr_equivalent_percent is not None:
        ax.axvline(
            result.cbr_equivalent_percent,
            color="#d62728",
            linestyle="--",
            linewidth=1.6,
            label=f"CBR Equivalent = {result.cbr_equivalent_percent:.2f}%",
        )
        ax.legend(loc="lower right", fontsize=8)

    ax.set_xlabel("CBR (%)")
    ax.set_ylabel("Depth (mm)")
    ax.set_title("CBR Equivalent Profile", pad=10)
    ax.invert_yaxis()
