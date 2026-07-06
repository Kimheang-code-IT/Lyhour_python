"""Layout name → class registry (like Nuxt ``layouts/`` folder)."""
from __future__ import annotations

from typing import Type

from app.layouts.base import BaseLayout
from app.layouts.blank import BlankLayout
from app.layouts.default import DefaultLayout
from app.layouts.scroll import ScrollLayout

LAYOUT_REGISTRY: dict[str, Type[BaseLayout]] = {
    DefaultLayout.name: DefaultLayout,
    ScrollLayout.name: ScrollLayout,
    BlankLayout.name: BlankLayout,
}

DEFAULT_LAYOUT = DefaultLayout.name


def get_layout(name: str) -> Type[BaseLayout]:
    key = (name or DEFAULT_LAYOUT).strip().lower()
    try:
        return LAYOUT_REGISTRY[key]
    except KeyError as exc:
        known = ", ".join(sorted(LAYOUT_REGISTRY))
        raise ValueError(f"Unknown layout {name!r}. Registered layouts: {known}") from exc


def register_layout(layout_cls: Type[BaseLayout]) -> Type[BaseLayout]:
    """Register a custom layout class (``layout_cls.name`` must be unique)."""
    LAYOUT_REGISTRY[layout_cls.name] = layout_cls
    return layout_cls
