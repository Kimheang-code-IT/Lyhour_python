"""Persistent application preferences (theme, language, font, workspace)."""
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field

from app.config.shortcuts import TOGGLEABLE_SHORTCUT_IDS
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import QObject, pyqtSignal

from app.config.settings import APP_NAME


@dataclass
class AppSettingsData:
    theme: str = "dark"  # dark | light
    font_scale: float = 1.0  # 0.9 | 1.0 | 1.15 | 1.3
    language: str = "en"  # en | km
    sidebar_visible: bool = True
    preview_visible: bool = True
    show_tooltips: bool = True
    confirm_exit: bool = False
    remember_panel_layout: bool = True
    compact_mode: bool = False
    accent_color: str = "#0078D4"
    default_growth_rate: float = 7.0
    auto_refresh_results: bool = True
    show_shortcut_hints: bool = True
    disabled_shortcuts: list[str] = field(default_factory=list)

    def normalized(self) -> AppSettingsData:
        theme = self.theme if self.theme in ("dark", "light") else "dark"
        language = self.language if self.language in ("en", "km") else "en"
        font_scale = self.font_scale
        if font_scale not in (0.9, 1.0, 1.15, 1.3):
            font_scale = min(1.3, max(0.9, round(font_scale, 2)))
        return AppSettingsData(
            theme=theme,
            font_scale=font_scale,
            language=language,
            sidebar_visible=bool(self.sidebar_visible),
            preview_visible=bool(self.preview_visible),
            show_tooltips=bool(self.show_tooltips),
            confirm_exit=bool(self.confirm_exit),
            remember_panel_layout=bool(self.remember_panel_layout),
            compact_mode=bool(self.compact_mode),
            accent_color=self.accent_color or "#0078D4",
            default_growth_rate=float(self.default_growth_rate),
            auto_refresh_results=bool(self.auto_refresh_results),
            show_shortcut_hints=bool(self.show_shortcut_hints),
            disabled_shortcuts=[
                sid for sid in self.disabled_shortcuts if sid in TOGGLEABLE_SHORTCUT_IDS
            ],
        )


FONT_SCALE_OPTIONS: tuple[tuple[str, float], ...] = (
    ("settings.font.small", 0.9),
    ("settings.font.medium", 1.0),
    ("settings.font.large", 1.15),
    ("settings.font.xlarge", 1.3),
)


def _settings_path() -> Path:
    base = Path.home() / ".kiec_engineering"
    base.mkdir(parents=True, exist_ok=True)
    safe_name = APP_NAME.replace(" ", "_").lower()
    return base / f"{safe_name}_settings.json"


class AppSettings(QObject):
    """Load/save user preferences and notify listeners when they change."""

    changed = pyqtSignal(object)

    _instance: AppSettings | None = None

    def __init__(self) -> None:
        super().__init__()
        self._data = AppSettingsData().normalized()
        self.load()

    @classmethod
    def instance(cls) -> AppSettings:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def current(cls) -> AppSettingsData:
        return cls.instance().data

    @property
    def data(self) -> AppSettingsData:
        return deepcopy(self._data)

    def load(self) -> AppSettingsData:
        path = _settings_path()
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                merged = {**asdict(AppSettingsData()), **raw}
                self._data = AppSettingsData(**merged).normalized()
            except Exception:
                self._data = AppSettingsData().normalized()
        else:
            self._data = AppSettingsData().normalized()
        return self._data

    def save(self, data: AppSettingsData | None = None) -> AppSettingsData:
        if data is not None:
            self._data = data.normalized()
        path = _settings_path()
        path.write_text(json.dumps(asdict(self._data), indent=2), encoding="utf-8")
        self.changed.emit(self.data)
        return self._data

    def update(self, **kwargs: Any) -> AppSettingsData:
        payload = asdict(self._data)
        payload.update(kwargs)
        return self.save(AppSettingsData(**payload))
