"""Tests for simple horizontal curve geometry."""
import math

from app.data.simple_curve_geometry import (
    compute_curve_stakeout,
    compute_simple_curve_elements,
    format_angle_dms,
)


def test_simple_curve_elements_example() -> None:
    # Reference: R=400, Δ≈79°14'55" → TL≈331.20, L≈553.26, C≈510.20, E≈119.32, M≈91.90
    deflection = 79 + 14 / 60 + 55.17 / 3600
    result = compute_simple_curve_elements(400.0, deflection)
    assert result is not None
    assert math.isclose(result.tangent_length_m, 331.20, rel_tol=0.002)
    assert math.isclose(result.curve_length_m, 553.26, rel_tol=0.002)
    assert math.isclose(result.chord_length_m, 510.20, rel_tol=0.002)
    assert math.isclose(result.external_distance_m, 119.32, rel_tol=0.002)
    assert math.isclose(result.middle_ordinate_m, 91.90, rel_tol=0.002)


def test_format_angle_dms() -> None:
    deflection = 79 + 14 / 60 + 55.17 / 3600
    assert format_angle_dms(deflection) == "79-14'55.17\""


def test_simple_curve_elements_invalid() -> None:
    assert compute_simple_curve_elements(0, 45) is None
    assert compute_simple_curve_elements(400, 0) is None
    assert compute_simple_curve_elements(400, 180) is None


def test_curve_stakeout_control_points() -> None:
    deflection = 79 + 14 / 60 + 55.17 / 3600
    elements = compute_simple_curve_elements(400.0, deflection)
    assert elements is not None

    rows = compute_curve_stakeout(400.0, deflection, pc_station_m=1000.0, interval_m=20.0)
    assert rows
    assert rows[0].name == "PC"
    assert math.isclose(rows[0].station_m, 1000.0)
    assert math.isclose(rows[0].chord_m, 0.0)

    assert rows[-1].name == "PI"
    assert math.isclose(rows[-1].station_m, 1000.0 + elements.tangent_length_m)
    assert math.isclose(rows[-1].x_m, elements.tangent_length_m)
    assert math.isclose(rows[-1].y_m, 0.0)

    pt = rows[-2]
    assert pt.name == "PT"
    assert math.isclose(pt.station_m, 1000.0 + elements.curve_length_m)
    assert math.isclose(pt.chord_m, elements.chord_length_m)
    assert math.isclose(pt.deflection_deg, deflection / 2.0)


def test_curve_stakeout_intermediate_spacing() -> None:
    deflection = 60.0
    rows = compute_curve_stakeout(300.0, deflection, pc_station_m=0.0, interval_m=20.0)
    arc_points = [r for r in rows if r.name == ""]
    assert arc_points
    assert all(math.isclose(r.arc_length_m % 20.0, 0.0, abs_tol=1e-6) for r in arc_points)


def test_curve_stakeout_invalid() -> None:
    assert compute_curve_stakeout(0, 45) == ()
    assert compute_curve_stakeout(400, 180) == ()
