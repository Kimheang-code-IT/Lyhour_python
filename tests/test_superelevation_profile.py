"""Tests for superelevation profile calculations."""
from app.data.superelevation_profile import compute_superelevation_profile, format_station


def test_superelevation_profile_lengths() -> None:
    profile = compute_superelevation_profile(
        e1_percent=2.5,
        e_max_percent=5.0,
        lane_width_m=3.5,
        relative_gradient_percent=0.30,
        curve_length_m=106.74,
        start_station_m=16_200,
    )

    assert profile is not None
    assert round(profile.transition_length_m, 2) == 87.50
    assert round(profile.tro_m, 2) == 29.17
    assert round(profile.sro_m, 2) == 58.33
    assert round(profile.cs_station_m, 2) == 16_394.24


def test_superelevation_profile_invalid_gradient() -> None:
    assert (
        compute_superelevation_profile(
            e1_percent=2.5,
            e_max_percent=5.0,
            lane_width_m=3.5,
            relative_gradient_percent=0.0,
            curve_length_m=106.74,
            start_station_m=16_200,
        )
        is None
    )


def test_y_axis_tick_labels() -> None:
    import numpy as np

    from app.data.superelevation_profile import (
        Y_AXIS_MAX,
        Y_AXIS_MIN,
        Y_AXIS_TICK_STEP,
        _format_y_tick,
    )

    yticks = np.arange(Y_AXIS_MIN, Y_AXIS_MAX + Y_AXIS_TICK_STEP / 2, Y_AXIS_TICK_STEP)
    assert list(yticks) == [-10.0, -7.5, -5.0, -2.5, 0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0]
    assert _format_y_tick(12.5) == "12.5"
    assert _format_y_tick(0) == "0"


def test_format_station() -> None:
    assert format_station(16_200) == "16+200"
    assert format_station(16_200.25) == "16+200.25"
