"""Lightweight formatting helpers for UI and reports."""


def format_int(value: int | float | None) -> str | None:
    if value is None:
        return None
    number = int(round(value))
    if number <= 0:
        return None
    return f"{number:,}"


def format_ratio(value: float | None, *, decimals: int = 2) -> str | None:
    if value is None:
        return None
    return f"{value:.{decimals}f}"
