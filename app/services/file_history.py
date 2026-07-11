"""Session-only Excel import history (metadata only, no workbook data)."""
from __future__ import annotations

from dataclasses import dataclass

from cachetools import LRUCache

_MAX_ENTRIES = 20


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


class FileHistoryStore:
    """Recent Excel imports for the current application session only."""

    _instance: FileHistoryStore | None = None

    def __init__(self) -> None:
        self._entries: list[FileHistoryEntry] = []
        self._lookup: LRUCache[str, FileHistoryEntry] = LRUCache(maxsize=_MAX_ENTRIES)

    @classmethod
    def instance(cls) -> FileHistoryStore:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def entries(self) -> list[FileHistoryEntry]:
        return list(self._entries)

    def load(self) -> list[FileHistoryEntry]:
        return self._entries

    def save(self) -> None:
        return None

    def add(self, entry: FileHistoryEntry) -> None:
        self._entries = [e for e in self._entries if e.session_id != entry.session_id]
        self._entries.insert(0, entry)
        self._entries = self._entries[:_MAX_ENTRIES]
        self._lookup[entry.session_id] = entry

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

    def clear(self) -> None:
        self._entries = []
        self._lookup.clear()
