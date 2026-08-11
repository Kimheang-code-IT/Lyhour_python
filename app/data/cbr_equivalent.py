"""CBR Equivalent calculations from DCP or user-defined layers."""
from __future__ import annotations

from dataclasses import dataclass

from app.data.dcp_analysis import DcpAnalysisRow, DcpLayeredSummaryRow


@dataclass(frozen=True)
class CbrEquivalentLayer:
    layer_no: int
    from_depth_mm: float
    to_depth_mm: float
    thickness_mm: float
    cbr_percent: float
    weighted_contribution: float


@dataclass(frozen=True)
class CbrEquivalentResult:
    design_depth_mm: float
    layers: tuple[CbrEquivalentLayer, ...]
    cbr_equivalent_percent: float | None
    minimum_cbr_percent: float | None

    @property
    def total_thickness_mm(self) -> float:
        return sum(layer.thickness_mm for layer in self.layers)


@dataclass(frozen=True)
class DcpCbrDisplayRow:
    """One row for the Use-DCP-data input table (English headers)."""

    depth_mm: float
    thickness_mm: float | None
    total_blows: float
    penetration_rate_mm_per_blow: float | None
    layered_cbr_percent: float | None
    evaluation: str


def evaluate_layered_cbr(cbr_percent: float | None) -> str:
    """Simple qualitative rating for the Evaluation column."""
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


def build_dcp_cbr_display_rows(rows: list[DcpAnalysisRow]) -> list[DcpCbrDisplayRow]:
    """Map raw DCP analysis rows to the English CBR input table (legacy)."""
    display: list[DcpCbrDisplayRow] = []
    for row in rows:
        display.append(
            DcpCbrDisplayRow(
                depth_mm=float(row.total_penetration_mm),
                thickness_mm=row.change_penetration_mm,
                total_blows=float(row.total_blow_number),
                penetration_rate_mm_per_blow=row.penetration_index_mm_per_blow,
                layered_cbr_percent=row.cbr_percent,
                evaluation=evaluate_layered_cbr(row.cbr_percent),
            )
        )
    return display


def _result_from_layer_parts(
    parts: list[tuple[float, float, float, float]],
    *,
    design_depth_mm: float,
) -> CbrEquivalentResult:
    """Build result from (from_depth, to_depth, thickness, cbr) parts."""
    layers: list[CbrEquivalentLayer] = []
    weighted_sum = 0.0
    thickness_sum = 0.0
    minimum_cbr: float | None = None

    for from_depth, to_depth, thickness, cbr in parts:
        if thickness <= 0:
            continue
        contribution = cbr * thickness
        layers.append(
            CbrEquivalentLayer(
                layer_no=len(layers) + 1,
                from_depth_mm=from_depth,
                to_depth_mm=to_depth,
                thickness_mm=thickness,
                cbr_percent=cbr,
                weighted_contribution=contribution,
            )
        )
        weighted_sum += contribution
        thickness_sum += thickness
        minimum_cbr = cbr if minimum_cbr is None else min(minimum_cbr, cbr)

    if not layers:
        return CbrEquivalentResult(
            design_depth_mm=design_depth_mm,
            layers=tuple(),
            cbr_equivalent_percent=None,
            minimum_cbr_percent=None,
        )

    return CbrEquivalentResult(
        design_depth_mm=design_depth_mm,
        layers=tuple(layers),
        cbr_equivalent_percent=weighted_sum / thickness_sum,
        minimum_cbr_percent=minimum_cbr,
    )


def compute_cbr_equivalent(
    rows: list[DcpAnalysisRow],
    *,
    design_depth_mm: float | None = None,
) -> CbrEquivalentResult | None:
    """Thickness-weighted CBR equivalent from DCP layers.

    When ``design_depth_mm`` is None, all DCP layers with CBR are used.
    """
    if design_depth_mm is not None and float(design_depth_mm) <= 0:
        return None

    depth_limit = float(design_depth_mm) if design_depth_mm is not None else None
    parts: list[tuple[float, float, float, float]] = []
    full_depth = 0.0

    for index, row in enumerate(rows):
        if index == 0 or row.cbr_percent is None:
            continue

        previous_depth = float(rows[index - 1].total_penetration_mm)
        layer_bottom = float(row.total_penetration_mm)
        layer_top = previous_depth
        full_depth = max(full_depth, layer_bottom)

        if depth_limit is not None:
            if layer_top >= depth_limit:
                break
            layer_bottom = min(layer_bottom, depth_limit)

        thickness = layer_bottom - layer_top
        if thickness <= 0:
            continue

        parts.append((layer_top, layer_bottom, thickness, float(row.cbr_percent)))

    design_depth = depth_limit if depth_limit is not None else full_depth
    return _result_from_layer_parts(parts, design_depth_mm=design_depth)


def compute_cbr_equivalent_from_user_layers(
    layers: list[tuple[float, float]],
    *,
    design_depth_mm: float | None = None,
) -> CbrEquivalentResult | None:
    """Thickness-weighted CBR from user pairs of (CBR %, Hi mm).

    When ``design_depth_mm`` is set, only the top zone up to that depth is used.
    """
    if not layers:
        return CbrEquivalentResult(
            design_depth_mm=float(design_depth_mm or 0.0),
            layers=tuple(),
            cbr_equivalent_percent=None,
            minimum_cbr_percent=None,
        )

    depth_limit = float(design_depth_mm) if design_depth_mm and design_depth_mm > 0 else None
    parts: list[tuple[float, float, float, float]] = []
    cursor = 0.0

    for cbr_raw, hi_raw in layers:
        cbr = float(cbr_raw)
        hi = float(hi_raw)
        if hi <= 0:
            continue

        layer_top = cursor
        layer_bottom = cursor + hi
        if depth_limit is not None:
            if layer_top >= depth_limit:
                break
            layer_bottom = min(layer_bottom, depth_limit)

        thickness = layer_bottom - layer_top
        if thickness <= 0:
            break

        parts.append((layer_top, layer_bottom, thickness, cbr))
        cursor = layer_bottom
        if depth_limit is not None and cursor >= depth_limit:
            break

    design_depth = depth_limit if depth_limit is not None else cursor
    return _result_from_layer_parts(parts, design_depth_mm=design_depth)


def display_rows_from_layered_summary(
    rows: list[DcpLayeredSummaryRow],
) -> list[DcpCbrDisplayRow]:
    """Map DCP Layered CBR Summary rows into the Use-DCP-data table."""
    return [
        DcpCbrDisplayRow(
            depth_mm=float(row.depth_mm),
            thickness_mm=row.layer_thickness_mm,
            total_blows=float(row.total_blows),
            penetration_rate_mm_per_blow=row.blows_per_300_mm,
            layered_cbr_percent=row.layered_cbr_percent,
            evaluation=row.remark or evaluate_layered_cbr(row.layered_cbr_percent),
        )
        for row in rows
    ]


def compute_cbr_equivalent_from_layered_summary(
    rows: list[DcpLayeredSummaryRow],
    *,
    design_depth_mm: float | None = None,
) -> CbrEquivalentResult | None:
    """Thickness-weighted CBR from DCP Layered CBR Summary rows."""
    layers: list[tuple[float, float]] = []
    for row in rows:
        if row.layer_thickness_mm is None or row.layered_cbr_percent is None:
            continue
        thickness = float(row.layer_thickness_mm)
        if thickness <= 0:
            continue
        layers.append((float(row.layered_cbr_percent), thickness))
    return compute_cbr_equivalent_from_user_layers(
        layers,
        design_depth_mm=design_depth_mm,
    )


def format_cbr_equivalent_result(result: CbrEquivalentResult | None) -> str:
    """Human-readable calculator result line."""
    if result is None or result.cbr_equivalent_percent is None:
        return "Result = —"
    return f"Result = {result.cbr_equivalent_percent:,.2f} %"


def summarize_cbr_equivalent(result: CbrEquivalentResult | None) -> dict[str, str]:
    """Compact summary for the quick-results panel."""
    if result is None:
        return {}

    summary: dict[str, str] = {
        "Layers used": str(len(result.layers)),
        "Total thickness": f"{result.total_thickness_mm:,.0f} mm",
    }
    if result.cbr_equivalent_percent is not None:
        summary["CBR Equivalent"] = f"{result.cbr_equivalent_percent:,.2f} %"
    if result.minimum_cbr_percent is not None:
        summary["Minimum CBR in zone"] = f"{result.minimum_cbr_percent:,.2f} %"
    return summary
