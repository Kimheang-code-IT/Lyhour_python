"""Superelevation transition profile calculations."""
from __future__ import annotations

from dataclasses import dataclass


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
    """Compute runoff/runout lengths for a full superelevation profile.

    Tro = WR × e1 / relative_gradient
    Le  = WR × (e1 + e_max) / relative_gradient
    Sro = Le − Tro
    """
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
