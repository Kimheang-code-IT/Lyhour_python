"""Road cross-section geometry from design inputs.

Builds a typical divided carriageway section (cut–shoulder–lanes–median–lanes–
shoulder–fill) using lane / shoulder widths and road class / design speed.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrossSectionSegment:
    """One horizontal segment of the cross-section (left → right)."""

    name: str
    width_m: float
    surface: str  # "earth" | "shoulder" | "lane" | "median"
    cross_slope_percent: float  # positive = falls to the right
    label: str = ""


@dataclass(frozen=True)
class CrossSectionDesign:
    road_classification: str
    design_speed_kmh: float
    lane_width_m: float
    shoulder_width_m: float
    lanes_per_direction: int
    median_width_m: float
    carriageway_cross_slope_percent: float
    shoulder_cross_slope_percent: float
    cut_slope_ratio: str  # e.g. "1:1.5" (V:H)
    fill_slope_ratio: str
    segments: tuple[CrossSectionSegment, ...]

    @property
    def total_width_m(self) -> float:
        return sum(seg.width_m for seg in self.segments)

    @property
    def title(self) -> str:
        return (
            f"{self.road_classification}  ·  V = {self.design_speed_kmh:.0f} km/h  ·  "
            f"{self.lanes_per_direction}+{self.lanes_per_direction} lanes"
        )


def _lanes_per_direction(road_classification: str, design_speed_kmh: float) -> int:
    code = (road_classification or "").split("/")[0].upper()
    if code in {"R1", "R2"} or design_speed_kmh >= 80:
        return 2
    return 1


def _median_width_m(road_classification: str, design_speed_kmh: float) -> float:
    code = (road_classification or "").split("/")[0].upper()
    if code == "R1":
        return 3.0
    if code == "R2":
        return 2.5
    if design_speed_kmh >= 80:
        return 2.0
    if design_speed_kmh >= 60:
        return 1.5
    return 1.0


def build_cross_section(
    *,
    road_classification: str,
    design_speed_kmh: float,
    lane_width_m: float,
    shoulder_width_m: float,
) -> CrossSectionDesign:
    """Build a left→right segment stack from page inputs."""
    lane_w = max(2.5, float(lane_width_m))
    shoulder_w = max(0.5, float(shoulder_width_m))
    lanes_n = _lanes_per_direction(road_classification, design_speed_kmh)
    median_w = _median_width_m(road_classification, design_speed_kmh)

    carriageway_slope = 2.0
    shoulder_slope = 4.0

    # Slope bench widths (visual only — earthworks beyond paved area).
    cut_bench = max(2.0, shoulder_w * 0.9)
    fill_bench = max(2.0, shoulder_w * 0.9)

    segments: list[CrossSectionSegment] = [
        CrossSectionSegment(
            name="cut",
            width_m=cut_bench,
            surface="earth",
            cross_slope_percent=-35.0,
            label="Cut Slope",
        ),
        CrossSectionSegment(
            name="shoulder_left",
            width_m=shoulder_w,
            surface="shoulder",
            cross_slope_percent=-shoulder_slope,
            label="Shoulder",
        ),
    ]

    for i in range(lanes_n):
        segments.append(
            CrossSectionSegment(
                name=f"lane_left_{i + 1}",
                width_m=lane_w,
                surface="lane",
                cross_slope_percent=-carriageway_slope,
                label=f"Lane {i + 1}",
            )
        )

    segments.append(
        CrossSectionSegment(
            name="median",
            width_m=median_w,
            surface="median",
            cross_slope_percent=0.0,
            label="Median",
        )
    )

    for i in range(lanes_n):
        segments.append(
            CrossSectionSegment(
                name=f"lane_right_{i + 1}",
                width_m=lane_w,
                surface="lane",
                cross_slope_percent=carriageway_slope,
                label=f"Lane {lanes_n + i + 1}",
            )
        )

    segments.append(
        CrossSectionSegment(
            name="shoulder_right",
            width_m=shoulder_w,
            surface="shoulder",
            cross_slope_percent=shoulder_slope,
            label="Shoulder",
        )
    )
    segments.append(
        CrossSectionSegment(
            name="fill",
            width_m=fill_bench,
            surface="earth",
            cross_slope_percent=35.0,
            label="Fill Slope",
        )
    )

    return CrossSectionDesign(
        road_classification=road_classification,
        design_speed_kmh=float(design_speed_kmh),
        lane_width_m=lane_w,
        shoulder_width_m=shoulder_w,
        lanes_per_direction=lanes_n,
        median_width_m=median_w,
        carriageway_cross_slope_percent=carriageway_slope,
        shoulder_cross_slope_percent=shoulder_slope,
        cut_slope_ratio="1:1.5",
        fill_slope_ratio="1:2",
        segments=tuple(segments),
    )
