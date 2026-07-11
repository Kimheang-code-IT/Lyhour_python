"""Tests for level of service suggestions."""
from app.data.level_of_service import (
    build_lane_los_suggestion_text,
    suggest_level_of_service,
)


def test_suggest_level_of_service_r4_u4() -> None:
    assert suggest_level_of_service("R4/U4") == "A"


def test_suggest_level_of_service_r3_u3() -> None:
    assert suggest_level_of_service("R3/U3") == "C"


def test_suggest_level_of_service_invalid() -> None:
    assert suggest_level_of_service(None) is None
    assert suggest_level_of_service("") is None


def test_build_lane_los_suggestion_text() -> None:
    text = build_lane_los_suggestion_text("R4/U4", "A")
    assert "R4/U4" in text
    assert ">A<" in text or ">A</span>" in text
