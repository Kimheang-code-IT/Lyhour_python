"""Import Austroads TLD workbooks into temp cache and recent-import history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.services.excel_io import ExcelIOService
from app.services.excel_session import ExcelSessionCache
from app.services.file_history import FileHistoryEntry, FileHistoryStore
from app.services.import_session_utils import prune_other_sessions, session_id_matches_file
from app.services.traffic_tld_excel import read_tld_workbook

_TLD_SESSION_PREFIX = "tld_"


@dataclass(frozen=True)
class TldImportResult:
    session_id: str
    path: str
    file_name: str
    row_count: int


class TldIOService:
    """Cache parsed TLD workbooks and track them in recent imports."""

    _instance: TldIOService | None = None

    @classmethod
    def instance(cls) -> TldIOService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def is_tld_session(session_id: str) -> bool:
        return str(session_id).startswith(_TLD_SESSION_PREFIX)

    @staticmethod
    def make_session_id(path: Path) -> str:
        return f"{_TLD_SESSION_PREFIX}{ExcelIOService.make_session_id(path)}"

    def import_tld_workbook(self, path: str | Path) -> TldImportResult:
        resolved = Path(path).resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"TLD file not found: {resolved}")

        data = read_tld_workbook(resolved)
        session_id = self.make_session_id(resolved)
        data["session_id"] = session_id
        data["source_path"] = str(resolved)

        ExcelSessionCache.instance().put(session_id, data)

        stat = resolved.stat()
        entry = FileHistoryEntry(
            session_id=session_id,
            path=str(resolved),
            file_name=resolved.name,
            imported_at=datetime.now(timezone.utc).isoformat(),
            size_bytes=stat.st_size,
            count_hour="",
            file_kind="tld",
        )
        FileHistoryStore.instance().add(entry)
        prune_other_sessions(path=str(resolved), keep_session_id=session_id, file_kind="tld")

        rows = data.get("distribution_rows") or []
        logger.info("Imported TLD {} ({} rows, session {})", resolved.name, len(rows), session_id)
        return TldImportResult(
            session_id=session_id,
            path=str(resolved),
            file_name=resolved.name,
            row_count=len(rows),
        )

    def load_session(self, session_id: str) -> dict | None:
        entry = FileHistoryStore.instance().get(session_id)
        if entry is not None and entry.file_kind == "tld" and Path(entry.path).is_file():
            if not session_id_matches_file(entry.path, session_id, tld=True):
                self.remove_from_history(session_id)
                result = self.import_tld_workbook(entry.path)
                return ExcelSessionCache.instance().get(result.session_id)

        cached = ExcelSessionCache.instance().get(session_id)
        if cached is not None:
            return cached

        if entry is None or entry.file_kind != "tld" or not Path(entry.path).is_file():
            return None

        result = self.import_tld_workbook(entry.path)
        return ExcelSessionCache.instance().get(result.session_id)

    def close_session(self, session_id: str) -> None:
        ExcelSessionCache.instance().delete(session_id)

    def remove_from_history(self, session_id: str) -> None:
        ExcelSessionCache.instance().delete(session_id)
        FileHistoryStore.instance().remove(session_id)
