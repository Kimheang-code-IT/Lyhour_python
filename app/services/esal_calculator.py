"""Pure ESAL calculation helpers (standard load, TLD, LDF, CGF, classification)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

AxleType = Literal["SAST", "TAST", "SADT", "TADT", "TRDT"]

AXLE_KEY_TO_TYPE: dict[str, AxleType] = {
    "steering_sast": "SAST",
    "tast": "TAST",
    "sadt": "SADT",
    "tadt": "TADT",
    "trdt": "TRDT",
}

AXLE_TYPE_ORDER: tuple[AxleType, ...] = ("SAST", "TAST", "SADT", "TADT", "TRDT")

AXLE_TYPE_TO_KEY: dict[AxleType, str] = {axle_type: key for key, axle_type in AXLE_KEY_TO_TYPE.items()}

STANDARD_LOADS_KN: dict[AxleType, float] = {
    "SAST": 53.0,
    "TAST": 89.0,
    "SADT": 80.0,
    "TADT": 135.0,
    "TRDT": 181.0,
}

DESIGN_PERIODS_YEARS: tuple[int, ...] = (15, 20, 25)


def esal_chart_years(pavement_design_years: int) -> tuple[int, ...]:
    """Chart milestones: 1, 5, 10, … through pavement design year (default 25)."""
    from app.services.traffic_aadt_pcu import projection_chart_years

    target_years = pavement_design_years if pavement_design_years > 0 else max(DESIGN_PERIODS_YEARS)
    return projection_chart_years(target_years)


def esal_table_years(pavement_design_years: int) -> tuple[int, ...]:
    """Table rows: year 1, 2, 3, … through pavement design year (default 25)."""
    from app.services.traffic_aadt_pcu import projection_table_years

    target_years = pavement_design_years if pavement_design_years > 0 else max(DESIGN_PERIODS_YEARS)
    return projection_table_years(target_years)


def get_ldf_by_lane(lane_each_direction: int) -> float:
    """Lane distribution factor for the design lane (lanes in each direction)."""
    lanes = int(lane_each_direction or 1)
    if lanes <= 0:
        return 1.0
    if lanes == 1:
        return 1.0
    if lanes == 2:
        return 0.9
    if lanes >= 3:
        return 0.7
    return 1.0


TLD_UPLOAD_MESSAGE = "Please upload Austroads TLD Excel to calculate ESAL using axle load distribution."


def safe_number(value: object) -> float:
    """Convert a value to a finite number, otherwise 0."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def normalize_tld_loads(
    loads: dict[str, float] | None,
) -> dict[str, float]:
    """Accept TLD loads keyed by axle type (SAST) or internal axle keys."""
    normalized = {key: 0.0 for key in AXLE_KEY_TO_TYPE}
    if not loads:
        return normalized
    for raw_key, raw_value in loads.items():
        load = safe_number(raw_value)
        if load <= 0:
            continue
        key = str(raw_key).strip()
        if key in normalized:
            normalized[key] = load
            continue
        upper = key.upper()
        if upper in AXLE_TYPE_TO_KEY:
            normalized[AXLE_TYPE_TO_KEY[upper]] = load
    return normalized


def has_tld_distribution(rows: list[dict[str, float]] | None) -> bool:
    if not rows:
        return False
    for row in rows:
        if safe_number(row.get("load_kn")) <= 0:
            continue
        for axle_type in AXLE_TYPE_ORDER:
            if safe_number(row.get(axle_type)) > 0:
                return True
    return False


def calculate_distribution_row_factor(load_kn: float, standard_load: float, percent: float) -> float:
    """Contribution from one TLD row: (percent / 100) * (load / standard)^4."""
    if percent <= 0 or load_kn <= 0 or standard_load <= 0:
        return 0.0
    ratio = load_kn / standard_load
    value = (percent / 100.0) * (ratio**4)
    return value if math.isfinite(value) else 0.0


def calculate_weighted_esal_factor(axle_type: AxleType, distribution_rows: list[dict[str, float]]) -> float:
    """Weighted ESAL factor from Austroads TLD distribution rows."""
    standard = STANDARD_LOADS_KN[axle_type]
    total = 0.0
    for row in distribution_rows:
        percent = safe_number(row.get(axle_type))
        load_kn = safe_number(row.get("load_kn"))
        total += calculate_distribution_row_factor(load_kn, standard, percent)
    return total if math.isfinite(total) else 0.0


def has_tld_load_values(loads: dict[str, float] | None) -> bool:
    return any(safe_number(value) > 0 for value in (loads or {}).values())


@dataclass(frozen=True)
class AxleEsalRow:
    axle_type: AxleType
    axle_key: str
    standard_load_kn: float
    actual_load_kn: float | None
    count: int
    esal_factor: float | None
    ldf: float
    esal_per_day: float


def calculate_cgf(rate_percent: float, period_year: int) -> float:
    """
    Cumulative Growth Factor.

    CGF = ((1 + 0.01 * R)^P - 1) / (0.01 * R), or P when R = 0.
    """
    years = max(0, int(period_year))
    if years <= 0:
        return 0.0
    rate = max(0.0, float(rate_percent or 0))
    if rate == 0:
        return float(years)
    rate_decimal = rate * 0.01
    numerator = (1 + rate_decimal) ** years - 1
    if rate_decimal == 0:
        return float(years)
    value = numerator / rate_decimal
    return value if math.isfinite(value) else 0.0


def calculate_esal_factor(axle_type: AxleType, actual_load: float, use_tld: bool) -> float:
    """ESAL factor: 1.0 for standard load, or (actual / standard)^4 for TLD."""
    standard = STANDARD_LOADS_KN[axle_type]
    if not use_tld:
        return 1.0
    if actual_load <= 0 or standard <= 0:
        return 0.0
    ratio = actual_load / standard
    value = ratio**4
    return value if math.isfinite(value) else 0.0


def calculate_axle_esal_per_day(count: int, factor: float, ldf: float) -> float:
    """ESAL per day for one axle type."""
    value = safe_number(count) * safe_number(factor) * safe_number(ldf)
    return value if math.isfinite(value) else 0.0


def calculate_total_esal_per_day(rows: list[AxleEsalRow]) -> float:
    total = sum(row.esal_per_day for row in rows)
    return total if math.isfinite(total) else 0.0


def calculate_design_period_esal(
    esal_per_day: float,
    rate_percent: float,
    period_year: int,
) -> int:
    """Total ESAL over a design period."""
    cgf = calculate_cgf(rate_percent, period_year)
    value = float(esal_per_day or 0) * 365.0 * cgf
    if not math.isfinite(value):
        return 0
    return int(round(max(0.0, value)))


def classify_traffic(esal: float) -> str:
    """Classify total ESAL (not millions) into T1..T8 / T8+."""
    million = max(0.0, float(esal or 0)) / 1_000_000
    if million < 0.3:
        return "T1"
    if million < 0.7:
        return "T2"
    if million < 1.5:
        return "T3"
    if million < 3.0:
        return "T4"
    if million < 6.0:
        return "T5"
    if million < 10.0:
        return "T6"
    if million < 17.0:
        return "T7"
    if million <= 30.0:
        return "T8"
    return "T8+"


def build_axle_esal_rows(
    axle_counts: dict[str, int],
    *,
    tld_distribution: list[dict[str, float]] | None = None,
    use_tld: bool = False,
    tld_loads_ready: bool = False,
    lane_each_direction: int = 1,
) -> tuple[AxleEsalRow, ...]:
    """Build per-axle ESAL/day rows from daily axle counts."""
    distribution = list(tld_distribution or [])
    ldf = get_ldf_by_lane(lane_each_direction)
    rows: list[AxleEsalRow] = []

    for axle_key, axle_type in AXLE_KEY_TO_TYPE.items():
        count = max(0, int(axle_counts.get(axle_key, 0) or 0))
        standard = STANDARD_LOADS_KN[axle_type]
        actual_load: float | None
        factor: float | None
        esal_day: float

        if not use_tld:
            actual_load = standard
            factor = 1.0
            esal_day = calculate_axle_esal_per_day(count, factor, ldf)
        elif not tld_loads_ready or not has_tld_distribution(distribution):
            actual_load = None
            factor = None
            esal_day = 0.0
        else:
            actual_load = None
            factor = calculate_weighted_esal_factor(axle_type, distribution)
            esal_day = calculate_axle_esal_per_day(count, factor or 0.0, ldf)

        rows.append(
            AxleEsalRow(
                axle_type=axle_type,
                axle_key=axle_key,
                standard_load_kn=standard,
                actual_load_kn=actual_load,
                count=count,
                esal_factor=factor,
                ldf=ldf,
                esal_per_day=esal_day,
            )
        )
    return tuple(rows)


def build_design_period_results(
    esal_per_day: float,
    *,
    rate_percent: float,
    periods: tuple[int, ...] = DESIGN_PERIODS_YEARS,
) -> list[tuple[int, int, str]]:
    """Return (years, total_esal, traffic_class) for each design period."""
    results: list[tuple[int, int, str]] = []
    for years in periods:
        total = calculate_design_period_esal(esal_per_day, rate_percent, years)
        results.append((years, total, classify_traffic(total)))
    return results
