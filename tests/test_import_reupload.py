"""Verify temporary import cache supports remove and re-upload cycles."""
from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from app.services.excel_session import ExcelSessionCache
from app.services.file_history import FileHistoryStore
from app.services.import_session_utils import prune_other_sessions
from app.services.tld_io import TldIOService


def _write_min_tld_workbook(path: Path, *, load_value: float = 10.0) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet["A3"] = "Axle group load (kN)"
    sheet["B4"] = "SAST"
    sheet["C4"] = "SADT"
    sheet["D4"] = "TAST"
    sheet["E4"] = "TADT"
    sheet["F4"] = "TRDT"
    sheet["B5"] = "%"
    sheet["A6"] = load_value
    sheet["B6"] = 0.2804
    workbook.save(path)
    workbook.close()


class ImportReuploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self._history = FileHistoryStore.instance()
        self._cache = ExcelSessionCache.instance()
        self._tld_io = TldIOService.instance()
        self._history.clear()
        self._cache.clear()

    def tearDown(self) -> None:
        self._history.clear()
        self._cache.clear()

    def test_tld_remove_and_reupload_same_file(self) -> None:
        try:
            from openpyxl import Workbook  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl not available")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as handle:
            temp_path = Path(handle.name)
        try:
            _write_min_tld_workbook(temp_path, load_value=10.0)
            first = self._tld_io.import_tld_workbook(temp_path)
            first_data = self._tld_io.load_session(first.session_id)
            self.assertIsNotNone(first_data)
            self.assertEqual(first_data["distribution_rows"][0]["load_kn"], 10.0)

            self._tld_io.remove_from_history(first.session_id)
            self.assertEqual(self._history.entries, [])
            self.assertIsNone(self._tld_io.load_session(first.session_id))

            second = self._tld_io.import_tld_workbook(temp_path)
            second_data = self._tld_io.load_session(second.session_id)
            self.assertIsNotNone(second_data)
            self.assertEqual(len(self._history.entries), 1)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_tld_reupload_updates_cache_without_restart(self) -> None:
        try:
            from openpyxl import Workbook  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl not available")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as handle:
            temp_path = Path(handle.name)
        try:
            _write_min_tld_workbook(temp_path, load_value=10.0)
            first = self._tld_io.import_tld_workbook(temp_path)
            _write_min_tld_workbook(temp_path, load_value=20.0)
            time.sleep(0.05)

            refreshed = self._tld_io.import_tld_workbook(temp_path)
            data = self._tld_io.load_session(refreshed.session_id)
            self.assertIsNotNone(data)
            self.assertEqual(data["distribution_rows"][0]["load_kn"], 20.0)
            self.assertEqual(len(self._history.entries), 1)
            self.assertNotEqual(first.session_id, refreshed.session_id)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_tld_recent_apply_refreshes_when_file_changed_on_disk(self) -> None:
        try:
            from openpyxl import Workbook  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl not available")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as handle:
            temp_path = Path(handle.name)
        try:
            _write_min_tld_workbook(temp_path, load_value=10.0)
            first = self._tld_io.import_tld_workbook(temp_path)
            old_session = first.session_id

            _write_min_tld_workbook(temp_path, load_value=30.0)
            time.sleep(0.05)

            data = self._tld_io.load_session(old_session)
            self.assertIsNotNone(data)
            self.assertEqual(data["distribution_rows"][0]["load_kn"], 30.0)
            self.assertNotEqual(data.get("session_id"), old_session)
            self.assertEqual(len(self._history.entries), 1)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_prune_other_sessions_keeps_only_latest_path_entry(self) -> None:
        from app.services.file_history import FileHistoryEntry

        self._history.add(
            FileHistoryEntry(
                session_id="old",
                path="C:/data/sample.xlsx",
                file_name="sample.xlsx",
                imported_at="",
                size_bytes=1,
                count_hour="",
                file_kind="tld",
            )
        )
        self._history.add(
            FileHistoryEntry(
                session_id="new",
                path="C:/data/sample.xlsx",
                file_name="sample.xlsx",
                imported_at="",
                size_bytes=2,
                count_hour="",
                file_kind="tld",
            )
        )
        self._cache.put("old", {"session_id": "old"})
        self._cache.put("new", {"session_id": "new"})
        prune_other_sessions(path="C:/data/sample.xlsx", keep_session_id="new", file_kind="tld")
        self.assertEqual(len(self._history.entries), 1)
        self.assertEqual(self._history.entries[0].session_id, "new")
        self.assertIsNone(self._cache.get("old"))
        self.assertIsNotNone(self._cache.get("new"))


if __name__ == "__main__":
    unittest.main()
