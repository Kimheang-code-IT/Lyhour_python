"""Tests for TLD import history integration."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.services.file_history import FileHistoryStore, format_recent_import_label
from app.services.tld_io import TldIOService


class TldImportHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._history = FileHistoryStore.instance()
        self._history.clear()
        self._tld_io = TldIOService.instance()

    def tearDown(self) -> None:
        self._history.clear()

    def test_import_tld_adds_recent_history_entry(self) -> None:
        try:
            from openpyxl import Workbook
        except ImportError:
            self.skipTest("openpyxl not available")

        workbook = Workbook()
        sheet = workbook.active
        sheet["A3"] = "Axle group load (kN)"
        sheet["B4"] = "SAST"
        sheet["C4"] = "SADT"
        sheet["D4"] = "TAST"
        sheet["E4"] = "TADT"
        sheet["F4"] = "TRDT"
        sheet["B5"] = "%"
        sheet["A6"] = 10
        sheet["B6"] = 0.2804

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as handle:
            temp_path = handle.name
        try:
            workbook.save(temp_path)
            workbook.close()
            result = self._tld_io.import_tld_workbook(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

        entries = self._history.entries
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].session_id, result.session_id)
        self.assertTrue(entries[0].is_tld)
        self.assertIn("TLD", format_recent_import_label(entries[0]))

    def test_remove_tld_clears_history_and_cache(self) -> None:
        try:
            from openpyxl import Workbook
        except ImportError:
            self.skipTest("openpyxl not available")

        workbook = Workbook()
        sheet = workbook.active
        sheet["A3"] = "Axle group load (kN)"
        sheet["B4"] = "SAST"
        sheet["B5"] = "%"
        sheet["A6"] = 10
        sheet["B6"] = 1.0

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as handle:
            temp_path = handle.name
        try:
            workbook.save(temp_path)
            workbook.close()
            result = self._tld_io.import_tld_workbook(temp_path)
            self.assertIsNotNone(self._tld_io.load_session(result.session_id))
            self._tld_io.remove_from_history(result.session_id)
            self.assertEqual(self._history.entries, [])
            self.assertIsNone(self._tld_io.load_session(result.session_id))
        finally:
            Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
