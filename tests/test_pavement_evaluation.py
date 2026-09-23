"""Tests for pavement evaluation traffic-class table."""
from app.data.pavement_evaluation import (
    SELECTED_SUBGRADE_MM,
    TRAFFIC_CLASSES,
    compute_pavement_evaluation,
)


def test_traffic_classes_are_t1_to_t8() -> None:
    assert TRAFFIC_CLASSES == ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8")


def test_evaluation_layers_shape() -> None:
    result = compute_pavement_evaluation("T7")
    assert result.traffic == "T7"
    assert [layer.key for layer in result.layers] == [
        "ac",
        "base",
        "subbase",
        "selected_subgrade",
        "subgrade",
    ]


def test_selected_subgrade_fixed_and_subgrade_has_no_thickness() -> None:
    result = compute_pavement_evaluation("T3")
    by_key = {layer.key: layer for layer in result.layers}
    assert by_key["selected_subgrade"].thickness_mm == SELECTED_SUBGRADE_MM
    assert by_key["subgrade"].thickness_mm is None


def test_field_values_present_for_every_layer() -> None:
    for traffic in TRAFFIC_CLASSES:
        result = compute_pavement_evaluation(traffic)
        for layer in result.layers:
            assert layer.fwd_mpa is not None
            assert layer.lwd_mpa is not None
            assert layer.b_beam_mm is not None


def test_unknown_traffic_is_empty() -> None:
    result = compute_pavement_evaluation("T99")
    by_key = {layer.key: layer for layer in result.layers}
    assert by_key["ac"].thickness_mm is None
    assert by_key["base"].thickness_mm is None
    assert by_key["subbase"].thickness_mm is None
    assert by_key["selected_subgrade"].thickness_mm == SELECTED_SUBGRADE_MM
    assert all(layer.fwd_mpa is None for layer in result.layers)
