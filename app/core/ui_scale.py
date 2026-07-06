"""Responsive UI scale based on the main content area width."""

from __future__ import annotations

_REFERENCE_WIDTH = 1200
_MIN_SCALE = 0.85
_MAX_SCALE = 1.35


class UiScale:
    _factor = 1.0
    _width = _REFERENCE_WIDTH
    _user_font_scale = 1.0
    _compact_mode = False

    @classmethod
    def set_compact_mode(cls, enabled: bool) -> None:
        cls._compact_mode = bool(enabled)

    @classmethod
    def set_user_font_scale(cls, scale: float) -> None:
        cls._user_font_scale = max(0.85, min(1.35, float(scale or 1.0)))

    @classmethod
    def user_font_scale(cls) -> float:
        return cls._user_font_scale

    @classmethod
    def effective_factor(cls) -> float:
        compact = 0.92 if cls._compact_mode else 1.0
        return cls._factor * cls._user_font_scale * compact

    @classmethod
    def factor(cls) -> float:
        return cls._factor

    @classmethod
    def width(cls) -> int:
        return cls._width

    @classmethod
    def update(cls, width: int) -> bool:
        width = max(640, int(width or _REFERENCE_WIDTH))
        factor = max(_MIN_SCALE, min(_MAX_SCALE, width / _REFERENCE_WIDTH))
        changed = abs(factor - cls._factor) > 0.02 or width != cls._width
        cls._factor = factor
        cls._width = width
        return changed

    @classmethod
    def px(cls, base: float) -> int:
        return max(1, round(base * cls.effective_factor()))

    @classmethod
    def pt(cls, base: float) -> float:
        return max(6.0, round(base * cls.effective_factor(), 1))

    @classmethod
    def spacing(cls, base: float) -> int:
        return cls.px(base)

    @classmethod
    def local_factor(cls, width: int, *, reference: int) -> float:
        """Extra scale for narrow widgets such as side panels or tables."""
        width = max(1, int(width or reference))
        local = width / reference
        return max(0.8, min(1.15, local))

    @classmethod
    def px_local(cls, base: float, width: int, *, reference: int) -> int:
        return max(1, round(base * cls.effective_factor() * cls.local_factor(width, reference=reference)))

    @classmethod
    def pt_local(cls, base: float, width: int, *, reference: int) -> float:
        return max(6.0, round(base * cls.effective_factor() * cls.local_factor(width, reference=reference), 1))
