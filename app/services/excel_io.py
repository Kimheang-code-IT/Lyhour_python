"""Excel import/export helpers (pandas/openpyxl/xlsxwriter, temporary cache)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from loguru import logger

from app.services.excel_session import ExcelSessionCache
from app.services.file_history import FileHistoryEntry, FileHistoryStore
from app.services.import_session_utils import prune_other_sessions, session_id_matches_file
from app.services.traffic_excel import read_traffic_investigation_workbook

_EXCEL_FILTER = "Excel (*.xlsx);;All Files (*)"


@dataclass(frozen=True)
class ExcelImportResult:
    session_id: str
    path: str
    file_name: str
    count_hour: str
    row_count: int
    survey_hours: int


class ExcelIOService:
    """Import traffic workbooks into temp cache; export summaries to Excel."""

    _instance: ExcelIOService | None = None

    @classmethod
    def instance(cls) -> ExcelIOService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def excel_filter() -> str:
        return _EXCEL_FILTER

    @staticmethod
    def make_session_id(path: Path) -> str:
        stat = path.stat()
        digest = hashlib.sha256(
            f"{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8")
        ).hexdigest()
        return digest[:16]

    def _validate_workbook(self, path: Path) -> None:
        if path.suffix.lower() != ".xlsx":
            raise ValueError("Only .xlsx traffic investigation files are supported.")
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        with pd.ExcelFile(path, engine="openpyxl") as workbook:
            names = {name.strip().upper() for name in workbook.sheet_names}
        if not names.intersection({"D1", "D2"}):
            raise ValueError("Workbook must contain sheets D1 and/or D2.")

    def import_traffic_workbook(
        self,
        path: str | Path,
        *,
        count_hour: str = "12h",
    ) -> ExcelImportResult:
        resolved = Path(path).resolve()
        self._validate_workbook(resolved)
        data = read_traffic_investigation_workbook(resolved, count_hour=count_hour)
        session_id = self.make_session_id(resolved)
        data["session_id"] = session_id
        data["source_path"] = str(resolved)

        cache = ExcelSessionCache.instance()
        cache.put(session_id, data)

        stat = resolved.stat()
        entry = FileHistoryEntry(
            session_id=session_id,
            path=str(resolved),
            file_name=resolved.name,
            imported_at=datetime.now(timezone.utc).isoformat(),
            size_bytes=stat.st_size,
            count_hour=count_hour,
            file_kind="traffic",
        )
        FileHistoryStore.instance().add(entry)
        prune_other_sessions(path=str(resolved), keep_session_id=session_id, file_kind="traffic")

        rows = data.get("traffic_count_rows") or []
        logger.info("Imported Excel {} ({} rows, session {})", resolved.name, len(rows), session_id)
        return ExcelImportResult(
            session_id=session_id,
            path=str(resolved),
            file_name=resolved.name,
            count_hour=count_hour,
            row_count=len(rows),
            survey_hours=int(data.get("survey_hours") or 12),
        )

    def load_session(self, session_id: str) -> dict | None:
        entry = FileHistoryStore.instance().get(session_id)
        if entry is not None and entry.file_kind == "traffic" and Path(entry.path).is_file():
            if not session_id_matches_file(entry.path, session_id, tld=False):
                self.remove_from_history(session_id)
                result = self.import_traffic_workbook(entry.path, count_hour=entry.count_hour)
                return ExcelSessionCache.instance().get(result.session_id)

        cached = ExcelSessionCache.instance().get(session_id)
        if cached is not None:
            return cached

        if entry is None or not Path(entry.path).is_file():
            return None
        result = self.import_traffic_workbook(entry.path, count_hour=entry.count_hour)
        if result.session_id != session_id:
            logger.warning("Session id changed on reload: {} -> {}", session_id, result.session_id)
        return ExcelSessionCache.instance().get(result.session_id)

    def close_session(self, session_id: str) -> None:
        """Remove temporary cached payload only (keep history metadata)."""
        ExcelSessionCache.instance().delete(session_id)

    def remove_from_history(self, session_id: str) -> None:
        ExcelSessionCache.instance().delete(session_id)
        FileHistoryStore.instance().remove(session_id)

    def export_traffic_summary(
        self,
        path: str | Path,
        *,
        traffic_count_rows: list[list],
        summary_total_row: list | None,
    ) -> Path:
        """Export chart/table summary to .xlsx (not a full workbook copy)."""
        import xlsxwriter

        out = Path(path)
        if out.suffix.lower() != ".xlsx":
            out = out.with_suffix(".xlsx")

        workbook = xlsxwriter.Workbook(str(out))
        sheet = workbook.add_worksheet("Summary")

        header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9E1F2", "border": 1})
        cell_fmt = workbook.add_format({"border": 1})

        if summary_total_row:
            for col, value in enumerate(summary_total_row):
                sheet.write(0, col, value, header_fmt if col == 0 else cell_fmt)
            start_row = 2
        else:
            start_row = 0

        for row_index, row in enumerate(traffic_count_rows, start=start_row):
            for col_index, value in enumerate(row):
                sheet.write(row_index, col_index, value, cell_fmt)

        sheet.set_column(0, 0, 14)
        sheet.set_column(1, 22, 10)
        workbook.close()
        logger.info("Exported traffic summary to {}", out)
        return out
