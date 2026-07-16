"""Geometric horizontal simple curve elements (PC–PI–PT)."""
from __future__ import annotations

import math
from dataclasses import dataclass


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
