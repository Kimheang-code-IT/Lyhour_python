"""Backward-compatible alias. Prefer app.layouts.DefaultLayout or BasePage."""
from app.layouts.default import DefaultLayout

PageShell = DefaultLayout

__all__ = ["PageShell", "DefaultLayout"]
