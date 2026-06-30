"""AADT and PCU calculations from traffic investigation daily totals."""
from __future__ import annotations

import re
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
    4.0,  # More than 24 Seats (buses)
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
    base_total_aadt: int
    base_total_pcu: int
    projected_total_aadt: int
    projected_total_pcu: int
    design_year_label: str = ""
    design_years: int = 0
    growth_rate: float = 0.0
    input_source: str = "read_data"

    @property
    def total_aadt(self) -> int:
        """Projected AADT used by road classification and quick results."""
        return self.projected_total_aadt

    @property
    def total_pcu(self) -> int:
        """Projected PCU used by road classification and quick results."""
        return self.projected_total_pcu

    @property
    def has_data(self) -> bool:
        return self.base_total_aadt > 0 or self.base_total_pcu > 0

    @property
    def chart_bars(self) -> list[tuple[str, float, str]]:
        year = self.design_year_label or "design year"
        return [
            (f"AADT ({year})", float(self.projected_total_aadt), AADT_BAR_COLOR),
            (f"PCU ({year})", float(self.projected_total_pcu), PCU_BAR_COLOR),
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
            "Total (base)",
            f"{self.base_total_aadt:,}",
            "",
            f"{self.base_total_pcu:,}",
        ])
        rows.append([
            f"Total (projected {self.design_year_label or 'design year'})",
            f"{self.projected_total_aadt:,}",
            "",
            f"{self.projected_total_pcu:,}",
        ])
        return rows


def parse_design_years(label: str) -> int:
    """Parse combo text such as '15 year' into 15."""
    text = (label or "").strip().lower()
    match = re.match(r"^(\d+)", text)
    if not match:
        return 0
    return max(0, int(match.group(1)))


def column_pcu(count: int, factor: float) -> int:
    """Match Excel: round each vehicle-type PCU, then sum."""
    return int(round(count * factor))


def project_traffic_value(base_value: float, design_years: int, growth_rate: float) -> int:
    """Project AADT or PCU to the selected geometry design year."""
    if base_value <= 0:
        return 0
    if design_years <= 0:
        return int(round(base_value))
    return int(round(base_value * ((1 + growth_rate) ** design_years)))


def project_count(base_count: int, design_years: int, growth_rate: float) -> int:
    """Project one vehicle count to the selected geometry design year."""
    return project_traffic_value(float(base_count), design_years, growth_rate)


def project_vehicle_totals(
    vehicle_totals: list[int],
    design_years: int,
    growth_rate: float,
) -> list[int]:
    return [
        project_count(count, design_years, growth_rate)
        for count in vehicle_totals
    ]


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


def _result_from_vehicle_totals(
    vehicle_totals: list[int],
) -> tuple[tuple[VehicleCategoryResult, ...], int, int]:
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

    return tuple(categories), total_aadt, total_pcu


def build_aadt_pcu_description(result: AadtPcuResult) -> str:
    if not result.has_data:
        if result.input_source == "direct_input":
            return (
                "- Base AADT from direct input is ____\n\n"
                "- Base PCU from direct input is ____\n\n"
                "- Projected AADT in design year is ____\n\n"
                "- Projected PCU in design year is ____"
            )
        return (
            "- Base AADT from traffic count is ____\n\n"
            "- Base PCU from traffic count is ____\n\n"
            "- Projected AADT in design year is ____\n\n"
            "- Projected PCU in design year is ____"
        )

    year = result.design_year_label or "design year"
    growth_pct = result.growth_rate * 100
    if result.input_source == "direct_input":
        base_aadt_label = "Base AADT from direct input"
        base_pcu_label = "Base PCU from direct input"
    else:
        base_aadt_label = "Base AADT from traffic count"
        base_pcu_label = "Base PCU from traffic count"

    return (
        f"- {base_aadt_label} is {result.base_total_aadt:,}\n\n"
        f"- {base_pcu_label} is {result.base_total_pcu:,}\n\n"
        f"- Design year for Geometry is {year}\n\n"
        f"- Projected AADT in {year} is {result.projected_total_aadt:,} "
        f"(growth rate {growth_pct:g}%)\n\n"
        f"- Projected PCU in {year} is {result.projected_total_pcu:,}"
    )


def _empty_result(
    *,
    design_year_label: str = "",
    design_years: int = 0,
    growth_rate: float = 0.0,
) -> AadtPcuResult:
    return AadtPcuResult(
        (),
        0,
        0,
        0,
        0,
        design_year_label=design_year_label,
        design_years=design_years,
        growth_rate=growth_rate,
    )


def compute_aadt_pcu(
    daily_totals: dict[str, list[int]] | None = None,
    *,
    count_hour: str = "12h",
    summary_total_row: list | None = None,
    design_years: int = 0,
    growth_rate: float = 0.0,
    design_year_label: str = "",
) -> AadtPcuResult:
    """
    Base AADT/PCU = sum of D1 + D2 columns (after count-hour power).
    Projected values grow each vehicle count by (1 + R) ** design_years, then PCU is recalculated.
    """
    if summary_total_row:
        vehicle_totals = vehicle_totals_from_summary_row(summary_total_row)
    elif daily_totals:
        vehicle_totals = sum_vehicle_totals(daily_totals, count_hour=count_hour)
    else:
        return _empty_result(
            design_year_label=design_year_label,
            design_years=design_years,
            growth_rate=growth_rate,
        )

    if not vehicle_totals or not any(vehicle_totals):
        return _empty_result(
            design_year_label=design_year_label,
            design_years=design_years,
            growth_rate=growth_rate,
        )

    base_categories, base_aadt, base_pcu = _result_from_vehicle_totals(vehicle_totals)
    projected_totals = project_vehicle_totals(vehicle_totals, design_years, growth_rate)
    _projected_categories, projected_aadt, projected_pcu = _result_from_vehicle_totals(projected_totals)

    return AadtPcuResult(
        base_categories,
        base_aadt,
        base_pcu,
        projected_aadt,
        projected_pcu,
        design_year_label=design_year_label,
        design_years=design_years,
        growth_rate=growth_rate,
        input_source="read_data",
    )


def compute_aadt_pcu_from_direct_input(
    base_aadt: int,
    base_pcu: float,
    *,
    design_years: int = 0,
    growth_rate: float = 0.0,
    design_year_label: str = "",
) -> AadtPcuResult:
    """Use manually entered AADT and PCU from the Direct Input section."""
    base_pcu_int = int(round(base_pcu))
    projected_aadt = project_traffic_value(float(base_aadt), design_years, growth_rate)
    projected_pcu = project_traffic_value(base_pcu, design_years, growth_rate)

    return AadtPcuResult(
        (),
        max(0, base_aadt),
        max(0, base_pcu_int),
        projected_aadt,
        projected_pcu,
        design_year_label=design_year_label,
        design_years=design_years,
        growth_rate=growth_rate,
        input_source="direct_input",
    )


def compute_aadt_pcu_from_workbook_data(
    data: dict,
    *,
    design_years: int = 0,
    growth_rate: float = 0.0,
    design_year_label: str = "",
) -> AadtPcuResult:
    """Convenience wrapper for session data stored in main_window."""
    daily_totals = data.get("daily_totals")
    count_hour = data.get("traffic_count_hour", "12h")
    summary_total_row = data.get("summary_total_row")

    if daily_totals:
        return compute_aadt_pcu(
            daily_totals,
            count_hour=count_hour,
            design_years=design_years,
            growth_rate=growth_rate,
            design_year_label=design_year_label,
        )
    if summary_total_row:
        return compute_aadt_pcu(
            summary_total_row=summary_total_row,
            design_years=design_years,
            growth_rate=growth_rate,
            design_year_label=design_year_label,
        )
    return _empty_result(
        design_year_label=design_year_label,
        design_years=design_years,
        growth_rate=growth_rate,
    )
