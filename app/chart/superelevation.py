"""Reusable Full Superelevation Graph chart."""
from __future__ import annotations

from typing import Any

from app.data.superelevation_profile import SuperelevationProfile, format_station

Y_AXIS_MIN = -10.0
Y_AXIS_MAX = 15.0
Y_AXIS_TICK_STEP = 2.5
Y_AXIS_TICK_FONTSIZE = 7
Y_AXIS_LABEL_FONTSIZE = 8

COLOR_ALIGNMENT = "#1f77b4"
COLOR_CENTERLINE = "#c44f4f"
COLOR_INSIDE = "#2ca02c"
COLOR_OUTSIDE = "#d87b3d"
COLOR_MARKER = "#d65f5f"
COLOR_DIM = "#4da3ff"
COLOR_GUIDE = "#777777"


def format_y_tick(value: float) -> str:
    rounded = round(float(value) * 2) / 2
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.1f}"


# Backwards-compatible private alias used by older tests.
_format_y_tick = format_y_tick


def configure_superelevation_y_axis(ax: Any) -> None:
    """Fixed Y scale matching road-design drawings: -10 to 15 % at 2.5 intervals."""
    import numpy as np

    from app.core.theme import theme_tokens

    tokens = theme_tokens()
    yticks = np.arange(Y_AXIS_MIN, Y_AXIS_MAX + Y_AXIS_TICK_STEP / 2, Y_AXIS_TICK_STEP)
    ax.set_ylim(Y_AXIS_MIN, Y_AXIS_MAX)
    ax.set_yticks(yticks)
    ax.set_yticklabels([format_y_tick(y) for y in yticks])
    ax.set_ylabel("Superelevation, e(%)", fontsize=Y_AXIS_LABEL_FONTSIZE, color=tokens.chart_label)

    ax.tick_params(axis="y", labelsize=Y_AXIS_TICK_FONTSIZE, length=3, width=0.6, pad=2, colors=tokens.chart_value)
    ax.yaxis.label.set_fontfamily("serif")
    for label in ax.get_yticklabels():
        label.set_fontfamily("serif")


def edge_elevations(profile: SuperelevationProfile) -> tuple[list[float], list[float], list[float]]:
    """Piecewise stations and outside/inside edge elevations (%) for the full profile.

    Outside edge (rotation about centerline):
      SSD: −e1 → TS: 0 → SC: +e_max → CS: +e_max → ST: 0 → ESD: −e1

    Inside edge:
      SSD–TS: −e1 → SC: −e_max → CS: −e_max → ST–ESD: −e1
    """
    e1 = profile.e1_percent
    emax = profile.e_max_percent
    stations = [
        profile.start_station_m,
        profile.ts_station_m,
        profile.sc_station_m,
        profile.cs_station_m,
        profile.st_station_m,
        profile.end_station_m,
    ]
    outside = [-e1, 0.0, emax, emax, 0.0, -e1]
    inside = [-e1, -e1, -emax, -emax, -e1, -e1]
    return stations, outside, inside


def _draw_dimension(
    ax: Any,
    x_left: float,
    x_right: float,
    y: float,
    text: str,
    *,
    color: str = COLOR_DIM,
    text_color: str = COLOR_MARKER,
    fontsize: float = 7,
) -> None:
    if x_right <= x_left:
        return
    ax.annotate(
        "",
        xy=(x_left, y),
        xytext=(x_right, y),
        arrowprops={"arrowstyle": "<->", "color": color, "lw": 1.0},
    )
    ax.text(
        (x_left + x_right) / 2,
        y,
        text,
        color=text_color,
        fontsize=fontsize,
        ha="center",
        va="bottom",
        fontfamily="serif",
    )


def _draw_cross_section_icon(
    ax: Any,
    x: float,
    *,
    kind: str,
    y_offset: float = -0.12,
    width: float = 0.028,
    height: float = 0.045,
) -> None:
    """Small pavement cross-section sketch below the x-axis (axes coordinates)."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyBboxPatch

    x_axes = ax.transLimits.transform((x, 0.0))[0]
    cx = float(x_axes)
    cy = y_offset
    half_w = width / 2
    half_h = height / 2

    frame = FancyBboxPatch(
        (cx - half_w - 0.004, cy - half_h - 0.004),
        width + 0.008,
        height + 0.008,
        boxstyle="round,pad=0.002,rounding_size=0.004",
        transform=ax.transAxes,
        facecolor="#f5f7fa",
        edgecolor=COLOR_ALIGNMENT,
        linewidth=0.7,
        clip_on=False,
        zorder=6,
    )
    ax.add_patch(frame)

    left = cx - half_w
    right = cx + half_w
    mid = cx
    top = cy + half_h * 0.55
    bottom = cy - half_h * 0.55
    mid_y = cy

    def _seg(x0: float, y0: float, x1: float, y1: float) -> None:
        line = Line2D(
            [x0, x1],
            [y0, y1],
            transform=ax.transAxes,
            color=COLOR_ALIGNMENT,
            linewidth=1.3,
            solid_capstyle="round",
            clip_on=False,
            zorder=7,
        )
        ax.add_line(line)

    if kind == "crown":
        _seg(left, bottom, mid, top)
        _seg(mid, top, right, bottom)
    elif kind == "remove_adverse":
        _seg(left, bottom, mid, mid_y)
        _seg(mid, mid_y, right, bottom * 0.4 + mid_y * 0.6)
    elif kind == "full_super":
        _seg(left, bottom, right, top)
    elif kind == "exit_runoff":
        _seg(left, bottom * 0.4 + mid_y * 0.6, mid, mid_y)
        _seg(mid, mid_y, right, bottom)
    else:
        _seg(left, bottom, mid, top)
        _seg(mid, top, right, bottom)


def draw_superelevation_profile(ax: Any, profile: SuperelevationProfile) -> None:
    """Draw a full superelevation graph matching the road-design reference drawing."""
    from matplotlib.lines import Line2D

    from app.core.theme import theme_tokens

    tokens = theme_tokens()
    text_muted = tokens.chart_value
    text_primary = tokens.chart_label

    stations, outside_y, inside_y = edge_elevations(profile)
    x0, x1, x2, x3, x4, x5 = stations
    e1 = profile.e1_percent
    emax = profile.e_max_percent

    left_margin = max(profile.tro_m, 12.0) * 1.15
    right_margin = max(profile.tro_m, 12.0) * 1.15
    x_left = x0 - left_margin
    x_right = x5 + right_margin

    ax.set_facecolor(tokens.bg_card)
    ax.set_title("Full Superelevation Graph", pad=12, fontsize=11, color=text_primary, fontfamily="serif")
    ax.set_xlabel("Distance, L(m)", fontsize=Y_AXIS_LABEL_FONTSIZE, color=tokens.chart_label)
    configure_superelevation_y_axis(ax)
    ax.set_xlim(x_left, x_right)

    ax.axhline(0, color=COLOR_CENTERLINE, linestyle="-.", linewidth=1.15, zorder=2)
    ax.plot([x_left, x0], [-e1, -e1], color=COLOR_ALIGNMENT, linewidth=2.0, zorder=3)
    ax.plot([x5, x_right], [-e1, -e1], color=COLOR_ALIGNMENT, linewidth=2.0, zorder=3)
    ax.plot(stations, outside_y, color=COLOR_OUTSIDE, linewidth=2.0, zorder=4)
    ax.plot(stations, inside_y, color=COLOR_INSIDE, linewidth=2.0, zorder=4)

    legend_handles = [
        Line2D([0], [0], color=COLOR_ALIGNMENT, linewidth=2.0, label="Alignment"),
        Line2D([0], [0], color=COLOR_CENTERLINE, linewidth=1.15, linestyle="-.", label="Centerline"),
        Line2D([0], [0], color=COLOR_INSIDE, linewidth=2.0, label="Inside Edge"),
        Line2D([0], [0], color=COLOR_OUTSIDE, linewidth=2.0, label="Outside Edge"),
    ]
    legend = ax.legend(
        handles=legend_handles,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        bbox_transform=ax.transAxes,
        frameon=True,
        fancybox=False,
        framealpha=1.0,
        facecolor="#ffffff",
        edgecolor=COLOR_ALIGNMENT,
        labelcolor="#111111",
        fontsize=8,
        borderpad=0.55,
        handlelength=2.2,
    )
    legend.get_frame().set_linewidth(1.25)

    station_labels = [
        (x0, "SSD"),
        (x1, "TS"),
        (x2, "SC"),
        (x3, "CS"),
        (x4, "ST"),
        (x5, "ESD"),
    ]
    label_y = Y_AXIS_MAX - 1.2
    for x, label in station_labels:
        ax.axvline(x, color=COLOR_GUIDE, linestyle="--", linewidth=0.9, zorder=1)
        ax.text(
            x,
            label_y,
            label,
            color=COLOR_MARKER,
            rotation=90,
            va="top",
            ha="right",
            fontsize=7.5,
            fontfamily="serif",
            fontweight="bold",
            zorder=5,
        )

    ax.text(
        (x0 + x1) / 2,
        -e1 - 1.1,
        "Crossfall\non straight",
        color=text_muted,
        ha="center",
        va="top",
        fontsize=7,
        fontfamily="serif",
    )
    ax.text(
        (x4 + x5) / 2,
        -e1 - 1.1,
        "Crossfall\non straight",
        color=text_muted,
        ha="center",
        va="top",
        fontsize=7,
        fontfamily="serif",
    )
    ax.text(
        (x2 + x3) / 2,
        emax + 0.55,
        "Design Superelevation",
        color=text_muted,
        ha="center",
        va="bottom",
        fontsize=7.5,
        fontfamily="serif",
    )

    mid_curve = (x2 + x3) / 2
    ax.annotate(
        "",
        xy=(mid_curve, emax),
        xytext=(mid_curve, -emax),
        arrowprops={"arrowstyle": "<->", "color": COLOR_DIM, "lw": 1.0},
        zorder=5,
    )
    ax.text(
        mid_curve + (x3 - x2) * 0.08,
        emax * 0.55,
        "Above\nDatum",
        color=text_muted,
        fontsize=6.5,
        ha="left",
        va="center",
        fontfamily="serif",
    )
    ax.text(
        mid_curve + (x3 - x2) * 0.08,
        -emax * 0.55,
        "Below\nDatum",
        color=text_muted,
        fontsize=6.5,
        ha="left",
        va="center",
        fontfamily="serif",
    )

    dim_y_top = Y_AXIS_MAX - 2.6
    dim_y_sub = Y_AXIS_MAX - 4.2
    _draw_dimension(ax, x0, x2, dim_y_top, f"Le = {profile.transition_length_m:.2f}m")
    _draw_dimension(ax, x2, x3, dim_y_top, f"Lc = {profile.curve_length_m:.2f}m")
    _draw_dimension(ax, x0, x1, dim_y_sub, f"Tro\n{profile.tro_m:.2f}m", fontsize=6.5)
    _draw_dimension(ax, x1, x2, dim_y_sub, f"Sro\n{profile.sro_m:.2f}m", fontsize=6.5)
    _draw_dimension(ax, x3, x4, dim_y_sub, f"Sro\n{profile.sro_m:.2f}m", fontsize=6.5)
    _draw_dimension(ax, x4, x5, dim_y_sub, f"Tro\n{profile.tro_m:.2f}m", fontsize=6.5)

    icon_kinds = {
        x0: "crown",
        x1: "remove_adverse",
        x2: "full_super",
        x3: "full_super",
        x4: "exit_runoff",
        x5: "crown",
    }
    for x, kind in icon_kinds.items():
        _draw_cross_section_icon(ax, x, kind=kind)

    ax.set_xticks(stations)
    ax.set_xticklabels([format_station(x) for x in stations], rotation=0, fontsize=Y_AXIS_TICK_FONTSIZE)
    ax.tick_params(axis="x", colors=tokens.chart_value, pad=18)
    for label in ax.get_xticklabels():
        label.set_fontfamily("serif")
    ax.xaxis.label.set_fontfamily("serif")
    ax.grid(True, color=tokens.chart_grid, alpha=0.45, linewidth=0.6, zorder=0)

    ax.text(
        0.5,
        -0.22,
        "Figure: Full Superelevation Graph of PI-01",
        transform=ax.transAxes,
        ha="center",
        va="top",
        color=text_muted,
        fontsize=8,
        fontfamily="serif",
        clip_on=False,
    )
