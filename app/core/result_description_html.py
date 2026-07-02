"""Shared rich-text HTML for Traffic Analysis result description panels."""

from __future__ import annotations

from app.core.ui_scale import UiScale

_BASE_BODY_PX = 20
_BASE_LINE_HEIGHT_PX = 20
_BASE_LINE_GAP_PX = 28
_BASE_TITLE_PX = 16


def _scaled_sizes(*, panel_width: int | None = None) -> tuple[int, int, int]:
    if panel_width and panel_width > 0:
        font_px = UiScale.px_local(_BASE_BODY_PX, panel_width, reference=320)
        line_px = UiScale.px_local(_BASE_LINE_HEIGHT_PX, panel_width, reference=320)
        gap_px = UiScale.px_local(_BASE_LINE_GAP_PX, panel_width, reference=320)
    else:
        font_px = UiScale.px(_BASE_BODY_PX)
        line_px = UiScale.px(_BASE_LINE_HEIGHT_PX)
        gap_px = UiScale.px(_BASE_LINE_GAP_PX)
    return font_px, line_px, gap_px


def result_body_style(*, panel_width: int | None = None) -> str:
    font_px, line_px, _gap_px = _scaled_sizes(panel_width=panel_width)
    return f"color:#ffffff; font-size:{font_px}px; line-height:{line_px}px; margin:0; padding:0;"


def result_emphasis_style() -> str:
    gap_px = UiScale.px(_BASE_LINE_GAP_PX)
    font_px = UiScale.px(_BASE_BODY_PX)
    line_px = UiScale.px(_BASE_LINE_HEIGHT_PX)
    return (
        f"margin-top:{gap_px}px; margin-bottom:0px; margin-left:0px; margin-right:0px; "
        f"font-size:{font_px}px; line-height:{line_px}px; font-weight:700; color:#ffffff;"
    )


def result_highlight_style() -> str:
    font_px = UiScale.px(_BASE_BODY_PX)
    line_px = UiScale.px(_BASE_LINE_HEIGHT_PX)
    return f"color:#ffffff; font-weight:700; font-size:{font_px}px; line-height:{line_px}px;"


def result_title_style() -> str:
    font_px = UiScale.px(_BASE_TITLE_PX)
    return f"font-size:{font_px}px; font-weight:600; color:#ffffff;"


def result_line_gap_px(*, panel_width: int | None = None) -> int:
    if panel_width and panel_width > 0:
        return UiScale.px_local(_BASE_LINE_GAP_PX, panel_width, reference=320)
    return UiScale.px(_BASE_LINE_GAP_PX)


# Backward-compatible names for imports that expect constants at import time.
RESULT_DESCRIPTION_BODY_STYLE = result_body_style()
RESULT_DESCRIPTION_EMPHASIS_STYLE = result_emphasis_style()
RESULT_DESCRIPTION_HIGHLIGHT_STYLE = result_highlight_style()
RESULT_DESCRIPTION_TITLE_STYLE = result_title_style()
RESULT_DESCRIPTION_LINE_GAP_PX = result_line_gap_px()


def _line_block(line: str, *, gap_after: int, panel_width: int | None = None) -> str:
    font_px, line_px, _gap_px = _scaled_sizes(panel_width=panel_width)
    block_style = (
        f"margin-top:0px; margin-bottom:{gap_after}px; margin-left:0px; margin-right:0px; "
        f"font-size:{font_px}px; line-height:{line_px}px; color:#ffffff;"
    )
    return f'<p style="{block_style}">{line}</p>'


def wrap_result_description_lines(
    lines: list[str],
    *,
    panel_width: int | None = None,
) -> str:
    """Build QLabel-friendly HTML with even spacing between lines."""
    if not lines:
        return f'<div style="{result_body_style(panel_width=panel_width)}"></div>'

    gap = result_line_gap_px(panel_width=panel_width)
    blocks = [
        _line_block(
            line,
            gap_after=0 if index == len(lines) - 1 else gap,
            panel_width=panel_width,
        )
        for index, line in enumerate(lines)
    ]
    return f'<div style="{result_body_style(panel_width=panel_width)}">{"".join(blocks)}</div>'


def wrap_result_description_with_emphasis(
    lines: list[str],
    emphasis_html: str | None = None,
) -> str:
    """Body lines plus an optional emphasis line at the end."""
    if not lines and not emphasis_html:
        return f'<div style="{result_body_style()}"></div>'

    gap = result_line_gap_px()
    blocks: list[str] = []
    for index, line in enumerate(lines):
        gap_after = gap if index < len(lines) - 1 or emphasis_html else 0
        blocks.append(_line_block(line, gap_after=gap_after))

    if emphasis_html:
        blocks.append(f'<p style="{result_emphasis_style()}">{emphasis_html}</p>')

    return f'<div style="{result_body_style()}">{"".join(blocks)}</div>'
