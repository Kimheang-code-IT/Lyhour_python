"""Reusable pavement catalog cross-section chart.

Draws an engineering-style vertical stack on the app page background:
thin black seal on top, hatched layers below, theme-colored thickness labels.
"""
from __future__ import annotations

from typing import Any

from matplotlib.patches import Patch, Rectangle

from app.chart.base import draw_empty_message
from app.core.theme import theme_tokens
from app.data.pavement_catalog import (
    MATERIAL_COLORS,
    MATERIAL_HATCHES,
    MATERIAL_LABELS,
    PavementCatalogDesign,
)

# Thin seal / AC surface visual height when stored thickness is 0 (DBST).
_SEAL_DRAW_MM = 18.0
# Minimum drawn height so very thin AC bands stay readable.
_MIN_DRAW_MM = 28.0

_EDGE = "#111111"


def draw_pavement_catalog_section(ax: Any, design: PavementCatalogDesign | None) -> None:
    """Draw one selected catalog pavement stack like a catalog section diagram."""
    if design is None or not design.layers:
        draw_empty_message(ax, "No catalog design for this selection")
        return

    tokens = theme_tokens()
    page_bg = tokens.bg_window
    label_color = tokens.chart_label

    ax.set_facecolor(page_bg)
    ax.grid(False)

    display_layers: list[tuple[str, float, float]] = []
    for layer in design.layers:
        real_h = float(layer.thickness_mm)
        if real_h <= 0:
            draw_h = _SEAL_DRAW_MM
        else:
            # Keep true proportions; only bump very thin bands so they stay visible.
            draw_h = max(real_h, _MIN_DRAW_MM)
        display_layers.append((layer.material, real_h, draw_h))

    total_h = sum(item[2] for item in display_layers)
    bar_x = 0.28
    bar_width = 0.34
    label_x = bar_x + bar_width + 0.035
    cursor = 0.0

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(total_h * 1.06, -total_h * 0.06)  # top of stack at y=0
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    used_materials: list[str] = []
    for material, real_h, draw_h in display_layers:
        top = cursor
        face = MATERIAL_COLORS.get(material, "#dddddd")
        hatch = MATERIAL_HATCHES.get(material, "")
        lw = 1.35 if real_h > 0 else 1.1

        rect = Rectangle(
            (bar_x, top),
            bar_width,
            draw_h,
            linewidth=lw,
            edgecolor=_EDGE,
            facecolor=face,
            hatch=hatch,
            joinstyle="miter",
        )
        rect.set_hatch(hatch)
        ax.add_patch(rect)

        # Thickness label on the right — catalog plate style (number only when known).
        if real_h > 0:
            ax.text(
                label_x,
                top + draw_h / 2.0,
                f"{real_h:.0f}",
                va="center",
                ha="left",
                fontsize=13,
                color=label_color,
                fontweight="bold",
                fontfamily="sans-serif",
            )
        else:
            ax.text(
                label_x,
                top + draw_h / 2.0,
                material,
                va="center",
                ha="left",
                fontsize=9,
                color=label_color,
                fontweight="bold",
            )

        if material not in used_materials:
            used_materials.append(material)
        cursor += draw_h

    # Outer outline of the full stack.
    ax.add_patch(
        Rectangle(
            (bar_x, 0.0),
            bar_width,
            total_h,
            fill=False,
            edgecolor=_EDGE,
            linewidth=1.8,
            zorder=5,
        )
    )

    legend_handles = [
        Patch(
            facecolor=MATERIAL_COLORS.get(code, "#dddddd"),
            edgecolor=_EDGE,
            hatch=MATERIAL_HATCHES.get(code, ""),
            label=MATERIAL_LABELS.get(code, code),
        )
        for code in used_materials
    ]
    legend = ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.04),
        ncol=1,
        frameon=False,
        fancybox=False,
        fontsize=8,
        labelcolor=label_color,
        facecolor=page_bg,
        edgecolor=tokens.chart_axis,
    )
    legend.get_frame().set_linewidth(0.0)
