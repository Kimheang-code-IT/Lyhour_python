"""Dynamic Cone Penetrometer (DCP) test calculations."""
from __future__ import annotations

from dataclasses import dataclass


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
