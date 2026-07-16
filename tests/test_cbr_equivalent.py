"""Tests for CBR equivalent calculations."""
from app.data.cbr_equivalent import (
    compute_cbr_equivalent,
    compute_cbr_equivalent_from_user_layers,
    format_cbr_equivalent_result,
)
from app.data.dcp_analysis import DcpInputRow, analyze_dcp_rows


def test_compute_cbr_equivalent_weighted_average() -> None:
    rows = analyze_dcp_rows(
        [
            DcpInputRow(0, 0),
            DcpInputRow(4, 60),
            DcpInputRow(4, 130),
            DcpInputRow(5, 150),
        ]
    )
    result = compute_cbr_equivalent(rows, design_depth_mm=130.0)
    assert result is not None
    assert len(result.layers) == 2
    assert result.layers[0].from_depth_mm == 0.0
    assert result.layers[0].to_depth_mm == 60.0
    assert result.layers[1].from_depth_mm == 60.0
    assert result.layers[1].to_depth_mm == 130.0
    assert result.cbr_equivalent_percent is not None
    assert result.minimum_cbr_percent is not None


def test_compute_cbr_equivalent_respects_design_depth() -> None:
    rows = analyze_dcp_rows(
        [
            DcpInputRow(0, 0),
            DcpInputRow(4, 60),
            DcpInputRow(4, 130),
        ]
    )
    result = compute_cbr_equivalent(rows, design_depth_mm=80.0)
    assert result is not None
    assert len(result.layers) == 2
    assert result.layers[-1].to_depth_mm == 80.0
    assert result.total_thickness_mm == 80.0


def test_compute_cbr_equivalent_from_user_layers() -> None:
    result = compute_cbr_equivalent_from_user_layers(
        [(10.0, 100.0), (20.0, 100.0), (30.0, 100.0)],
        design_depth_mm=200.0,
    )
    assert result is not None
    assert len(result.layers) == 2
    assert result.total_thickness_mm == 200.0
    assert result.cbr_equivalent_percent == 15.0
    assert format_cbr_equivalent_result(result) == "Result = 15.00 %"
