"""Helpers for temporary import sessions (traffic + TLD)."""
from __future__ import annotations

from pathlib import Path

from app.services.excel_session import ExcelSessionCache
from app.services.file_history import FileHistoryStore


def prune_other_sessions(*, path: str | Path, keep_session_id: str, file_kind: str) -> None:
    """Drop older cache/history rows for the same source file path."""
    resolved = str(Path(path).resolve())
    store = FileHistoryStore.instance()
    cache = ExcelSessionCache.instance()
    for entry in list(store.entries):
        if entry.file_kind != file_kind:
            continue
        if str(Path(entry.path).resolve()) != resolved:
            continue
        if entry.session_id == keep_session_id:
            continue
        cache.delete(entry.session_id)
        store.remove(entry.session_id)


def session_id_matches_file(path: str | Path, session_id: str, *, tld: bool = False) -> bool:
    """Return True when session_id still matches the file on disk."""
    resolved = Path(path)
    if not resolved.is_file():
        return False
    from app.services.excel_io import ExcelIOService
    from app.services.tld_io import TldIOService

    current_id = (
        TldIOService.make_session_id(resolved)
        if tld
        else ExcelIOService.make_session_id(resolved)
    )
    return current_id == session_id
