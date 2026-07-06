"""Reusable stylesheet snippets with responsive font sizes."""

from __future__ import annotations

from app.core.theme import theme_tokens
from app.core.ui_scale import UiScale


def px(base: float) -> int:
    return UiScale.px(base)


def label_style(
    base_px: float,
    *,
    bold: bool = False,
    color: str | None = None,
    extra: str = "",
) -> str:
    tokens = theme_tokens()
    resolved_color = color or tokens.text_primary
    weight = "bold" if bold else "normal"
    style = f"font-size: {px(base_px)}px; font-weight: {weight}; color: {resolved_color};"
    if extra:
        style = f"{style} {extra}"
    return style


def title_style(base_px: float = 22) -> str:
    return label_style(base_px, bold=True)


def subtitle_style(base_px: float = 14, *, color: str | None = None) -> str:
    tokens = theme_tokens()
    return label_style(base_px, color=color or tokens.text_muted)


def section_title_style(base_px: float = 18) -> str:
    return label_style(base_px, bold=True)


def card_title_style(base_px: float = 14) -> str:
    return label_style(base_px, bold=True)


def muted_style(base_px: float = 15) -> str:
    tokens = theme_tokens()
    return label_style(base_px, color=tokens.text_muted, extra="padding: 24px;")
