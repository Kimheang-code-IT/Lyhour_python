"""Application keyboard shortcut definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShortcutSpec:
    id: str
    label_key: str
    sequence: str
    category_key: str = "shortcuts.category.app"
    toggleable: bool = True


APP_SHORTCUTS: tuple[ShortcutSpec, ...] = (
    ShortcutSpec("search", "shortcuts.search", "Ctrl+K"),
    ShortcutSpec("toggle_sidebar", "shortcuts.toggle_sidebar", "Ctrl+B"),
    ShortcutSpec("settings", "shortcuts.settings", "Ctrl+,"),
    ShortcutSpec("help", "shortcuts.help", "F1"),
    ShortcutSpec(
        "search_open",
        "shortcuts.search_open",
        "Enter",
        category_key="shortcuts.category.search_palette",
        toggleable=False,
    ),
    ShortcutSpec(
        "search_close",
        "shortcuts.search_close",
        "Esc",
        category_key="shortcuts.category.search_palette",
        toggleable=False,
    ),
    ShortcutSpec(
        "search_navigate",
        "shortcuts.search_navigate",
        "Up / Down",
        category_key="shortcuts.category.search_palette",
        toggleable=False,
    ),
)

TOGGLEABLE_SHORTCUT_IDS: frozenset[str] = frozenset(
    spec.id for spec in APP_SHORTCUTS if spec.toggleable
)
