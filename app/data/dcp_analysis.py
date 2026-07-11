"""Dynamic Cone Penetrometer (DCP) test calculations and charts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DcpInputRow:
    number_of_blow: float
    total_penetration_mm: float


@dataclass(frozen=True)
class DcpAnalysisRow:
    number_of_blow: float
    total_blow_number: float
    total_penetration_mm: float
    change_penetration_mm: float | None
    penetration_index_mm_per_blow: float | None
    cbr_percent: float | None


def cbr_from_penetration_index(penetration_index: float) -> float | None:
    """Empirical CBR correlation from mm/blow (calibrated to reference sample)."""
    if penetration_index <= 0:
        return None
    return 221.0 / penetration_index


def analyze_dcp_rows(rows: list[DcpInputRow]) -> list[DcpAnalysisRow]:
    """Build the full DCP analysis table from input blows and cumulative depth."""
    results: list[DcpAnalysisRow] = []
    cumulative_blows = 0.0
    previous_depth = 0.0

    for row in rows:
        blows = max(0.0, float(row.number_of_blow))
        depth = max(0.0, float(row.total_penetration_mm))
        cumulative_blows += blows

        if depth < previous_depth:
            depth = previous_depth

        change = None
        penetration_index = None
        cbr = None

        if len(results) > 0:
            change = depth - previous_depth
            if blows > 0 and change is not None:
                penetration_index = change / blows
                cbr = cbr_from_penetration_index(penetration_index)

        results.append(
            DcpAnalysisRow(
                number_of_blow=blows,
                total_blow_number=cumulative_blows,
                total_penetration_mm=depth,
                change_penetration_mm=change,
                penetration_index_mm_per_blow=penetration_index,
                cbr_percent=cbr,
            )
        )
        previous_depth = depth

    return results


def summarize_dcp_analysis(rows: list[DcpAnalysisRow]) -> dict[str, str]:
    """Compact DCP summary for the quick-results panel."""
    if not rows:
        return {}

    valid_cbr = [row.cbr_percent for row in rows if row.cbr_percent is not None]
    last = rows[-1]
    summary: dict[str, str] = {
        "Number of layers": str(len(rows)),
        "Maximum depth": f"{last.total_penetration_mm:,.0f} mm",
        "Total blow number": f"{last.total_blow_number:,.0f}",
    }
    if valid_cbr:
        summary["CBR at max depth"] = f"{valid_cbr[-1]:,.2f} %"
        summary["Minimum CBR"] = f"{min(valid_cbr):,.2f} %"
        summary["Average CBR"] = f"{sum(valid_cbr) / len(valid_cbr):,.2f} %"
    return summary


def draw_dcp_depth_vs_blows(ax: Any, rows: list[DcpAnalysisRow]) -> None:
    """Depth (inverted) vs cumulative blows."""
    plot_rows = [row for row in rows if row.total_blow_number > 0 or row.total_penetration_mm > 0]
    if len(plot_rows) < 2:
        ax.text(0.5, 0.5, "Enter DCP data to plot", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return

    x = [row.total_blow_number for row in plot_rows]
    y = [row.total_penetration_mm for row in plot_rows]

    ax.plot(x, y, color="#1f77b4", marker="o", markerfacecolor="white", linewidth=1.8)
    ax.set_xlabel("Total Blow Number")
    ax.set_ylabel("Total Penetration (mm)")
    ax.set_title("Depth vs Total Blows", pad=10)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.35)


def draw_dcp_depth_vs_cbr(ax: Any, rows: list[DcpAnalysisRow]) -> None:
    """Depth (inverted) vs CBR%."""
    plot_rows = [
        row
        for row in rows
        if row.cbr_percent is not None and row.total_penetration_mm > 0
    ]
    if len(plot_rows) < 2:
        ax.text(0.5, 0.5, "Enter DCP data to plot", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return

    x = [row.cbr_percent for row in plot_rows]
    y = [row.total_penetration_mm for row in plot_rows]

    ax.plot(x, y, color="#d62728", marker="D", markerfacecolor="white", linewidth=1.8)
    ax.set_xlabel("CBR (%)")
    ax.set_ylabel("Total Penetration (mm)")
    ax.set_title("Depth vs CBR", pad=10)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.35)
