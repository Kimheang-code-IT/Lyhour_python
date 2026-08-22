"""Parabolic vertical-curve profile diagram (crest / sag)."""
from __future__ import annotations

from typing import Any

import numpy as np

from app.chart.base import apply_axes_theme, draw_empty_message
from app.core.theme import theme_tokens
from app.data.vertical_curve import VerticalCurveResult, format_station


def draw_vertical_curve(
    ax: Any,
    result: VerticalCurveResult | None,
    *,
    show_tangents: bool = True,
    show_turning_point: bool = True,
    show_existing_ground: bool = False,
    show_sd_envelope: bool = True,
) -> None:
    tokens = theme_tokens()
    ax.clear()
    if result is None or result.length_m <= 0:
        draw_empty_message(ax, "Enter grades and length to draw the vertical curve.")
        return

    apply_axes_theme(ax)
    curve_color = "#f3f4f6"
    tangent_color = "#6ea8ff"
    pvi_color = "#e8b84a"
    marker_color = "#ffffff"
    sag_beam = "#f0d56a"
    crest_sight = "#7ad0ff"

    x = np.array(result.profile_x_m)
    y = np.array(result.profile_y_m)
    ax.plot(x, y, color=curve_color, linewidth=2.4, solid_capstyle="round", zorder=4)

    if show_tangents:
        ax.plot(
            result.tangent_in_x_m,
            result.tangent_in_y_m,
            color=tangent_color,
            linewidth=1.5,
            linestyle="--",
            zorder=3,
        )
        ax.plot(
            result.tangent_out_x_m,
            result.tangent_out_y_m,
            color=tangent_color,
            linewidth=1.5,
            linestyle="--",
            zorder=3,
        )
        ax.plot(
            [result.pvc_station_m, result.pvi_station_m, result.pvt_station_m],
            [result.pvc_elev_m, result.pvi_elev_m, result.pvt_elev_m],
            color="#8a8a8a",
            linewidth=1.1,
            linestyle=":",
            zorder=2,
        )
        ax.plot(
            [result.pvi_station_m, result.pvi_station_m],
            [result.pvi_elev_m, np.interp(result.pvi_station_m, x, y)],
            color=pvi_color,
            linewidth=1.0,
            linestyle="--",
            zorder=3,
        )

    if show_existing_ground:
        noise = 0.12 * np.sin((x - x[0]) / max(result.length_m, 1.0) * 7.0)
        offset = -0.35 if result.curve_type == "Crest" else 0.35
        ax.plot(x, y + offset + noise, color="#7a6a55", linewidth=1.1, linestyle="-.", zorder=1)

    if show_sd_envelope and result.sight_distance_m:
        _draw_sd_envelope(ax, result, x, y, crest_sight, sag_beam)

    points = (
        ("PVC", result.pvc_station_m, result.pvc_elev_m, "left"),
        ("PVI", result.pvi_station_m, result.pvi_elev_m, "center"),
        ("PVT", result.pvt_station_m, result.pvt_elev_m, "right"),
    )
    for name, sta, elev, align in points:
        ax.scatter([sta], [elev], s=36, color=marker_color, zorder=6, edgecolors=pvi_color, linewidths=0.8)
        ha = {"left": "right", "right": "left", "center": "center"}[align]
        dx = -8 if align == "left" else 8 if align == "right" else 0
        ax.annotate(
            f"{name}\nSta. {format_station(sta)}\nElv. {elev:.2f}",
            xy=(sta, elev),
            xytext=(dx, 14),
            textcoords="offset points",
            ha=ha,
            va="bottom",
            color=tokens.chart_label,
            fontsize=8,
            zorder=7,
        )

    if show_turning_point and result.turning_station_m is not None and result.turning_elev_m is not None:
        label = "High Point" if result.curve_type == "Crest" else "Low Point"
        ax.scatter(
            [result.turning_station_m],
            [result.turning_elev_m],
            s=42,
            color="#4caf7a",
            zorder=6,
            marker="D",
        )
        ax.annotate(
            f"{label}\nSta. {format_station(result.turning_station_m)}\nElv. {result.turning_elev_m:.2f}",
            xy=(result.turning_station_m, result.turning_elev_m),
            xytext=(0, -28 if result.curve_type == "Crest" else 14),
            textcoords="offset points",
            ha="center",
            va="top" if result.curve_type == "Crest" else "bottom",
            color="#8ee0b0",
            fontsize=8,
            zorder=7,
        )

    title = f"{result.curve_type} Vertical Curve  (parabolic)"
    ax.set_title(title, color=tokens.chart_label, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel("Station", color=tokens.chart_label)
    ax.set_ylabel("Elevation (m)", color=tokens.chart_label)

    ticks = np.linspace(x[0], x[-1], 5)
    ax.set_xticks(ticks)
    ax.set_xticklabels([format_station(v) for v in ticks], fontsize=8)

    y_min = min(float(np.min(y)), result.pvi_elev_m, result.pvc_elev_m, result.pvt_elev_m)
    y_max = max(float(np.max(y)), result.pvi_elev_m, result.pvc_elev_m, result.pvt_elev_m)
    pad = max((y_max - y_min) * 0.28, 0.8)
    ax.set_ylim(y_min - pad, y_max + pad)
    ax.margins(x=0.06)


def _draw_sd_envelope(ax, result: VerticalCurveResult, x, y, crest_color: str, sag_color: str) -> None:
    sd = min(float(result.sight_distance_m or 0.0), result.length_m)
    if sd <= 1.0:
        return
    mid = result.pvi_station_m
    x1 = mid - sd / 2.0
    x2 = mid + sd / 2.0
    if x1 < x[0] or x2 > x[-1]:
        x1 = float(x[0])
        x2 = float(x[-1])
    y1 = float(np.interp(x1, x, y))
    y2 = float(np.interp(x2, x, y))
    if result.curve_type == "Crest":
        ax.plot([x1, x2], [y1 + 1.08, y2 + 0.60], color=crest_color, linewidth=1.2, linestyle="--", zorder=5)
        ax.annotate("SD envelope", xy=((x1 + x2) / 2.0, (y1 + y2) / 2.0 + 0.9), color=crest_color, fontsize=8, ha="center")
    else:
        ax.plot([x1, x2], [y1 + 0.60, y2 + 0.60 + 0.0175 * sd], color=sag_color, linewidth=1.2, linestyle="--", zorder=5)
        ax.annotate(
            "Headlight beam limit",
            xy=((x1 + x2) / 2.0, y1 + 1.1),
            color=sag_color,
            fontsize=8,
            ha="center",
        )
