"""Nuxt-style layouts: assign ``layout`` per page, content fills a slot.

Quick start::

    from app.layouts import BasePage, define_page

    @define_page("default", title="Cross Section")
    class RGDCrossSectionPage(BasePage):
        def setup(self, content):
            content.addStretch()

Layouts live in this package (``default``, ``scroll``, ``blank``).
Register custom layouts with ``register_layout``.
"""

from app.layouts.base import BaseLayout
from app.layouts.blank import BlankLayout
from app.layouts.default import DefaultLayout
from app.layouts.meta import PageMeta, define_page
from app.layouts.page import BasePage
from app.layouts.registry import DEFAULT_LAYOUT, LAYOUT_REGISTRY, get_layout, register_layout
from app.layouts.scroll import ScrollLayout

__all__ = [
    "BaseLayout",
    "BasePage",
    "BlankLayout",
    "DEFAULT_LAYOUT",
    "DefaultLayout",
    "LAYOUT_REGISTRY",
    "PageMeta",
    "ScrollLayout",
    "define_page",
    "get_layout",
    "register_layout",
]
