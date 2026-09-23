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


@dataclass(frozen=True)
class StakeoutPoint:
    """One staked point of a simple horizontal curve (local PC origin frame)."""

    name: str
    station_m: float
    arc_length_m: float | None
    deflection_deg: float | None
    chord_m: float | None
    x_m: float
    y_m: float


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


def compute_curve_stakeout(
    radius_m: float,
    deflection_deg: float,
    *,
    pc_station_m: float = 0.0,
    interval_m: float = 20.0,
) -> tuple[StakeoutPoint, ...]:
    """Stake PC, intermediate arc points, PT, and the off-curve PI control point.

    Local frame: PC at the origin, incoming tangent along +X, curve turning left
    (center at (0, R)). Coordinates: x = R·sinθ, y = R·(1 − cosθ).
    """
    elements = compute_simple_curve_elements(radius_m, deflection_deg)
    if elements is None:
        return ()

    radius = elements.radius_m
    total = elements.curve_length_m
    pc_station = float(pc_station_m)
    interval = max(float(interval_m), 1.0)

    offsets: list[float] = []
    arc = 0.0
    while arc < total - 1e-9:
        offsets.append(arc)
        arc += interval
    offsets.append(total)

    rows: list[StakeoutPoint] = []
    for arc in offsets:
        theta = arc / radius
        if arc <= 1e-9:
            name = "PC"
        elif abs(arc - total) <= 1e-6:
            name = "PT"
        else:
            name = ""
        rows.append(
            StakeoutPoint(
                name=name,
                station_m=pc_station + arc,
                arc_length_m=arc,
                deflection_deg=math.degrees(theta / 2.0),
                chord_m=2.0 * radius * math.sin(theta / 2.0),
                x_m=radius * math.sin(theta),
                y_m=radius * (1.0 - math.cos(theta)),
            )
        )

    rows.append(
        StakeoutPoint(
            name="PI",
            station_m=pc_station + elements.tangent_length_m,
            arc_length_m=None,
            deflection_deg=None,
            chord_m=None,
            x_m=elements.tangent_length_m,
            y_m=0.0,
        )
    )
    return tuple(rows)
