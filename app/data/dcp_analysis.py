"""Dynamic Cone Penetrometer (DCP) test calculations."""
from __future__ import annotations

import math
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


@dataclass(frozen=True)
class DcpLayeredSummaryRow:
    """One row of the Layered CBR Summary table."""

    depth_mm: float
    layer_thickness_mm: float | None
    total_blows: float
    blows_per_300_mm: float | None
    layered_cbr_percent: float | None
    remark: str


DEFAULT_LAYER_INTERVAL_MM = 200.0


def cbr_from_penetration_index(penetration_index: float) -> float | None:
    """Empirical CBR correlation from mm/blow (calibrated to reference sample)."""
    if penetration_index <= 0:
        return None
    return 221.0 / penetration_index


def cbr_from_trl_penetration_index(penetration_index: float) -> float | None:
    """TRL layered-CBR correlation: log10(CBR) = 2.48 − 1.057·log10(PI)."""
    if penetration_index <= 0:
        return None
    return 10.0 ** (2.48 - 1.057 * math.log10(penetration_index))


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


def _cumulative_blows_at_depth(rows: list[DcpAnalysisRow], depth_mm: float) -> float:
    """Linearly interpolate cumulative blows at a target depth."""
    if not rows:
        return 0.0
    depth = max(0.0, float(depth_mm))
    if depth <= rows[0].total_penetration_mm:
        if rows[0].total_penetration_mm <= 0:
            return float(rows[0].total_blow_number)
        t = depth / rows[0].total_penetration_mm
        return t * float(rows[0].total_blow_number)

    for index in range(1, len(rows)):
        d0 = float(rows[index - 1].total_penetration_mm)
        d1 = float(rows[index].total_penetration_mm)
        b0 = float(rows[index - 1].total_blow_number)
        b1 = float(rows[index].total_blow_number)
        if depth <= d1:
            if d1 <= d0:
                return b1
            t = (depth - d0) / (d1 - d0)
            return b0 + t * (b1 - b0)

    return float(rows[-1].total_blow_number)


def _layered_cbr_remark(cbr_percent: float | None) -> str:
    if cbr_percent is None:
        return ""
    if cbr_percent < 3:
        return "Very poor"
    if cbr_percent < 5:
        return "Poor"
    if cbr_percent < 10:
        return "Fair"
    if cbr_percent < 15:
        return "Good"
    return "Excellent"


def build_layered_cbr_summary(
    rows: list[DcpAnalysisRow],
    *,
    layer_interval_mm: float = DEFAULT_LAYER_INTERVAL_MM,
) -> list[DcpLayeredSummaryRow]:
    """Aggregate DCP readings into fixed-depth layered CBR summary rows.

    Columns: Depth, Layer Thickness, Total Blows, Blows/300 mm, Layered-CBR, Remark.
    Blows/300 mm uses penetration index (mm/blow) as shown on typical MPWT sheets.
    Layered-CBR uses the TRL correlation from that index.
    """
    if not rows:
        return []

    interval = max(1.0, float(layer_interval_mm))
    max_depth = float(rows[-1].total_penetration_mm)
    summary: list[DcpLayeredSummaryRow] = [
        DcpLayeredSummaryRow(
            depth_mm=0.0,
            layer_thickness_mm=None,
            total_blows=_cumulative_blows_at_depth(rows, 0.0),
            blows_per_300_mm=None,
            layered_cbr_percent=None,
            remark="",
        )
    ]

    depth = 0.0
    while depth < max_depth - 1e-6:
        next_depth = min(depth + interval, max_depth)
        thickness = next_depth - depth
        if thickness <= 0:
            break

        blows_prev = _cumulative_blows_at_depth(rows, depth)
        blows_next = _cumulative_blows_at_depth(rows, next_depth)
        layer_blows = max(0.0, blows_next - blows_prev)

        blows_per_300 = None
        layered_cbr = None
        if thickness > 0 and layer_blows > 0:
            # Sheet column "Blows / 300 mm" shows mm/blow (penetration index).
            blows_per_300 = thickness / layer_blows
            layered_cbr = cbr_from_trl_penetration_index(blows_per_300)

        summary.append(
            DcpLayeredSummaryRow(
                depth_mm=next_depth,
                layer_thickness_mm=thickness,
                total_blows=blows_next,
                blows_per_300_mm=blows_per_300,
                layered_cbr_percent=layered_cbr,
                remark=_layered_cbr_remark(layered_cbr),
            )
        )
        depth = next_depth

    return summary


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
