"""
Minimum radius (R_min) formula and table lookup for horizontal curve design.
R_min = V² / (127 * (e + f)); e in decimal (superelevation % / 100).

Excel logic:
- IF(E7="Sealed roads") → Rmin_Table from Table 7.6 (INDEX/MATCH on M5:T16, L5:L16, M4:T4)
- Else → Rmin_Table from Table 7.7 (INDEX/MATCH on M22:T31, L22:L31, M21:T21)
"""

from typing import Optional

# Table 7.6: Minimum Horizontal Curve Radius on Sealed Pavement (m)
TABLE_7_6_SPEEDS = [130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20]
TABLE_7_6_E_RATES = [0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
TABLE_7_6_GRID = [
    [634, 665, 700, 741, 787, 840, 901, 972],
    [538, 565, 595, 629, 668, 713, 765, 825],
    [452, 475, 500, 530, 562, 600, 644, 694],
    [375, 394, 415, 439, 467, 498, 534, 576],
    [303, 319, 336, 356, 378, 404, 433, 467],
    [240, 252, 266, 282, 300, 320, 343, 370],
    [184, 194, 204, 216, 230, 246, 264, 284],
    [135, 142, 150, 159, 169, 180, 193, 208],
    [94, 99, 104, 110, 117, 125, 134, 145],
    [60, 63, 67, 71, 75, 80, 86, 93],
    [34, 35, 37, 40, 42, 45, 49, 52],
    [15, 16, 17, 18, 19, 20, 22, 23],
]
TABLE_7_6_GRID[4][5] = 354.0

# Table 7.7: Minimum Horizontal Curve Radius on Unsealed Pavement (m)
TABLE_7_7_SPEEDS = [110, 100, 90, 80, 70, 60, 50, 40, 30, 25]
TABLE_7_7_E_RATES = [0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
TABLE_7_7_GRID = [
    [530, 560, 595, 634, 678, 728, 785, 851],
    [438, 463, 492, 525, 562, 604, 652, 707],
    [356, 376, 400, 427, 458, 493, 532, 577],
    [283, 299, 318, 339, 364, 391, 422, 458],
    [217, 229, 244, 260, 279, 300, 324, 351],
    [158, 167, 178, 190, 204, 219, 236, 256],
    [106, 112, 119, 127, 136, 146, 158, 171],
    [63, 67, 71, 76, 81, 87, 94, 102],
    [28, 30, 32, 34, 36, 39, 42, 46],
    [20, 21, 22, 24, 25, 27, 29, 32],
]
TABLE_7_7_GRID[2][5] = 460.0


# Table 7.5: Recommended side friction factors (f). None = no value (dash).
# Keys: speed (km/h). Sealed: Car/Truck × Des max/Abs max. Unsealed: Cars and trucks Des max only.
TABLE_7_5_SPEEDS = [25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130]

# f (sealed roads) — Cars
TABLE_7_5_SEALED_CARS_DES = {40: 0.30, 50: 0.30, 60: 0.24, 70: 0.19, 80: 0.16, 90: 0.13, 100: 0.12, 110: 0.12, 120: 0.11, 130: 0.11}
TABLE_7_5_SEALED_CARS_ABS = {40: 0.35, 50: 0.35, 60: 0.33, 70: 0.31, 80: 0.26, 90: 0.20, 100: 0.16, 110: 0.12, 120: 0.11, 130: 0.11}
# f (sealed roads) — Trucks
TABLE_7_5_SEALED_TRUCKS_DES = {40: 0.21, 50: 0.21, 60: 0.17, 70: 0.14, 80: 0.13, 90: 0.12, 100: 0.12, 110: 0.12, 120: 0.11, 130: 0.11}
TABLE_7_5_SEALED_TRUCKS_ABS = {40: None, 50: 0.25, 60: 0.24, 70: 0.23, 80: 0.20, 90: 0.15, 100: 0.12, 110: 0.12, 120: 0.11, 130: None}
# f (unsealed roads) — Cars and trucks Des max
TABLE_7_5_UNSEALED_DES = {25: 0.18, 30: 0.16, 40: 0.14, 50: 0.12, 60: 0.11, 70: 0.10, 80: 0.10, 90: 0.09, 100: 0.09, 110: 0.08, 120: None, 130: None}


def _match_speed_for_f(speeds: list[int], V_kmh: float) -> int:
    """Return nearest speed in TABLE_7_5_SPEEDS for lookup."""
    V_int = int(round(V_kmh))
    if V_int in speeds:
        return V_int
    lower = [s for s in speeds if s <= V_int]
    if lower:
        return lower[-1]
    return speeds[0] if speeds else 40


def lookup_f_table_7_5(
    V_kmh: float,
    surface: str,
    vehicle_type: str,
    friction_type: str,
) -> Optional[float]:
    """
    Table 7.5 Recommended side friction factors.
    Returns f value or None if cell is empty. Uses nearest speed row for V_kmh.
    """
    speed = _match_speed_for_f(TABLE_7_5_SPEEDS, V_kmh)
    surface_clean = (surface or "").strip()

    if surface_clean == "Sealed roads":
        if vehicle_type == "Car":
            return TABLE_7_5_SEALED_CARS_ABS.get(speed) if friction_type == "Ads max" else TABLE_7_5_SEALED_CARS_DES.get(speed)
        if vehicle_type == "Truck":
            return TABLE_7_5_SEALED_TRUCKS_ABS.get(speed) if friction_type == "Ads max" else TABLE_7_5_SEALED_TRUCKS_DES.get(speed)
        return None  # unknown vehicle
    else:
        # Unsealed: Cars and trucks, Des max only
        return TABLE_7_5_UNSEALED_DES.get(speed)


def get_f_options_for_table_7_5(
    V_kmh: float,
    surface: str,
    vehicle_type: str,
    friction_type: str,
) -> list[float]:
    """
    Return list of f values for dropdown: normally one value from Table 7.5.
    If table has no value, returns [0.12] as fallback.
    """
    f_val = lookup_f_table_7_5(V_kmh, surface, vehicle_type, friction_type)
    if f_val is not None:
        return [f_val]
    # Fallback: use 0.12 or nearest available speed
    for s in reversed(TABLE_7_5_SPEEDS):
        if s <= V_kmh + 20:
            f_val = lookup_f_table_7_5(s, surface, vehicle_type, friction_type)
            if f_val is not None:
                return [f_val]
    return [0.12]


def _match_row(speeds: list[int], V_kmh: float) -> int:
    V_int = int(round(V_kmh))
    if V_int in speeds:
        return speeds.index(V_int)
    lower = [i for i, s in enumerate(speeds) if s <= V_int]
    if lower:
        return lower[-1]
    return 0


def _match_col(e_rates: list[float], e_decimal: float) -> int:
    e = round(e_decimal, 2)
    for i, rate in enumerate(e_rates):
        if abs(rate - e) < 1e-6:
            return i
    best = 0
    for i, rate in enumerate(e_rates):
        if abs(rate - e) < abs(e_rates[best] - e):
            best = i
    return best


def calc_rmin(V_kmh: float, e_percent: float, f: float) -> float:
    """R_min = V² / (127 * (e + f)); e as decimal (e_percent / 100)."""
    e = e_percent / 100.0
    denom = 127.0 * (e + f)
    if denom <= 0:
        raise ValueError("Invalid inputs: (e + f) must be > 0")
    return (V_kmh ** 2) / denom


def calc_rmin_ongrade(r_min: float, grading_percent: float) -> float:
    """
    Minimum radius on grade (Equation 7.5, On steep downgrades).
    Rmin_ongrade = Rmin [1 + (G-3)/10]; G = grade (%).
    Ref: Table 7.7 section "On steep downgrades" — increase Rmin by 10% per 1% grade over 3%.
    """
    return r_min * (1.0 + (grading_percent - 3.0) / 10.0)


def lookup_rmin_table(
    V_kmh: float,
    e_percent: float,
    surface: str,
) -> tuple[Optional[float], str]:
    """
    IF(surface == "Sealed roads") → Table 7.6 lookup, else Table 7.7 lookup.
    Returns (Rmin_from_table, "Table 7.6" | "Table 7.7").
    """
    e_decimal = e_percent / 100.0
    surface_clean = (surface or "").strip()

    if surface_clean == "Sealed roads":
        row = _match_row(TABLE_7_6_SPEEDS, V_kmh)
        col = _match_col(TABLE_7_6_E_RATES, e_decimal)
        val = TABLE_7_6_GRID[row][col]
        return (float(val), "Table 7.6")
    else:
        row = _match_row(TABLE_7_7_SPEEDS, V_kmh)
        col = _match_col(TABLE_7_7_E_RATES, e_decimal)
        val = TABLE_7_7_GRID[row][col]
        return (float(val), "Table 7.7")
