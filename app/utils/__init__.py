"""Small stateless helpers. Business rules live in app.services."""

from app.utils.formatting import format_int, format_ratio
from app.utils.result_html import (
    RESULT_DESCRIPTION_BODY_STYLE,
    RESULT_DESCRIPTION_EMPHASIS_STYLE,
    RESULT_DESCRIPTION_HIGHLIGHT_STYLE,
    RESULT_DESCRIPTION_LINE_GAP_PX,
    RESULT_DESCRIPTION_TITLE_STYLE,
    result_body_style,
    result_emphasis_style,
    result_highlight_style,
    result_line_gap_px,
    result_title_style,
    wrap_result_description_lines,
    wrap_result_description_with_emphasis,
)

__all__ = [
    "format_int",
    "format_ratio",
    "result_body_style",
    "result_emphasis_style",
    "result_highlight_style",
    "result_line_gap_px",
    "result_title_style",
    "wrap_result_description_lines",
    "wrap_result_description_with_emphasis",
    "RESULT_DESCRIPTION_BODY_STYLE",
    "RESULT_DESCRIPTION_EMPHASIS_STYLE",
    "RESULT_DESCRIPTION_HIGHLIGHT_STYLE",
    "RESULT_DESCRIPTION_LINE_GAP_PX",
    "RESULT_DESCRIPTION_TITLE_STYLE",
]
