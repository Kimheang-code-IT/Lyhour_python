"""Build compact traffic analysis values for the Quick Results panel."""
from __future__ import annotations

from app.services.traffic_aadt_pcu import parse_design_years
from app.services.traffic_lane_projection import (
    DEFAULT_CAPACITY_PER_LANE,
    DEFAULT_FHV,
    DEFAULT_FW,
    DEFAULT_START_YEAR,
)


def _format_int(value: int | float | None) -> str | None:
    if value is None:
        return None
    number = int(round(value))
    if number <= 0:
        return None
    return f"{number:,}"


def _projection_row_at_design_year(
    projection_rows: list[dict],
    design_years: int,
    *,
    start_year: int = DEFAULT_START_YEAR,
) -> dict | None:
    if not projection_rows:
        return None
    if design_years <= 0:
        return projection_rows[-1]
    target_year = start_year + design_years
    for row in projection_rows:
        if int(row.get("Year", 0)) == target_year:
            return row
    return min(
        projection_rows,
        key=lambda row: abs(int(row.get("Year", 0)) - target_year),
    )


def capacity_ratio_for_row(row: dict | None) -> float | None:
    if not row:
        return None
    total_volume = float(row.get("D1 Projected Volume", 0)) + float(row.get("D2 Projected Volume", 0))
    total_lanes = int(row.get("Total Required Lanes", 0))
    if total_volume <= 0 or total_lanes <= 0:
        return None
    capacity = total_lanes * DEFAULT_CAPACITY_PER_LANE * DEFAULT_FW * DEFAULT_FHV
    if capacity <= 0:
        return None
    return total_volume / capacity


def _esal_period_for_pavement(
    design_periods: list[dict],
    pavement_design_years: int,
) -> dict | None:
    if not design_periods:
        return None
    if pavement_design_years > 0:
        for period in design_periods:
            if int(period.get("years", 0)) == pavement_design_years:
                return period
    for period in design_periods:
        if int(period.get("total_esal", 0)) > 0:
            return period
    return design_periods[0]


def build_traffic_quick_results(
    traffic_state: dict | None,
    *,
    geometry_design_year: str = "",
    pavement_design_year: str = "",
) -> dict[str, str]:
    traffic_state = traffic_state or {}
    aadt_pcu = traffic_state.get("aadt_pcu") or {}
    lane_projection = traffic_state.get("lane_projection") or {}
    esal_state = traffic_state.get("esal") or {}

    results: dict[str, str] = {}

    aadt = _format_int(aadt_pcu.get("projected_aadt", aadt_pcu.get("total_aadt")))
    if aadt:
        results["AADT"] = aadt

    pcu = _format_int(aadt_pcu.get("projected_pcu", aadt_pcu.get("total_pcu")))
    if pcu:
        results["PCU"] = pcu

    road_year = (geometry_design_year or aadt_pcu.get("design_year_label") or "").strip()
    if road_year and (aadt or pcu):
        results["Road classification"] = road_year

    design_years = parse_design_years(road_year)
    projection_rows = lane_projection.get("projection_rows") or []
    lane_row = _projection_row_at_design_year(projection_rows, design_years)
    if lane_row is not None:
        total_lanes = int(lane_row.get("Total Required Lanes", 0))
        if total_lanes > 0:
            results["Number of lane"] = str(total_lanes)

        ratio = capacity_ratio_for_row(lane_row)
        if ratio is not None:
            results["Capacity ratio"] = f"{ratio:.2f}"

    pavement_years = parse_design_years(pavement_design_year)
    esal_period = _esal_period_for_pavement(
        esal_state.get("design_periods") or [],
        pavement_years,
    )
    if esal_period is not None:
        total_esal = int(esal_period.get("total_esal", 0))
        traffic_class = str(esal_period.get("traffic_class", "")).strip()
        if total_esal > 0:
            label = f"{total_esal:,}"
            if traffic_class and traffic_class != "—":
                label = f"{label} ({traffic_class})"
            results["ESAL"] = label

    return results
