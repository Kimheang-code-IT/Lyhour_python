"""Superelevation transition profile calculations and chart drawing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SuperelevationProfile:
    e1_percent: float
    e_max_percent: float
    lane_width_m: float
    relative_gradient_percent: float
    curve_length_m: float
    start_station_m: float
    transition_length_m: float
    tro_m: float
    sro_m: float

    @property
    def ts_station_m(self) -> float:
        return self.start_station_m + self.tro_m

    @property
    def sc_station_m(self) -> float:
        return self.start_station_m + self.transition_length_m

    @property
    def cs_station_m(self) -> float:
        return self.sc_station_m + self.curve_length_m

    @property
    def st_station_m(self) -> float:
        return self.cs_station_m + self.sro_m

    @property
    def end_station_m(self) -> float:
        return self.st_station_m + self.tro_m


def compute_superelevation_profile(
    *,
    e1_percent: float,
    e_max_percent: float,
    lane_width_m: float,
    relative_gradient_percent: float,
    curve_length_m: float,
    start_station_m: float,
) -> SuperelevationProfile | None:
    """Compute runoff/runout lengths for a full superelevation profile."""
    e1 = abs(float(e1_percent))
    e_max = abs(float(e_max_percent))
    lane_width = float(lane_width_m)
    relative_gradient = float(relative_gradient_percent) / 100.0
    curve_length = max(0.0, float(curve_length_m))
    start_station = float(start_station_m)

    if lane_width <= 0 or relative_gradient <= 0:
        return None

    tro = lane_width * (e1 / 100.0) / relative_gradient
    transition_length = lane_width * ((e1 + e_max) / 100.0) / relative_gradient
    sro = max(0.0, transition_length - tro)

    return SuperelevationProfile(
        e1_percent=e1,
        e_max_percent=e_max,
        lane_width_m=lane_width,
        relative_gradient_percent=float(relative_gradient_percent),
        curve_length_m=curve_length,
        start_station_m=start_station,
        transition_length_m=transition_length,
        tro_m=tro,
        sro_m=sro,
    )


def format_station(distance_m: float) -> str:
    """Format chainage as 16+200 style."""
    distance = max(0.0, float(distance_m))
    km = int(distance // 1000)
    metres = distance - (km * 1000)
    return f"{km}+{metres:06.2f}" if metres % 1 else f"{km}+{int(metres):03d}"


Y_AXIS_MIN = -10.0
Y_AXIS_MAX = 15.0
Y_AXIS_TICK_STEP = 2.5
Y_AXIS_TICK_FONTSIZE = 7
Y_AXIS_LABEL_FONTSIZE = 8


def _format_y_tick(value: float) -> str:
    rounded = round(float(value) * 2) / 2
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.1f}"


def configure_superelevation_y_axis(ax: Any) -> None:
    """Fixed Y scale matching road-design drawings: -10 to 15 % at 2.5 intervals."""
    import numpy as np

    yticks = np.arange(Y_AXIS_MIN, Y_AXIS_MAX + Y_AXIS_TICK_STEP / 2, Y_AXIS_TICK_STEP)
    ax.set_ylim(Y_AXIS_MIN, Y_AXIS_MAX)
    ax.set_yticks(yticks)
    ax.set_yticklabels([_format_y_tick(y) for y in yticks])
    ax.set_ylabel("Superelevation, e(%)", fontsize=Y_AXIS_LABEL_FONTSIZE)

    ax.tick_params(axis="y", labelsize=Y_AXIS_TICK_FONTSIZE, length=3, width=0.6, pad=2)
    ax.yaxis.label.set_fontfamily("serif")
    for label in ax.get_yticklabels():
        label.set_fontfamily("serif")


def draw_superelevation_profile(ax: Any, profile: SuperelevationProfile) -> None:
    """Draw a full superelevation graph similar to the road design reference."""
    from matplotlib.lines import Line2D

    x0 = profile.start_station_m
    x1 = profile.ts_station_m
    x2 = profile.sc_station_m
    x3 = profile.cs_station_m
    x4 = profile.st_station_m
    x5 = profile.end_station_m
    left_margin = max(profile.tro_m, 10.0) * 0.8
    right_margin = max(profile.tro_m, 10.0) * 0.8

    e1 = profile.e1_percent
    emax = profile.e_max_percent
    chart_top = Y_AXIS_MAX - 1.0

    ax.set_title("Full Superelevation Graph", pad=10, fontsize=10)
    ax.set_xlabel("Distance, L(m)", fontsize=Y_AXIS_LABEL_FONTSIZE)
    configure_superelevation_y_axis(ax)
    ax.set_xlim(x0 - left_margin, x5 + right_margin)

    ax.axhline(0, color="#c44f4f", linestyle="--", linewidth=1.0, dashes=(4, 3))

    outside_x = [x0, x1, x2, x3, x5]
    outside_y = [-e1, -e1, emax, emax, -e1]
    inside_x = [x0, x1, x2, x3, x4, x5]
    inside_y = [-e1, -e1, -emax, -emax, -e1, -e1]
    alignment_x = [x1, x2, x3, x4]
    alignment_y = [chart_top, chart_top, chart_top, chart_top]

    ax.plot(alignment_x, alignment_y, color="#1f77b4", linewidth=1.8)
    ax.plot(inside_x, inside_y, color="#2ca02c", linewidth=1.8)
    ax.plot(outside_x, outside_y, color="#d87b3d", linewidth=1.8)

    legend_handles = [
        Line2D([0], [0], color="#1f77b4", linewidth=1.8, label="Alignment"),
        Line2D([0], [0], color="#c44f4f", linewidth=1.0, linestyle="--", label="Centerline"),
        Line2D([0], [0], color="#2ca02c", linewidth=1.8, label="Inside Edge"),
        Line2D([0], [0], color="#d87b3d", linewidth=1.8, label="Outside Edge"),
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
        edgecolor="#1f77b4",
        labelcolor="#111111",
        fontsize=8,
        borderpad=0.5,
        handlelength=2.0,
    )
    legend.get_frame().set_linewidth(1.2)

    labels = [
        (x0, "SSD"),
        (x1, "TS"),
        (x2, "SC"),
        (x3, "CS"),
        (x4, "ST"),
        (x5, "ESD"),
    ]
    for x, label in labels:
        ax.axvline(x, color="#777777", linestyle="--", linewidth=1.0)
        ax.text(x, 6.5, label, color="#d65f5f", rotation=90, va="center", ha="center", fontsize=7)

    ax.text((x0 + x1) / 2, -e1 - 0.8, "Crossfall\non straight", color="#d8d8d8", ha="center", va="top", fontsize=7)
    ax.text((x2 + x3) / 2, emax + 0.4, "Design Superelevation", color="#d8d8d8", ha="center", fontsize=7)

    arrow_y = chart_top - 0.8
    ax.annotate(
        f"Le = {profile.transition_length_m:.2f}m",
        xy=(x0, arrow_y),
        xytext=(x2, arrow_y),
        arrowprops={"arrowstyle": "<->", "color": "#4da3ff"},
        color="#d65f5f",
        fontsize=7,
        ha="center",
        va="bottom",
    )
    ax.annotate(
        f"Lc = {profile.curve_length_m:.2f}m",
        xy=(x2, arrow_y),
        xytext=(x3, arrow_y),
        arrowprops={"arrowstyle": "<->", "color": "#4da3ff"},
        color="#d65f5f",
        fontsize=7,
        ha="center",
        va="bottom",
    )

    label_y = chart_top - 2.0
    ax.text((x0 + x1) / 2, label_y, f"Tro\n{profile.tro_m:.2f}m", color="#d65f5f", ha="center", fontsize=7)
    ax.text((x1 + x2) / 2, label_y, f"Sro\n{profile.sro_m:.2f}m", color="#d65f5f", ha="center", fontsize=7)
    ax.text((x3 + x4) / 2, label_y, f"Sro\n{profile.sro_m:.2f}m", color="#d65f5f", ha="center", fontsize=7)
    ax.text((x4 + x5) / 2, label_y, f"Tro\n{profile.tro_m:.2f}m", color="#d65f5f", ha="center", fontsize=7)

    tick_positions = [x0, x1, x2, x3, x4, x5]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([format_station(x) for x in tick_positions], rotation=0, fontsize=Y_AXIS_TICK_FONTSIZE)
    for label in ax.get_xticklabels():
        label.set_fontfamily("serif")
    ax.xaxis.label.set_fontfamily("serif")
    ax.grid(True, color="#555555", alpha=0.35, linewidth=0.6)
    ax.text(
        0.5,
        -0.14,
        "Figure: Full Superelevation Graph of PI-01",
        transform=ax.transAxes,
        ha="center",
        va="top",
        color="#cccccc",
        fontsize=8,
    )
