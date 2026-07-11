"""Tests for simple horizontal curve geometry."""
import math

from app.data.simple_curve_geometry import compute_simple_curve_elements, format_angle_dms


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
