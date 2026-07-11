"""Level of service options and suggestions from road classification."""
from __future__ import annotations

from app.utils.result_html import result_highlight_style

LOS_OPTIONS = ["A", "B", "C", "D", "E", "F"]

# Suggested LOS by rural/urban class level (1–5). R4/U4 → A per design reference.
_SUGGESTED_LOS_BY_LEVEL: dict[int, str] = {
    1: "E",
    2: "D",
    3: "C",
    4: "A",
    5: "B",
}


def _class_level(code: str) -> int | None:
    value = (code or "").strip()
    if len(value) < 2 or value[0] not in {"R", "U"} or not value[1].isdigit():
        return None
    return int(value[1])


def suggest_level_of_service(road_classification: str | None) -> str | None:
    """Return suggested LOS letter from a combined code such as R4/U4."""
    if not road_classification or "/" not in road_classification:
        return None
    rural, _, urban = road_classification.partition("/")
    rural_level = _class_level(rural)
    urban_level = _class_level(urban)
    levels = [level for level in (rural_level, urban_level) if level is not None]
    if not levels:
        return None
    return _SUGGESTED_LOS_BY_LEVEL.get(max(levels))


def build_lane_los_suggestion_text(
    road_classification: str | None,
    suggested_los: str | None,
) -> str:
    """HTML for: Road Classification is R4/U4 So LOS = A is suggested."""
    highlight = result_highlight_style()
    code = (road_classification or "").strip() or "—"
    los = (suggested_los or "").strip() or "—"
    return (
        f'Road Classification is <span style="{highlight}">{code}</span> '
        f'So LOS = <span style="{highlight}">{los}</span> is suggested'
    )
