"""ESAL calculations from temporary D1/D2 traffic session data."""
from __future__ import annotations

from dataclasses import dataclass

from app.services.traffic_excel import VEHICLE_TYPE_COUNT, traffic_count_hour_multiplier

# ESAL factor per vehicle per day (equivalent axle loads), by Excel column C–T.
COLUMN_ESAL_FACTORS: list[float] = [
    0.0001,  # Motor
    0.0001,  # Tricycles
    0.0002,  # Koyon
    0.0002,  # Passenger Car
    0.0002,  # Pick-up
    0.0004,  # Max 15 Seats
    0.0008,  # More than 15 Seats
    0.0100,  # More than 24 Seats
    0.0200,  # 2 axles 4 tires
    0.1000,  # 2 axles 6 tires
    0.3000,  # 3 axles
    0.5000,  # 4 axles No-trailer
    0.6000,  # 4 axles Full-trailer
    0.7000,  # 4 axles Semi-trailer
    0.9000,  # 5 axles No-trailer
    1.0000,  # 5 axles Full-trailer
    1.1000,  # 5 axles Semi-trailer
    1.2000,  # 6 axles Semi-trailer
]

DESIGN_PERIODS = (15, 20, 25)

# Axle summary table groups -> column indices in vehicle totals.
AXLE_TABLE_GROUPS: tuple[tuple[str, list[int]], ...] = (
    ("steering_sast", [0, 1, 2, 3, 4]),
    ("sadt", [5, 6]),
    ("tast", [8]),
    ("tadt", [9, 10]),
    ("trdt", list(range(11, VEHICLE_TYPE_COUNT))),
)

CHART_COLORS = ("#156082", "#e97132", "#196b24")


@dataclass(frozen=True)
class EsalDesignPeriodResult:
    years: int
    total_esal: int
    traffic_class: str


@dataclass(frozen=True)
class EsalResult:
    axle_numbers: dict[str, int]
    design_periods: tuple[EsalDesignPeriodResult, ...]

    @property
    def has_data(self) -> bool:
        return any(period.total_esal > 0 for period in self.design_periods)


def get_traffic_class(esal_million: float) -> str:
    if esal_million < 0.3:
        return "T1"
    if esal_million < 0.7:
        return "T2"
    if esal_million < 1.5:
        return "T3"
    if esal_million < 3.0:
        return "T4"
    if esal_million < 6.0:
        return "T5"
    if esal_million < 10:
        return "T6"
    if esal_million < 17:
        return "T7"
    if esal_million <= 30:
        return "T8"
    return "More than T8"


def sum_vehicle_totals(
    daily_totals: dict[str, list[int]],
    *,
    count_hour: str = "12h",
) -> list[int]:
    """Sum D1 + D2 daily totals and apply Traffic Count Hour power."""
    power = traffic_count_hour_multiplier(count_hour)
    summed = [0] * VEHICLE_TYPE_COUNT
    for sheet_name in ("D1", "D2"):
        values = daily_totals.get(sheet_name) or []
        for index in range(VEHICLE_TYPE_COUNT):
            if index < len(values):
                summed[index] += int(values[index])
    return [int(round(value * power)) for value in summed]


def vehicle_totals_from_summary_row(summary_total_row: list) -> list[int]:
    if not summary_total_row or len(summary_total_row) < 1 + VEHICLE_TYPE_COUNT:
        return []
    return [int(summary_total_row[index]) for index in range(1, 1 + VEHICLE_TYPE_COUNT)]


def daily_esal_rate(vehicle_totals: list[int]) -> float:
    """Daily ESAL contribution from all vehicle types."""
    total = 0.0
    for count, factor in zip(vehicle_totals, COLUMN_ESAL_FACTORS):
        total += int(count) * factor
    return total


def cumulative_growth_multiplier(design_years: int, growth_rate: float) -> float:
    """Sum of (1 + growth_rate) ** t for t = 0 .. design_years-1."""
    if design_years <= 0:
        return 0.0
    if growth_rate == 0:
        return float(design_years)
    return (((1 + growth_rate) ** design_years) - 1) / growth_rate


def total_esal_for_design_period(
    vehicle_totals: list[int],
    design_years: int,
    *,
    growth_rate: float,
) -> int:
    """Total ESAL over a design period with compound traffic growth."""
    rate = daily_esal_rate(vehicle_totals)
    multiplier = cumulative_growth_multiplier(design_years, growth_rate)
    return int(round(rate * 365 * multiplier))


def axle_group_esal(vehicle_totals: list[int], column_indices: list[int]) -> int:
    """Annual ESAL contribution for one axle group (used in summary table)."""
    annual = 0.0
    for index in column_indices:
        if index < len(vehicle_totals):
            annual += vehicle_totals[index] * COLUMN_ESAL_FACTORS[index] * 365
    return int(round(annual))


def build_axle_numbers(vehicle_totals: list[int]) -> dict[str, int]:
    numbers: dict[str, int] = {}
    for key, indices in AXLE_TABLE_GROUPS:
        numbers[key] = axle_group_esal(vehicle_totals, indices)
    return numbers


def build_design_period_description(periods: tuple[EsalDesignPeriodResult, ...]) -> str:
    lines = [
        f"- Design period in {period.years} year is {period.traffic_class}"
        for period in periods
    ]
    return "\n\n".join(lines)


def compute_esal(
    daily_totals: dict[str, list[int]] | None = None,
    *,
    count_hour: str = "12h",
    summary_total_row: list | None = None,
    growth_rate: float = 0.05,
    design_periods: tuple[int, ...] = DESIGN_PERIODS,
) -> EsalResult:
    if summary_total_row:
        vehicle_totals = vehicle_totals_from_summary_row(summary_total_row)
    elif daily_totals:
        vehicle_totals = sum_vehicle_totals(daily_totals, count_hour=count_hour)
    else:
        vehicle_totals = []

    if not vehicle_totals or not any(vehicle_totals):
        empty_periods = tuple(
            EsalDesignPeriodResult(years=years, total_esal=0, traffic_class="—")
            for years in design_periods
        )
        return EsalResult(
            axle_numbers={key: 0 for key, _ in AXLE_TABLE_GROUPS},
            design_periods=empty_periods,
        )

    axle_numbers = build_axle_numbers(vehicle_totals)
    period_results: list[EsalDesignPeriodResult] = []
    for years in design_periods:
        total_esal = total_esal_for_design_period(
            vehicle_totals,
            years,
            growth_rate=growth_rate,
        )
        esal_million = total_esal / 1_000_000
        period_results.append(
            EsalDesignPeriodResult(
                years=years,
                total_esal=total_esal,
                traffic_class=get_traffic_class(esal_million),
            )
        )

    return EsalResult(
        axle_numbers=axle_numbers,
        design_periods=tuple(period_results),
    )


def compute_esal_from_workbook_data(
    workbook_data: dict,
    *,
    growth_rate: float = 0.05,
) -> EsalResult:
    return compute_esal(
        workbook_data.get("daily_totals"),
        count_hour=workbook_data.get("traffic_count_hour", "12h"),
        summary_total_row=workbook_data.get("summary_total_row"),
        growth_rate=growth_rate,
    )


def chart_bars_from_esal(result: EsalResult) -> list[tuple[str, float, str]]:
    bars: list[tuple[str, float, str]] = []
    for index, period in enumerate(result.design_periods):
        color = CHART_COLORS[index % len(CHART_COLORS)]
        bars.append((f"{period.years} year", float(period.total_esal), color))
    return bars
