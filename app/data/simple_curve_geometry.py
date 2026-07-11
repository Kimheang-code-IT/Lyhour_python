"""Geometric horizontal simple curve elements (PC–PI–PT)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SimpleCurveElements:
    radius_m: float
    deflection_deg: float
    tangent_length_m: float
    curve_length_m: float
    chord_length_m: float
    external_distance_m: float
    middle_ordinate_m: float

    @property
    def deflection_rad(self) -> float:
        return math.radians(self.deflection_deg)


def format_angle_dms(degrees: float) -> str:
    """Format decimal degrees as D°-M'S.S\" (e.g. 79-14'55.17\")."""
    total = abs(float(degrees))
    d = int(total)
    minutes_float = (total - d) * 60.0
    m = int(minutes_float)
    s = (minutes_float - m) * 60.0
    return f"{d}-{m:02d}'{s:05.2f}\""


def compute_simple_curve_elements(radius_m: float, deflection_deg: float) -> SimpleCurveElements | None:
    """Compute TL, L, C, E, M from radius R and deflection angle Δ (degrees)."""
    radius = float(radius_m)
    deflection = float(deflection_deg)
    if radius <= 0 or deflection <= 0 or deflection >= 180:
        return None

    half_rad = math.radians(deflection / 2.0)
    return SimpleCurveElements(
        radius_m=radius,
        deflection_deg=deflection,
        tangent_length_m=radius * math.tan(half_rad),
        curve_length_m=radius * math.radians(deflection),
        chord_length_m=2.0 * radius * math.sin(half_rad),
        external_distance_m=(radius / math.cos(half_rad)) - radius,
        middle_ordinate_m=radius * (1.0 - math.cos(half_rad)),
    )


def draw_simple_curve_diagram(
    ax: Any,
    elements: SimpleCurveElements,
    *,
    title: str = "Geometric Horizontal of Simple Curve Elements",
) -> None:
    """Draw a schematic PC–PI–PT curve matching standard road-geometry diagrams."""
    import matplotlib.patches as patches

    from app.core.theme import theme_tokens

    tokens = theme_tokens()
    struct_line = tokens.chart_label
    text_primary = tokens.chart_label

    half_rad = math.radians(elements.deflection_deg / 2.0)
    tl = elements.tangent_length_m
    radius = elements.radius_m

    # PI at apex; symmetric curve opening downward.
    pi = np.array([0.0, 0.0])
    pc = np.array([-tl * math.sin(half_rad), -tl * math.cos(half_rad)])
    pt = np.array([tl * math.sin(half_rad), -tl * math.cos(half_rad)])

    pc_x = abs(float(pc[0]))
    center_y = float(pc[1]) - math.sqrt(radius**2 - pc_x**2)
    center = np.array([0.0, center_y])

    inc_dir = (pi - pc) / tl
    out_dir = (pt - pi) / tl
    ext_len = tl * 0.45
    inc_ext = pc - inc_dir * ext_len
    out_ext = pt + out_dir * ext_len

    angle_pc = math.atan2(pc[1] - center_y, pc[0])
    angle_pt = math.atan2(pt[1] - center_y, pt[0])
    arc_t = np.linspace(angle_pc, angle_pt, 240)
    arc_x = center[0] + radius * np.cos(arc_t)
    arc_y = center[1] + radius * np.sin(arc_t)
    arc_mid = np.array([0.0, center_y + radius])

    chord_mid = (pc + pt) / 2.0
    ordinate_mid = np.array([0.0, float(chord_mid[1]) - elements.middle_ordinate_m])
    external_point = np.array([0.0, center_y + radius])

    pad_x = tl * 0.55
    pad_y = tl * 0.35
    x_min = min(pc[0], inc_ext[0], center[0] - radius) - pad_x
    x_max = max(pt[0], out_ext[0], center[0] + radius) + pad_x
    y_min = center_y - radius * 0.22
    y_max = tl * 0.18

    ax.set_facecolor(tokens.bg_card)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.axis("off")
    ax.set_title(title, color=text_primary, fontsize=11, fontweight="bold", pad=10)

    red = "#d71920"
    blue = "#1f4e9a"
    brown = "#c49a6c"
    green = "#2d8f2d"
    orange = "#d65a00"

    # Tangent extensions (approach / departure).
    ax.plot([inc_ext[0], pc[0]], [inc_ext[1], pc[1]], color=blue, linewidth=2.0, solid_capstyle="round")
    ax.plot([pt[0], out_ext[0]], [pt[1], out_ext[1]], color=blue, linewidth=2.0, solid_capstyle="round")

    # Main tangents.
    ax.plot([pc[0], pi[0]], [pc[1], pi[1]], color=red, linewidth=2.6, solid_capstyle="round")
    ax.plot([pi[0], pt[0]], [pi[1], pt[1]], color=red, linewidth=2.6, solid_capstyle="round")

    # Circular curve.
    ax.plot(arc_x, arc_y, color=red, linewidth=2.2, solid_capstyle="round")

    # Radius lines to PC and PT.
    ax.plot([center[0], pc[0]], [center[1], pc[1]], color=struct_line, linewidth=1.2)
    ax.plot([center[0], pt[0]], [center[1], pt[1]], color=struct_line, linewidth=1.2)

    # Long chord.
    ax.plot([pc[0], pt[0]], [pc[1], pt[1]], color=struct_line, linewidth=1.8)
    ax.text(
        0.0,
        float(chord_mid[1]) + tl * 0.045,
        f"{elements.chord_length_m:.3f}",
        color=brown,
        fontsize=9,
        ha="center",
        va="bottom",
        fontweight="bold",
    )

    # External distance E (PI to curve along bisector).
    ax.annotate(
        "",
        xy=external_point,
        xytext=pi,
        arrowprops={"arrowstyle": "-|>", "color": green, "lw": 1.6, "mutation_scale": 12},
    )
    ax.text(
        tl * 0.06,
        (pi[1] + external_point[1]) / 2.0,
        f"E {elements.external_distance_m:.3f}",
        color=orange,
        fontsize=9,
        ha="left",
        va="center",
        fontweight="bold",
    )

    # Middle ordinate M.
    ax.annotate(
        "",
        xy=ordinate_mid,
        xytext=chord_mid,
        arrowprops={"arrowstyle": "<->", "color": blue, "lw": 1.4, "mutation_scale": 10},
    )
    ax.text(
        tl * 0.05,
        float(ordinate_mid[1] + chord_mid[1]) / 2.0,
        f"M {elements.middle_ordinate_m:.3f}",
        color=text_primary,
        fontsize=9,
        ha="left",
        va="center",
        fontweight="bold",
    )

    # Tangent length labels on both tangents.
    left_mid = (pi + pc) / 2.0
    right_mid = (pi + pt) / 2.0
    tl_label = f"TL {elements.tangent_length_m:.3f}"
    ax.text(
        float(left_mid[0]) - tl * 0.04,
        float(left_mid[1]),
        tl_label,
        color=red,
        fontsize=8.5,
        ha="right",
        va="center",
        rotation=math.degrees(math.atan2(pc[1] - pi[1], pc[0] - pi[0])),
        rotation_mode="anchor",
    )
    ax.text(
        float(right_mid[0]) + tl * 0.04,
        float(right_mid[1]),
        tl_label,
        color=red,
        fontsize=8.5,
        ha="left",
        va="center",
        rotation=math.degrees(math.atan2(pt[1] - pi[1], pt[0] - pi[0])),
        rotation_mode="anchor",
    )

    # Curve length along arc.
    label_angle = (angle_pc + angle_pt) / 2.0
    label_r = radius + tl * 0.08
    lcc_x = center[0] + label_r * math.cos(label_angle)
    lcc_y = center[1] + label_r * math.sin(label_angle)
    ax.text(
        lcc_x,
        lcc_y,
        f"Lcc (L) {elements.curve_length_m:.2f}",
        color=text_primary,
        fontsize=9,
        ha="center",
        va="center",
        fontweight="bold",
        bbox={"facecolor": tokens.bg_card, "edgecolor": "none", "pad": 1.0, "alpha": 0.85},
    )

    # Radius label at center.
    ax.text(
        0.0,
        center_y - radius * 0.12,
        f"Radius(R) {radius:.3f}",
        color=red,
        fontsize=10,
        ha="center",
        va="top",
        fontweight="bold",
    )

    # Deflection angle at PI.
    angle_arc = patches.Arc(
        pi,
        tl * 0.34,
        tl * 0.34,
        angle=0,
        theta1=-90.0 - math.degrees(half_rad),
        theta2=-90.0 + math.degrees(half_rad),
        color=green,
        linewidth=1.4,
    )
    ax.add_patch(angle_arc)
    ax.text(
        tl * 0.18,
        -tl * 0.06,
        format_angle_dms(elements.deflection_deg),
        color=blue,
        fontsize=10,
        ha="left",
        va="top",
        fontweight="bold",
    )

    # Point labels.
    station_style = {"fontsize": 9, "color": text_primary, "fontweight": "bold", "ha": "center"}
    ax.plot(pi[0], pi[1], "o", color=red, markersize=5, zorder=5)
    ax.text(float(pc[0]), float(pc[1]) - tl * 0.05, "Pc Station", va="top", **station_style)
    ax.text(float(pi[0]), float(pi[1]) + tl * 0.04, "PI Station", va="bottom", **station_style)
    ax.text(float(pt[0]), float(pt[1]) - tl * 0.05, "PT Station", va="top", **station_style)
