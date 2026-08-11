"""Reusable road cross-section design diagram."""
from __future__ import annotations

from typing import Any

from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

from app.chart.base import draw_empty_message
from app.core.theme import theme_tokens
from app.data.cross_section import CrossSectionDesign, CrossSectionSegment

_SURFACE_COLORS = {
    "earth": "#6b8f3c",
    "shoulder": "#d4b45a",
    "lane": "#2a2a2a",
    "median": "#9a9a9a",
}
_BASE_COLOR = "#5c5c5c"
_EDGE = "#111111"


def draw_cross_section(ax: Any, design: CrossSectionDesign | None) -> None:
    """Draw a dynamic cross-section matching typical road design plates."""
    if design is None or not design.segments:
        draw_empty_message(ax, "No cross-section for this selection")
        return

    tokens = theme_tokens()
    ax.set_facecolor(tokens.bg_card)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    segments = design.segments
    total_w = max(design.total_width_m, 1.0)

    # Vertical layout (meters, exaggerated for readability).
    y_surface = 0.0
    pavement_depth = 0.55
    base_depth = 1.05
    dim_y = 2.35
    label_y = 1.55
    slope_label_y = -2.35

    # Build surface elevations left → right from cross slopes.
    x_edges = [0.0]
    z_edges = [0.0]
    cursor = 0.0
    z = 0.0
    for seg in segments:
        # Fall to the right when slope > 0.
        dz = -(seg.cross_slope_percent / 100.0) * seg.width_m
        # Amplify slope visually slightly for earth banks.
        if seg.surface == "earth":
            dz = -(0.55 if seg.cross_slope_percent > 0 else -0.55) * seg.width_m
        cursor += seg.width_m
        z += dz
        x_edges.append(cursor)
        z_edges.append(z)

    # Normalize so median / center is near y_surface.
    mid_idx = len(x_edges) // 2
    z_offset = -z_edges[mid_idx]
    z_edges = [z + z_offset for z in z_edges]

    # Draw each segment as a 3D-ish extruded prism (front face + top).
    depth_3d = total_w * 0.12
    for i, seg in enumerate(segments):
        x0, x1 = x_edges[i], x_edges[i + 1]
        z0, z1 = z_edges[i], z_edges[i + 1]
        _draw_segment_prism(
            ax,
            x0,
            x1,
            z0,
            z1,
            y_surface,
            pavement_depth if seg.surface != "earth" else base_depth * 0.55,
            base_depth if seg.surface != "earth" else base_depth * 0.85,
            depth_3d,
            seg,
        )

    # Median barrier when median exists.
    for i, seg in enumerate(segments):
        if seg.surface != "median":
            continue
        x0, x1 = x_edges[i], x_edges[i + 1]
        z0, z1 = z_edges[i], z_edges[i + 1]
        xm = (x0 + x1) / 2.0
        zm = (z0 + z1) / 2.0
        barrier_w = min(0.45, seg.width_m * 0.35)
        ax.add_patch(
            Rectangle(
                (xm - barrier_w / 2.0, zm + 0.05),
                barrier_w,
                0.85,
                facecolor="#c8c8c8",
                edgecolor=_EDGE,
                linewidth=1.0,
                zorder=6,
            )
        )

    # Dimension lines + width labels above each paved / earth segment.
    for i, seg in enumerate(segments):
        x0, x1 = x_edges[i], x_edges[i + 1]
        _draw_dimension(ax, x0, x1, dim_y, f"{seg.width_m:.2f} m".rstrip("0").rstrip("."))
        ax.text(
            (x0 + x1) / 2.0,
            label_y,
            seg.label,
            ha="center",
            va="center",
            fontsize=8,
            color=tokens.chart_label,
            fontweight="600",
        )

    # Cross-slope callouts on shoulders and outer lanes.
    for i, seg in enumerate(segments):
        if seg.surface not in {"shoulder", "lane"}:
            continue
        if abs(seg.cross_slope_percent) < 0.1:
            continue
        x0, x1 = x_edges[i], x_edges[i + 1]
        z0, z1 = z_edges[i], z_edges[i + 1]
        xm = (x0 + x1) / 2.0
        zm = (z0 + z1) / 2.0 + 0.35
        direction = 1 if seg.cross_slope_percent > 0 else -1
        ax.annotate(
            f"{abs(seg.cross_slope_percent):.0f}%",
            xy=(xm + direction * seg.width_m * 0.22, zm - 0.15),
            xytext=(xm, zm + 0.35),
            color=tokens.chart_label,
            fontsize=8,
            fontweight="bold",
            arrowprops={
                "arrowstyle": "->",
                "color": tokens.chart_label,
                "lw": 1.0,
            },
            ha="center",
            va="bottom",
            zorder=8,
        )

    # Cut / fill slope ratios under earth banks.
    for i, seg in enumerate(segments):
        if seg.surface != "earth":
            continue
        x0, x1 = x_edges[i], x_edges[i + 1]
        ratio = design.cut_slope_ratio if seg.name == "cut" else design.fill_slope_ratio
        ax.text(
            (x0 + x1) / 2.0,
            slope_label_y,
            f"{seg.label}\n{ratio}",
            ha="center",
            va="top",
            fontsize=8,
            color=tokens.chart_value,
        )

    # Travel direction chevrons on lane surfaces.
    for i, seg in enumerate(segments):
        if seg.surface != "lane":
            continue
        x0, x1 = x_edges[i], x_edges[i + 1]
        z0, z1 = z_edges[i], z_edges[i + 1]
        xm = (x0 + x1) / 2.0
        zm = (z0 + z1) / 2.0 + 0.08
        # Left carriageway points "out of page", right points "into page" (schematic).
        left_side = x1 <= total_w * 0.5
        dy = -0.35 if left_side else 0.35
        ax.add_patch(
            FancyArrowPatch(
                (xm, zm - dy * 0.2),
                (xm, zm + dy),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.4,
                color="#f0f0f0",
                zorder=7,
            )
        )

    pad = total_w * 0.04
    ax.set_xlim(-pad, total_w + pad)
    ax.set_ylim(-3.2, 3.1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(design.title, color=tokens.chart_label, fontsize=11, pad=8, fontweight="600")


def _draw_segment_prism(
    ax: Any,
    x0: float,
    x1: float,
    z0: float,
    z1: float,
    y_surface: float,
    pavement_depth: float,
    base_depth: float,
    depth_3d: float,
    seg: CrossSectionSegment,
) -> None:
    face = _SURFACE_COLORS.get(seg.surface, "#888888")

    # Top surface (road / shoulder / earth).
    top = Polygon(
        [
            (x0, z0),
            (x1, z1),
            (x1 + depth_3d * 0.15, z1 + depth_3d * 0.08),
            (x0 + depth_3d * 0.15, z0 + depth_3d * 0.08),
        ],
        closed=True,
        facecolor=face,
        edgecolor=_EDGE,
        linewidth=0.9,
        zorder=4,
    )
    ax.add_patch(top)

    # Front pavement / base thickness (not for pure earth cut face beyond).
    if seg.surface != "earth":
        front = Polygon(
            [
                (x0, z0),
                (x1, z1),
                (x1, z1 - pavement_depth),
                (x0, z0 - pavement_depth),
            ],
            closed=True,
            facecolor=_BASE_COLOR,
            edgecolor=_EDGE,
            linewidth=0.8,
            zorder=3,
        )
        ax.add_patch(front)
        base = Polygon(
            [
                (x0, z0 - pavement_depth),
                (x1, z1 - pavement_depth),
                (x1, z1 - base_depth),
                (x0, z0 - base_depth),
            ],
            closed=True,
            facecolor="#7a6a55",
            edgecolor=_EDGE,
            linewidth=0.7,
            zorder=2,
        )
        ax.add_patch(base)
    else:
        # Earth bank front face.
        front = Polygon(
            [
                (x0, z0),
                (x1, z1),
                (x1, z1 - base_depth * 0.7),
                (x0, z0 - base_depth * 0.7),
            ],
            closed=True,
            facecolor="#5f7a3a",
            edgecolor=_EDGE,
            linewidth=0.8,
            zorder=2,
        )
        ax.add_patch(front)

    # Lane markings: dashed center between adjacent lanes handled lightly.
    if seg.surface == "lane":
        xm = (x0 + x1) / 2.0
        zm = (z0 + z1) / 2.0
        ax.plot(
            [xm, xm + depth_3d * 0.12],
            [zm + 0.02, zm + depth_3d * 0.06],
            color="#ffffff",
            linewidth=1.0,
            linestyle=(0, (4, 4)),
            zorder=5,
        )


def _draw_dimension(ax: Any, x0: float, x1: float, y: float, text: str) -> None:
    tokens = theme_tokens()
    color = tokens.chart_label
    ax.plot([x0, x0], [y - 0.15, y + 0.15], color=color, linewidth=0.9)
    ax.plot([x1, x1], [y - 0.15, y + 0.15], color=color, linewidth=0.9)
    ax.annotate(
        "",
        xy=(x1, y),
        xytext=(x0, y),
        arrowprops={"arrowstyle": "<->", "color": color, "lw": 1.0},
    )
    ax.text(
        (x0 + x1) / 2.0,
        y + 0.22,
        text,
        ha="center",
        va="bottom",
        fontsize=8,
        color=color,
        fontweight="bold",
    )
