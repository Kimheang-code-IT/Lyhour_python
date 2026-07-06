"""Local Excel import history (metadata only, no workbook data)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from cachetools import LRUCache
from loguru import logger

_MAX_ENTRIES = 20
_HISTORY_FILE = "excel_file_history.json"


@dataclass
class FileHistoryEntry:
    session_id: str
    path: str
    file_name: str
    imported_at: str
    size_bytes: int
    count_hour: str = "12h"
    file_kind: str = "traffic"

    @classmethod
    def from_dict(cls, raw: dict) -> FileHistoryEntry:
        return cls(
            session_id=str(raw.get("session_id", "")),
            path=str(raw.get("path", "")),
            file_name=str(raw.get("file_name", "")),
            imported_at=str(raw.get("imported_at", "")),
            size_bytes=int(raw.get("size_bytes", 0)),
            count_hour=str(raw.get("count_hour", "12h")),
            file_kind=str(raw.get("file_kind", "traffic")),
        )

    @property
    def is_tld(self) -> bool:
        return self.file_kind == "tld"


def format_recent_import_label(entry: FileHistoryEntry) -> str:
    from app.core.i18n import tr

    if entry.is_tld:
        return f"{entry.file_name} ({tr('file.recent.tld')})"
    return f"{entry.file_name} ({tr('file.recent.traffic')})"


def _history_path() -> Path:
    base = Path.home() / ".kiec_engineering"
    base.mkdir(parents=True, exist_ok=True)
    return base / _HISTORY_FILE


class FileHistoryStore:
    """Recent Excel imports on this machine (paths + timestamps only)."""

    _instance: FileHistoryStore | None = None

    def __init__(self) -> None:
        self._entries: list[FileHistoryEntry] = []
        self._lookup: LRUCache[str, FileHistoryEntry] = LRUCache(maxsize=_MAX_ENTRIES)
        self.load()

    @classmethod
    def instance(cls) -> FileHistoryStore:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def entries(self) -> list[FileHistoryEntry]:
        return list(self._entries)

    def load(self) -> list[FileHistoryEntry]:
        path = _history_path()
        if not path.is_file():
            self._entries = []
            self._lookup.clear()
            return self._entries
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            items = raw if isinstance(raw, list) else []
            self._entries = [FileHistoryEntry.from_dict(item) for item in items[:_MAX_ENTRIES]]
        except Exception as exc:
            logger.warning("Could not load file history: {}", exc)
            self._entries = []
        self._lookup.clear()
        for entry in self._entries:
            self._lookup[entry.session_id] = entry
        return self._entries

    def save(self) -> None:
        path = _history_path()
        payload = [asdict(entry) for entry in self._entries[:_MAX_ENTRIES]]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add(self, entry: FileHistoryEntry) -> None:
        self._entries = [e for e in self._entries if e.session_id != entry.session_id]
        self._entries.insert(0, entry)
        self._entries = self._entries[:_MAX_ENTRIES]
        self._lookup[entry.session_id] = entry
        self.save()

    def get(self, session_id: str) -> FileHistoryEntry | None:
        cached = self._lookup.get(session_id)
        if cached is not None:
            return cached
        for entry in self._entries:
            if entry.session_id == session_id:
                self._lookup[session_id] = entry
                return entry
        return None

    def remove(self, session_id: str) -> None:
        self._entries = [e for e in self._entries if e.session_id != session_id]
        self._lookup.pop(session_id, None)
        self.save()

    def clear(self) -> None:
        self._entries = []
        self._lookup.clear()
        self.save()
