"""Page metadata and ``define_page`` decorator (Nuxt ``definePageMeta`` style)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PageMeta:
    layout: str = "default"
    title: str = ""


def define_page(
    layout: str = "default",
    *,
    title: str = "",
) -> Callable[[type[T]], type[T]]:
    """Attach layout metadata to a page class.

    Example::

        @define_page("default", title="Cross Section")
        class RGDCrossSectionPage(BasePage):
            def setup(self, content):
                ...
    """

    def decorator(cls: type[T]) -> type[T]:
        cls.page_meta = PageMeta(layout=layout, title=title)  # type: ignore[attr-defined]
        cls.layout_name = layout  # type: ignore[attr-defined]
        cls.title = title  # type: ignore[attr-defined]
        return cls

    return decorator
