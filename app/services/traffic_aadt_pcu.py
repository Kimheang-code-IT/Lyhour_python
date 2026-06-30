"""AADT and PCU calculations from traffic investigation daily totals."""
from __future__ import annotations

from dataclasses import dataclass

from app.services.traffic_excel import VEHICLE_TYPE_COUNT, traffic_count_hour_multiplier

# PCU factors per Excel vehicle column (C … T), matching Traffic Demand Forecast (PCU).
COLUMN_PCU_FACTORS: list[float] = [
    0.4,  # Motor
    1.2,  # Tricycles
    1.2,  # Koyon
    1.0,  # Passenger Car
    1.0,  # Pick-up
    2.0,  # Max 15 Sets
    2.0,  # More than 15 Sets
    4.0,  # More than 24 Sets (buses)
    2.5,  # 2 axles 4 tires
    2.5,  # 2 axles 6 tires
    4.5,  # 3 axles
    4.5,  # 4 axles No-trailer
    4.5,  # 4 axles Full-trailer
    4.5,  # 4 axles Semi-trailer
    4.5,  # 5 axles No-trailer
    4.5,  # 5 axles Full-trailer
    4.5,  # 5 axles Semi-trailer
    4.5,  # 6 axles Semi-trailer
]

_HEAVY_COLUMN_START = 10
_HEAVY_PCU_FACTOR = 4.5

# AADT display groups (PCU is summed per underlying column, not one factor per group).
VEHICLE_CATEGORIES: list[tuple[str, list[int]]] = [
    ("Passenger cars", [3, 4]),
    ("Motorcycles", [0]),
    ("Motor-Trailer", [2]),
    ("Motor tricycles (autorickshaw)", [1]),
    ("Light vans", [5, 6]),
    ("Buses", [7]),
    ("Single unit trucks", [8, 9]),
    ("Heavy vehicles", list(range(10, VEHICLE_TYPE_COUNT))),
]

AADT_BAR_COLOR = "#156082"
PCU_BAR_COLOR = "#e97132"


@dataclass(frozen=True)
class VehicleCategoryResult:
    name: str
    aadt: int
    pcu_factor: float
    pcu: int


@dataclass(frozen=True)
class AadtPcuResult:
    categories: tuple[VehicleCategoryResult, ...]
    total_aadt: int
    total_pcu: int

    @property
    def chart_bars(self) -> list[tuple[str, float, str]]:
        return [
            ("AADT", float(self.total_aadt), AADT_BAR_COLOR),
            ("PCU", float(self.total_pcu), PCU_BAR_COLOR),
        ]

    @property
    def table_rows(self) -> list[list[str]]:
        rows: list[list[str]] = []
        for item in self.categories:
            rows.append([
                item.name,
                f"{item.aadt:,}",
                f"{item.pcu_factor:g}" if item.aadt else "—",
                f"{item.pcu:,}",
            ])
        rows.append([
            "Total",
            f"{self.total_aadt:,}",
            "",
            f"{self.total_pcu:,}",
        ])
        return rows


_EMPTY = AadtPcuResult((), 0, 0)


def column_pcu(count: int, factor: float) -> int:
    """Match Excel: round each vehicle-type PCU, then sum."""
    return int(round(count * factor))


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
    """Extract per-type totals from a summary row produced by traffic_excel."""
    if not summary_total_row or len(summary_total_row) < 1 + VEHICLE_TYPE_COUNT:
        return []
    return [int(summary_total_row[index]) for index in range(1, 1 + VEHICLE_TYPE_COUNT)]


def compute_aadt_pcu(
    daily_totals: dict[str, list[int]] | None = None,
    *,
    count_hour: str = "12h",
    summary_total_row: list | None = None,
) -> AadtPcuResult:
    """
    AADT = sum of D1 + D2 columns (after count-hour power).
    PCU = per-column factors for cols C–K, then heavy axles (L–T) as one group × 4.5.
    """
    if summary_total_row:
        vehicle_totals = vehicle_totals_from_summary_row(summary_total_row)
    elif daily_totals:
        vehicle_totals = sum_vehicle_totals(daily_totals, count_hour=count_hour)
    else:
        return _EMPTY

    if not vehicle_totals or not any(vehicle_totals):
        return _EMPTY

    light_pcus = [
        column_pcu(count, factor)
        for count, factor in zip(
            vehicle_totals[:_HEAVY_COLUMN_START],
            COLUMN_PCU_FACTORS[:_HEAVY_COLUMN_START],
        )
    ]
    heavy_aadt = sum(vehicle_totals[_HEAVY_COLUMN_START:])
    heavy_pcu = column_pcu(heavy_aadt, _HEAVY_PCU_FACTOR)
    total_pcu = sum(light_pcus) + heavy_pcu
    total_aadt = sum(vehicle_totals)

    categories: list[VehicleCategoryResult] = []
    for name, column_indices in VEHICLE_CATEGORIES:
        aadt = sum(vehicle_totals[index] for index in column_indices if index < len(vehicle_totals))
        if name == "Heavy vehicles":
            pcu = heavy_pcu
        else:
            pcu = sum(
                light_pcus[index]
                for index in column_indices
                if index < _HEAVY_COLUMN_START
            )
        factor = round(pcu / aadt, 2) if aadt else 0.0
        categories.append(VehicleCategoryResult(name, aadt, factor, pcu))

    return AadtPcuResult(tuple(categories), total_aadt, total_pcu)


def compute_aadt_pcu_from_workbook_data(data: dict) -> AadtPcuResult:
    """Convenience wrapper for session data stored in main_window."""
    daily_totals = data.get("daily_totals")
    count_hour = data.get("traffic_count_hour", "12h")
    summary_total_row = data.get("summary_total_row")

    if daily_totals:
        return compute_aadt_pcu(daily_totals, count_hour=count_hour)
    if summary_total_row:
        return compute_aadt_pcu(summary_total_row=summary_total_row)
    return _EMPTY
