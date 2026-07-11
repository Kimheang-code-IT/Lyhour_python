"""Future lane requirement projection from D1/D2 peak hour volumes."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CAPACITY_PER_LANE = 1710
DEFAULT_VC_RATIO = 0.85
DEFAULT_FW = 1.0
DEFAULT_FHV = 1.0
DEFAULT_START_YEAR = 2025
DEFAULT_GROWTH_RATE = 0.05
FUTURE_YEARS = list(range(2025, 2046, 5))

PROJECTION_COLUMNS = [
    "Year",
    "D1 Projected Volume",
    "D2 Projected Volume",
    "D1 Required Lanes",
    "D2 Required Lanes",
    "Total Required Lanes",
]

ProjectionRow = dict[str, Any]


@dataclass(frozen=True)
class LaneProjectionResult:
    d1_peak_volume: int
    d2_peak_volume: int
    projection_rows: tuple[ProjectionRow, ...]

    @property
    def has_data(self) -> bool:
        return bool(self.projection_rows)

    @property
    def projection_table_rows(self) -> list[list[str]]:
        """Table rows for the lane projection summary table."""
        rows: list[list[str]] = []
        for row in self.projection_rows:
            rows.append([
                str(int(row["Year"])),
                f"{float(row['D1 Projected Volume']):,.0f}",
                f"{float(row['D2 Projected Volume']):,.0f}",
                str(int(row["D1 Required Lanes"])),
                str(int(row["D2 Required Lanes"])),
                str(int(row["Total Required Lanes"])),
            ])
        return rows


def peak_hour_volume(hourly_rows: list[list]) -> int:
    """Return the maximum hourly total volume from one sheet (last column)."""
    if not hourly_rows:
        return 0
    return max(int(row[-1]) for row in hourly_rows)


def peak_hour_volumes_from_sheets(sheets: dict[str, list[list]]) -> tuple[int, int]:
    """Peak hour volume for D1 and D2 using raw hourly rows only."""
    d1_peak = peak_hour_volume(sheets.get("D1") or [])
    d2_peak = peak_hour_volume(sheets.get("D2") or [])
    return d1_peak, d2_peak


def required_lanes(
    volume: float,
    *,
    capacity_per_lane: float = DEFAULT_CAPACITY_PER_LANE,
    vc_ratio: float = DEFAULT_VC_RATIO,
    fw: float = DEFAULT_FW,
    fhv: float = DEFAULT_FHV,
) -> int:
    """lanes = ceil(volume / (capacity_per_lane * vc_ratio * fw * fHV))"""
    if volume <= 0:
        return 0
    denominator = capacity_per_lane * vc_ratio * fw * fhv
    if denominator <= 0:
        return 0
    return math.ceil(volume / denominator)


def projected_volume(
    base_peak_volume: float,
    future_year: int,
    *,
    start_year: int = DEFAULT_START_YEAR,
    growth_rate: float = DEFAULT_GROWTH_RATE,
) -> float:
    """future_volume = base_peak_volume * ((1 + growth_rate) ** (future_year - start_year))"""
    years_ahead = future_year - start_year
    return base_peak_volume * ((1 + growth_rate) ** years_ahead)


def build_lane_projection_table(
    d1_peak_volume: int,
    d2_peak_volume: int,
    *,
    growth_rate: float = DEFAULT_GROWTH_RATE,
    start_year: int = DEFAULT_START_YEAR,
    future_years: list[int] | None = None,
    capacity_per_lane: float = DEFAULT_CAPACITY_PER_LANE,
    vc_ratio: float = DEFAULT_VC_RATIO,
    fw: float = DEFAULT_FW,
    fhv: float = DEFAULT_FHV,
) -> list[ProjectionRow]:
    """Build the future lane projection table for D1 and D2."""
    years = future_years or FUTURE_YEARS
    rows: list[ProjectionRow] = []

    for future_year in years:
        d1_volume = projected_volume(
            d1_peak_volume,
            future_year,
            start_year=start_year,
            growth_rate=growth_rate,
        )
        d2_volume = projected_volume(
            d2_peak_volume,
            future_year,
            start_year=start_year,
            growth_rate=growth_rate,
        )
        d1_lanes = required_lanes(
            d1_volume,
            capacity_per_lane=capacity_per_lane,
            vc_ratio=vc_ratio,
            fw=fw,
            fhv=fhv,
        )
        d2_lanes = required_lanes(
            d2_volume,
            capacity_per_lane=capacity_per_lane,
            vc_ratio=vc_ratio,
            fw=fw,
            fhv=fhv,
        )
        rows.append({
            "Year": future_year,
            "D1 Projected Volume": round(d1_volume, 2),
            "D2 Projected Volume": round(d2_volume, 2),
            "D1 Required Lanes": d1_lanes,
            "D2 Required Lanes": d2_lanes,
            "Total Required Lanes": d1_lanes + d2_lanes,
        })

    return rows


def print_lane_projection_table(projection_rows: list[ProjectionRow]) -> None:
    """Format the future projection table (no stdout output)."""
    _ = projection_rows


def save_lane_projection_chart(
    projection_rows: list[ProjectionRow],
    chart_path: str | Path,
    *,
    title: str = "Required Road Lanes by Future Year",
) -> Path:
    """Save a bar chart of total required lanes by year (optional export)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chart_path = Path(chart_path)
    chart_path.parent.mkdir(parents=True, exist_ok=True)

    years = [int(row["Year"]) for row in projection_rows]
    totals = [int(row["Total Required Lanes"]) for row in projection_rows]

    figure, axis = plt.subplots(figsize=(10, 6))
    bars = axis.bar(years, totals, color="#156082", width=3.5)
    axis.set_xlabel("Year")
    axis.set_ylabel("Total Required Lanes")
    axis.set_title(title)
    axis.set_xticks(years)
    axis.set_xticklabels([str(year) for year in years])

    for bar, value in zip(bars, totals):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            str(value),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    figure.tight_layout()
    figure.savefig(chart_path, dpi=150)
    plt.close(figure)
    return chart_path


def save_lane_projection_excel(projection_rows: list[ProjectionRow], excel_path: str | Path) -> Path:
    """Save projection table to Excel (optional export)."""
    import pandas as pd

    excel_path = Path(excel_path)
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(projection_rows, columns=PROJECTION_COLUMNS).to_excel(
        excel_path,
        index=False,
        sheet_name="Lane Projection",
    )
    return excel_path


def save_lane_projection_outputs(
    projection_rows: list[ProjectionRow],
    output_dir: str | Path,
    *,
    excel_name: str = "traffic_lane_projection.xlsx",
    chart_name: str = "traffic_lane_projection_chart.png",
) -> tuple[Path, Path]:
    """Save projection table and chart image (optional export)."""
    output_dir = Path(output_dir)
    excel_path = save_lane_projection_excel(projection_rows, output_dir / excel_name)
    chart_path = save_lane_projection_chart(projection_rows, output_dir / chart_name)
    return excel_path, chart_path


def compute_lane_projection_from_workbook_data(
    workbook_data: dict,
    *,
    growth_rate: float = DEFAULT_GROWTH_RATE,
    start_year: int = DEFAULT_START_YEAR,
    output_dir: str | Path | None = None,
    save_outputs: bool = False,
    print_table: bool = False,
) -> LaneProjectionResult:
    """
    Calculate lane projection from temporary D1/D2 session data.

    Uses workbook_data["sheets"] produced by read_traffic_investigation_workbook().
    No files are written unless save_outputs=True.
    """
    sheets = workbook_data.get("sheets") or {}
    d1_peak, d2_peak = peak_hour_volumes_from_sheets(sheets)

    projection_rows = build_lane_projection_table(
        d1_peak,
        d2_peak,
        growth_rate=growth_rate,
        start_year=start_year,
    )

    if print_table:
        print_lane_projection_table(projection_rows)

    if save_outputs:
        target_dir = Path(output_dir) if output_dir else Path(workbook_data.get("source_path", ".")).parent
        save_lane_projection_outputs(projection_rows, target_dir)

    return LaneProjectionResult(
        d1_peak_volume=d1_peak,
        d2_peak_volume=d2_peak,
        projection_rows=tuple(projection_rows),
    )


def chart_bars_from_projection(projection_rows: list[ProjectionRow]) -> list[tuple[str, float, str]]:
    """Convert projection rows to UI bar chart tuples."""
    colors = ["#156082", "#e97132", "#196b24", "#0f9ed5", "#a02b93"]
    bars: list[tuple[str, float, str]] = []
    for index, row in enumerate(projection_rows):
        color = colors[index % len(colors)]
        bars.append((str(int(row["Year"])), float(row["Total Required Lanes"]), color))
    return bars
