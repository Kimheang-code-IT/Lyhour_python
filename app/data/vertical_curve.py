"""Equal-tangent parabolic vertical curve (AASHTO 1993/2018 geometry)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CurveType = Literal["Crest", "Sag"]
SightCriterion = Literal["Stopping SD", "Passing SD", "Decision SD"]

# AASHTO Green Book (metric) K for stopping sight distance.
_K_CREST_SSD = {
    20: 1.0,
    30: 2.0,
    40: 4.0,
    50: 7.0,
    60: 11.0,
    70: 17.0,
    80: 26.0,
    90: 39.0,
    100: 52.0,
    110: 74.0,
    120: 102.0,
    130: 139.0,
}
_K_SAG_SSD = {
    20: 3.0,
    30: 6.0,
    40: 9.0,
    50: 13.0,
    60: 18.0,
    70: 23.0,
    80: 30.0,
    90: 38.0,
    100: 45.0,
    110: 55.0,
    120: 63.0,
    130: 72.0,
}
_K_CREST_PASSING = {
    20: 8.0,
    30: 17.0,
    40: 36.0,
    50: 62.0,
    60: 102.0,
    70: 154.0,
    80: 222.0,
    90: 303.0,
    100: 407.0,
    110: 529.0,
    120: 694.0,
    130: 884.0,
}
_SSD_M = {
    20: 20.0,
    30: 35.0,
    40: 50.0,
    50: 65.0,
    60: 85.0,
    70: 105.0,
    80: 130.0,
    90: 160.0,
    100: 185.0,
    110: 220.0,
    120: 250.0,
    130: 285.0,
}

DESIGN_SPEEDS = tuple(sorted(_K_CREST_SSD))
CURVE_TYPE_OPTIONS = ("Crest", "Sag")
SIGHT_CRITERION_OPTIONS = ("Stopping SD", "Passing SD", "Decision SD")
STANDARD_OPTIONS = ("AASHTO 2018",)


@dataclass(frozen=True)
class StakeoutRow:
    station_m: float
    tangent_elev_m: float
    correction_y_m: float
    curve_elev_m: float


@dataclass(frozen=True)
class VerticalCurveResult:
    curve_type: CurveType
    g1_percent: float
    g2_percent: float
    a_percent: float
    a_signed: float
    length_m: float
    k_provided: float | None
    k_required: float | None
    sight_distance_m: float | None
    pvi_station_m: float
    pvi_elev_m: float
    pvc_station_m: float
    pvc_elev_m: float
    pvt_station_m: float
    pvt_elev_m: float
    turning_station_m: float | None
    turning_elev_m: float | None
    design_ok: bool | None
    profile_x_m: tuple[float, ...]
    profile_y_m: tuple[float, ...]
    tangent_in_x_m: tuple[float, float]
    tangent_in_y_m: tuple[float, float]
    tangent_out_x_m: tuple[float, float]
    tangent_out_y_m: tuple[float, float]
    stakeout: tuple[StakeoutRow, ...]


def format_station(distance_m: float) -> str:
    """Format chainage as 1+250.00."""
    sign = "-" if distance_m < 0 else ""
    distance = abs(float(distance_m))
    km = int(distance // 1000)
    metres = distance - km * 1000
    return f"{sign}{km}+{metres:06.2f}"


def classify_curve(g1_percent: float, g2_percent: float) -> CurveType | None:
    delta = float(g2_percent) - float(g1_percent)
    if abs(delta) < 1e-9:
        return None
    return "Sag" if delta > 0 else "Crest"


def algebraic_difference(g1_percent: float, g2_percent: float) -> float:
    return abs(float(g2_percent) - float(g1_percent))


def _lerp_table(table: dict[int, float], speed_kmh: float) -> float:
    speed = max(float(speed_kmh), float(DESIGN_SPEEDS[0]))
    speed = min(speed, float(DESIGN_SPEEDS[-1]))
    keys = list(DESIGN_SPEEDS)
    if speed in table:
        return float(table[int(speed)])
    lo = keys[0]
    hi = keys[-1]
    for a, b in zip(keys, keys[1:]):
        if a <= speed <= b:
            lo, hi = a, b
            break
    t = (speed - lo) / (hi - lo) if hi != lo else 0.0
    return table[lo] + t * (table[hi] - table[lo])


def required_k(
    *,
    speed_kmh: float,
    curve_type: CurveType,
    sight_criterion: SightCriterion,
) -> float:
    if curve_type == "Crest" and sight_criterion == "Passing SD":
        return _lerp_table(_K_CREST_PASSING, speed_kmh)
    k_ssd = _lerp_table(_K_CREST_SSD if curve_type == "Crest" else _K_SAG_SSD, speed_kmh)
    if sight_criterion == "Decision SD":
        return k_ssd * 1.8
    return k_ssd


def sight_distance_m(speed_kmh: float, sight_criterion: SightCriterion) -> float:
    ssd = _lerp_table(_SSD_M, speed_kmh)
    if sight_criterion == "Passing SD":
        return ssd * 1.7
    if sight_criterion == "Decision SD":
        return ssd * 1.4
    return ssd


def curve_elevation(x_from_pvc: float, *, pvc_elev_m: float, g1_percent: float, a_signed: float, length_m: float) -> float:
    """E(x) = E_PVC + (g1/100)x + (A_signed /(200 L)) x²."""
    x = float(x_from_pvc)
    length = max(float(length_m), 1e-9)
    return (
        float(pvc_elev_m)
        + (float(g1_percent) / 100.0) * x
        + (float(a_signed) / (200.0 * length)) * x * x
    )


def compute_vertical_curve(
    *,
    curve_type: CurveType,
    g1_percent: float,
    g2_percent: float,
    pvi_station_m: float,
    pvi_elev_m: float,
    length_m: float | None = None,
    target_k: float | None = None,
    speed_kmh: float = 80.0,
    sight_criterion: SightCriterion = "Stopping SD",
    stakeout_interval_m: float = 10.0,
) -> VerticalCurveResult:
    g1 = float(g1_percent)
    g2 = float(g2_percent)
    a_signed = g2 - g1
    a_abs = abs(a_signed)
    classified = classify_curve(g1, g2)
    selected: CurveType = curve_type
    if classified is not None:
        selected = classified

    if target_k is not None and (length_m is None or length_m <= 0):
        length = max(float(target_k) * a_abs, 1.0) if a_abs > 1e-9 else 1.0
    else:
        length = max(float(length_m or 0.0), 1.0)

    half = length / 2.0
    pvc_sta = float(pvi_station_m) - half
    pvt_sta = float(pvi_station_m) + half
    pvc_elev = float(pvi_elev_m) - (g1 / 100.0) * half
    pvt_elev = float(pvi_elev_m) + (g2 / 100.0) * half

    k_prov = (length / a_abs) if a_abs > 1e-9 else None
    k_req = required_k(speed_kmh=speed_kmh, curve_type=selected, sight_criterion=sight_criterion)
    sd = sight_distance_m(speed_kmh, sight_criterion)
    design_ok = None if k_prov is None else k_prov + 1e-9 >= k_req

    turning_sta = None
    turning_elev = None
    if abs(a_signed) > 1e-9:
        x_hl = -g1 * length / a_signed
        if 0.0 < x_hl < length:
            turning_sta = pvc_sta + x_hl
            turning_elev = curve_elevation(
                x_hl, pvc_elev_m=pvc_elev, g1_percent=g1, a_signed=a_signed, length_m=length
            )

    samples = 80
    xs = [i * length / samples for i in range(samples + 1)]
    ys = [
        curve_elevation(x, pvc_elev_m=pvc_elev, g1_percent=g1, a_signed=a_signed, length_m=length)
        for x in xs
    ]
    profile_x = tuple(pvc_sta + x for x in xs)
    profile_y = tuple(ys)

    extend = max(length * 0.22, 12.0)
    tan_in_x = (pvc_sta - extend, float(pvi_station_m))
    tan_in_y = (
        pvc_elev - (g1 / 100.0) * extend,
        float(pvi_elev_m),
    )
    tan_out_x = (float(pvi_station_m), pvt_sta + extend)
    tan_out_y = (
        float(pvi_elev_m),
        pvt_elev + (g2 / 100.0) * extend,
    )

    interval = max(float(stakeout_interval_m), 1.0)
    stations: list[float] = []
    sta = pvc_sta
    while sta < pvt_sta - 1e-9:
        stations.append(sta)
        sta += interval
    stations.append(pvt_sta)
    if abs(float(pvi_station_m) - pvc_sta) > 1e-6:
        stations.append(float(pvi_station_m))
    if turning_sta is not None:
        stations.append(turning_sta)
    unique = sorted({round(s, 5) for s in stations})

    rows: list[StakeoutRow] = []
    for station in unique:
        x = station - pvc_sta
        tan_elev = pvc_elev + (g1 / 100.0) * x
        y_off = (a_signed / (200.0 * length)) * x * x
        rows.append(
            StakeoutRow(
                station_m=station,
                tangent_elev_m=tan_elev,
                correction_y_m=y_off,
                curve_elev_m=tan_elev + y_off,
            )
        )

    return VerticalCurveResult(
        curve_type=selected,
        g1_percent=g1,
        g2_percent=g2,
        a_percent=a_abs,
        a_signed=a_signed,
        length_m=length,
        k_provided=k_prov,
        k_required=k_req,
        sight_distance_m=sd,
        pvi_station_m=float(pvi_station_m),
        pvi_elev_m=float(pvi_elev_m),
        pvc_station_m=pvc_sta,
        pvc_elev_m=pvc_elev,
        pvt_station_m=pvt_sta,
        pvt_elev_m=pvt_elev,
        turning_station_m=turning_sta,
        turning_elev_m=turning_elev,
        design_ok=design_ok,
        profile_x_m=profile_x,
        profile_y_m=profile_y,
        tangent_in_x_m=tan_in_x,
        tangent_in_y_m=tan_in_y,
        tangent_out_x_m=tan_out_x,
        tangent_out_y_m=tan_out_y,
        stakeout=tuple(rows),
    )
