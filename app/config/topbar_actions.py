"""Topbar toolbar button definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopbarButton:
    id: str
    label_key: str
    action: str | None = None
    shortcut: str | None = None


# Menu-style placeholders (future: dropdown menus)
MENU_BUTTONS: tuple[TopbarButton, ...] = (
    TopbarButton("file", "menu.file"),
    TopbarButton("edit", "menu.edit"),
    TopbarButton("view", "menu.view"),
)

# Buttons that open dialogs or run actions immediately
ACTION_BUTTONS: tuple[TopbarButton, ...] = (
    TopbarButton("settings", "menu.settings", action="settings", shortcut="Ctrl+,"),
    TopbarButton("help", "menu.help", action="help", shortcut="F1"),
)

TOPBAR_BUTTONS: tuple[TopbarButton, ...] = MENU_BUTTONS + ACTION_BUTTONS
