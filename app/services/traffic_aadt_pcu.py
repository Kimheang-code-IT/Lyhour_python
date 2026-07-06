"""AADT and PCU calculations from traffic investigation daily totals."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.traffic_excel import VEHICLE_TYPE_COUNT, average_vehicle_totals
from app.data.area_type import (
    DEFAULT_AREA_TYPE,
    normalize_area_type,
    pcu_factors_for_area_type,
)

# Default PCU factors (Rural Standard) — kept for backward compatibility.
COLUMN_PCU_FACTORS: list[float] = pcu_factors_for_area_type(DEFAULT_AREA_TYPE)

_HEAVY_COLUMN_START = 10

# AADT display groups; PCU sums per-column values inside each group.
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

CHART_YEAR_STEP = 5


@dataclass(frozen=True)
class AadtPcuProjectionRow:
    years: int
    aadt: int
    pcu: int


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
    area_type: str = DEFAULT_AREA_TYPE
    input_source: str = "read_data"
    vehicle_totals: tuple[int, ...] = ()

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
    def chart_groups(self) -> list[tuple[str, list[tuple[float, str]]]]:
        """Grouped AADT/PCU bars at year 1, 5, 10, 15, … up to geometry design year."""
        groups: list[tuple[str, list[tuple[float, str]]]] = []
        for years in projection_chart_years(self.design_years):
            aadt, pcu = self.projected_totals_at_year(years)
            groups.append((
                f"Year {years}",
                [
                    (float(aadt), AADT_BAR_COLOR),
                    (float(pcu), PCU_BAR_COLOR),
                ],
            ))
        return groups

    @property
    def projection_table_rows(self) -> list[list[str]]:
        """Table rows (Year, AADT, PCU) for each year from 1 through geometry design year."""
        rows: list[list[str]] = []
        for years in projection_table_years(self.design_years):
            aadt, pcu = self.projected_totals_at_year(years)
            rows.append([f"Year {years}", f"{aadt:,}", f"{pcu:,}"])
        return rows

    @property
    def projection_table_highlight_row(self) -> int | None:
        if self.design_years <= 0:
            return None
        return self.design_years - 1

    def projected_totals_at_year(self, years: int) -> tuple[int, int]:
        """Project base traffic to a future year count."""
        if not self.has_data and years <= 0:
            return 0, 0
        factors = pcu_factors_for_area_type(self.area_type)
        if self.input_source == "direct_input":
            return (
                project_traffic_value(float(self.base_total_aadt), years, self.growth_rate),
                project_traffic_value(float(self.base_total_pcu), years, self.growth_rate),
            )
        if self.vehicle_totals:
            projected_totals = project_vehicle_totals(list(self.vehicle_totals), years, self.growth_rate)
            _categories, aadt, pcu = _result_from_vehicle_totals(projected_totals, pcu_factors=factors)
            return aadt, pcu
        return (
            project_traffic_value(float(self.base_total_aadt), years, self.growth_rate),
            project_traffic_value(float(self.base_total_pcu), years, self.growth_rate),
        )

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


def projection_chart_years(design_years: int) -> tuple[int, ...]:
    """Chart x-axis years: 1, 5, 10, 15, 20, … through geometry design year."""
    if design_years <= 0:
        return ()
    years = [1]
    milestone = CHART_YEAR_STEP
    while milestone < design_years:
        years.append(milestone)
        milestone += CHART_YEAR_STEP
    if years[-1] != design_years:
        years.append(design_years)
    return tuple(years)


def projection_table_years(design_years: int) -> tuple[int, ...]:
    """Table rows: year 1, 2, 3, … through geometry design year."""
    if design_years <= 0:
        return ()
    return tuple(range(1, design_years + 1))


def column_pcu(count: int, factor: float) -> int:
    """Match Excel: round each vehicle-type PCU, then sum."""
    return int(round(count * factor))


def column_pcus_for_totals(
    vehicle_totals: list[int],
    pcu_factors: list[float],
) -> list[int]:
    """PCU for each vehicle column: round(count × factor) one type at a time."""
    column_pcus: list[int] = []
    for index in range(VEHICLE_TYPE_COUNT):
        count = vehicle_totals[index] if index < len(vehicle_totals) else 0
        factor = pcu_factors[index] if index < len(pcu_factors) else pcu_factors[-1]
        column_pcus.append(column_pcu(count, factor))
    return column_pcus


def total_pcu_from_vehicle_totals(
    vehicle_totals: list[int],
    pcu_factors: list[float],
) -> int:
    """Sum PCU from each vehicle type using the selected area-type factors."""
    return sum(column_pcus_for_totals(vehicle_totals, pcu_factors))


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
    daily_totals: dict[str, list[int]] | None = None,
    *,
    daily_totals_12h: dict[str, list[int]] | None = None,
    daily_totals_24h: dict[str, list[int]] | None = None,
    survey_hours: int = 12,
    count_hour: str = "12h",
) -> list[int]:
    """Average D1 and D2 daily totals for the selected count period and apply power."""
    return average_vehicle_totals(
        daily_totals_12h=daily_totals_12h,
        daily_totals_24h=daily_totals_24h,
        daily_totals=daily_totals,
        survey_hours=survey_hours,
        count_hour=count_hour,
    )


def vehicle_totals_from_summary_row(summary_total_row: list) -> list[int]:
    """Extract per-type totals from a summary row produced by traffic_excel."""
    if not summary_total_row or len(summary_total_row) < 1 + VEHICLE_TYPE_COUNT:
        return []
    return [int(summary_total_row[index]) for index in range(1, 1 + VEHICLE_TYPE_COUNT)]


def _result_from_vehicle_totals(
    vehicle_totals: list[int],
    *,
    pcu_factors: list[float] | None = None,
) -> tuple[tuple[VehicleCategoryResult, ...], int, int]:
    factors = pcu_factors or COLUMN_PCU_FACTORS
    column_pcus = column_pcus_for_totals(vehicle_totals, factors)
    total_pcu = sum(column_pcus)
    total_aadt = sum(vehicle_totals[:VEHICLE_TYPE_COUNT])

    categories: list[VehicleCategoryResult] = []
    for name, column_indices in VEHICLE_CATEGORIES:
        aadt = sum(vehicle_totals[index] for index in column_indices if index < len(vehicle_totals))
        pcu = sum(column_pcus[index] for index in column_indices if index < len(column_pcus))
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
        f"- Area Type is {result.area_type}\n\n"
        f"- Design year for Geometry is {year}\n\n"
        f"- Projected AADT in {year} is {result.projected_total_aadt:,} "
        f"(growth rate {growth_pct:g}%)\n\n"
        f"- Projected PCU in {year} is {result.projected_total_pcu:,} "
        f"(vehicle counts grown by {growth_pct:g}%, then PCU factors applied)"
    )


def _empty_result(
    *,
    design_year_label: str = "",
    design_years: int = 0,
    growth_rate: float = 0.0,
    area_type: str = DEFAULT_AREA_TYPE,
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
        area_type=normalize_area_type(area_type),
    )


def compute_aadt_pcu(
    daily_totals: dict[str, list[int]] | None = None,
    *,
    daily_totals_12h: dict[str, list[int]] | None = None,
    daily_totals_24h: dict[str, list[int]] | None = None,
    survey_hours: int = 12,
    count_hour: str = "12h",
    summary_total_row: list | None = None,
    design_years: int = 0,
    growth_rate: float = 0.0,
    design_year_label: str = "",
    area_type: str = DEFAULT_AREA_TYPE,
) -> AadtPcuResult:
    """
    Base AADT/PCU = average of D1 and D2 for the selected count period (after power).
    PCU = sum of round(count × area-type factor) for each vehicle column (C–T).
    Projected values grow each vehicle count by (1 + R) ** design_years, then PCU is recalculated.
    """
    if summary_total_row:
        vehicle_totals = vehicle_totals_from_summary_row(summary_total_row)
    elif daily_totals or daily_totals_12h or daily_totals_24h:
        vehicle_totals = sum_vehicle_totals(
            daily_totals,
            daily_totals_12h=daily_totals_12h,
            daily_totals_24h=daily_totals_24h,
            survey_hours=survey_hours,
            count_hour=count_hour,
        )
    else:
        return _empty_result(
            design_year_label=design_year_label,
            design_years=design_years,
            growth_rate=growth_rate,
            area_type=area_type,
        )

    if not vehicle_totals or not any(vehicle_totals):
        return _empty_result(
            design_year_label=design_year_label,
            design_years=design_years,
            growth_rate=growth_rate,
            area_type=area_type,
        )

    resolved_area_type = normalize_area_type(area_type)
    pcu_factors = pcu_factors_for_area_type(resolved_area_type)
    base_categories, base_aadt, base_pcu = _result_from_vehicle_totals(
        vehicle_totals,
        pcu_factors=pcu_factors,
    )
    projected_totals = project_vehicle_totals(vehicle_totals, design_years, growth_rate)
    _projected_categories, projected_aadt, projected_pcu = _result_from_vehicle_totals(
        projected_totals,
        pcu_factors=pcu_factors,
    )

    return AadtPcuResult(
        base_categories,
        base_aadt,
        base_pcu,
        projected_aadt,
        projected_pcu,
        design_year_label=design_year_label,
        design_years=design_years,
        growth_rate=growth_rate,
        area_type=resolved_area_type,
        input_source="read_data",
        vehicle_totals=tuple(vehicle_totals),
    )


def compute_aadt_pcu_from_direct_input(
    base_aadt: int,
    base_pcu: float,
    *,
    design_years: int = 0,
    growth_rate: float = 0.0,
    design_year_label: str = "",
    area_type: str = DEFAULT_AREA_TYPE,
) -> AadtPcuResult:
    """Use manually entered AADT and PCU from the Direct Input section."""
    base_pcu_int = int(round(base_pcu))
    projected_aadt = project_traffic_value(float(base_aadt), design_years, growth_rate)
    projected_pcu = project_traffic_value(base_pcu, design_years, growth_rate)
    resolved_area_type = normalize_area_type(area_type)

    return AadtPcuResult(
        (),
        max(0, base_aadt),
        max(0, base_pcu_int),
        projected_aadt,
        projected_pcu,
        design_year_label=design_year_label,
        design_years=design_years,
        growth_rate=growth_rate,
        area_type=resolved_area_type,
        input_source="direct_input",
    )


def compute_aadt_pcu_from_workbook_data(
    data: dict,
    *,
    design_years: int = 0,
    growth_rate: float = 0.0,
    design_year_label: str = "",
    area_type: str = DEFAULT_AREA_TYPE,
) -> AadtPcuResult:
    """Convenience wrapper for session data stored in main_window."""
    daily_totals = data.get("daily_totals")
    daily_totals_12h = data.get("daily_totals_12h")
    daily_totals_24h = data.get("daily_totals_24h")
    survey_hours = int(data.get("survey_hours") or 12)
    count_hour = data.get("traffic_count_hour", "12h")
    summary_total_row = data.get("summary_total_row")

    if daily_totals or daily_totals_12h or daily_totals_24h:
        return compute_aadt_pcu(
            daily_totals,
            daily_totals_12h=daily_totals_12h,
            daily_totals_24h=daily_totals_24h,
            survey_hours=survey_hours,
            count_hour=count_hour,
            design_years=design_years,
            growth_rate=growth_rate,
            design_year_label=design_year_label,
            area_type=area_type,
        )
    if summary_total_row:
        return compute_aadt_pcu(
            summary_total_row=summary_total_row,
            design_years=design_years,
            growth_rate=growth_rate,
            design_year_label=design_year_label,
            area_type=area_type,
        )
    return _empty_result(
        design_year_label=design_year_label,
        design_years=design_years,
        growth_rate=growth_rate,
        area_type=area_type,
    )
