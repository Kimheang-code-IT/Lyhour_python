"""CBR Equivalent calculations from DCP layer CBR values."""
from __future__ import annotations

from dataclasses import dataclass

from typing import Any

from app.data.dcp_analysis import DcpAnalysisRow


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


def compute_cbr_equivalent(
    rows: list[DcpAnalysisRow],
    *,
    design_depth_mm: float = 300.0,
) -> CbrEquivalentResult | None:
    """Thickness-weighted CBR equivalent over the top ``design_depth_mm`` of subgrade."""
    depth = float(design_depth_mm)
    if depth <= 0:
        return None

    layers: list[CbrEquivalentLayer] = []
    weighted_sum = 0.0
    thickness_sum = 0.0
    minimum_cbr: float | None = None

    for index, row in enumerate(rows):
        if index == 0 or row.cbr_percent is None:
            continue

        previous_depth = float(rows[index - 1].total_penetration_mm)
        layer_bottom = min(float(row.total_penetration_mm), depth)
        layer_top = previous_depth
        if layer_top >= depth:
            break

        thickness = layer_bottom - layer_top
        if thickness <= 0:
            continue

        cbr = float(row.cbr_percent)
        contribution = cbr * thickness
        layers.append(
            CbrEquivalentLayer(
                layer_no=len(layers) + 1,
                from_depth_mm=layer_top,
                to_depth_mm=layer_bottom,
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
            design_depth_mm=depth,
            layers=tuple(),
            cbr_equivalent_percent=None,
            minimum_cbr_percent=None,
        )

    return CbrEquivalentResult(
        design_depth_mm=depth,
        layers=tuple(layers),
        cbr_equivalent_percent=weighted_sum / thickness_sum,
        minimum_cbr_percent=minimum_cbr,
    )


def summarize_cbr_equivalent(result: CbrEquivalentResult | None) -> dict[str, str]:
    """Compact summary for the quick-results panel."""
    if result is None:
        return {}

    summary: dict[str, str] = {
        "Design depth": f"{result.design_depth_mm:,.0f} mm",
        "Layers used": str(len(result.layers)),
    }
    if result.cbr_equivalent_percent is not None:
        summary["CBR Equivalent"] = f"{result.cbr_equivalent_percent:,.2f} %"
    if result.minimum_cbr_percent is not None:
        summary["Minimum CBR in zone"] = f"{result.minimum_cbr_percent:,.2f} %"
    return summary


def draw_cbr_equivalent_profile(ax: Any, result: CbrEquivalentResult) -> None:
    """Plot layer CBR values and the equivalent CBR line."""
    if not result.layers:
        ax.text(0.5, 0.5, "Enter DCP data to calculate CBR Equivalent", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return

    depths: list[float] = [result.layers[0].from_depth_mm]
    cbr_steps: list[float] = [result.layers[0].cbr_percent]
    for layer in result.layers:
        depths.extend([layer.to_depth_mm, layer.to_depth_mm])
        cbr_steps.extend([layer.cbr_percent, layer.cbr_percent])
    depths = depths[:-1]
    cbr_steps = cbr_steps[:-1]

    ax.plot(cbr_steps, depths, color="#1f77b4", linewidth=2.0, drawstyle="steps-post")
    if result.cbr_equivalent_percent is not None:
        ax.axvline(
            result.cbr_equivalent_percent,
            color="#d62728",
            linestyle="--",
            linewidth=1.6,
            label=f"CBR Equivalent = {result.cbr_equivalent_percent:.2f}%",
        )
        ax.legend(loc="lower right", fontsize=8)

    ax.set_xlabel("CBR (%)")
    ax.set_ylabel("Depth (mm)")
    ax.set_title("CBR Equivalent Profile", pad=10)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.35)
