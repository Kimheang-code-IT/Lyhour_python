"""Topbar toolbar button definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopbarButton:
    id: str
    label_key: str
    menu: str | None = None
    shortcut: str | None = None


TOPBAR_BUTTONS: tuple[TopbarButton, ...] = (
    TopbarButton("file", "menu.file", menu="file"),
    TopbarButton("edit", "menu.edit", menu="edit"),
    TopbarButton("view", "menu.view", menu="view"),
    TopbarButton("settings", "menu.settings", menu="settings", shortcut="Ctrl+,"),
    TopbarButton("help", "menu.help", menu="help", shortcut="F1"),
)
