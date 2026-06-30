"""Read traffic investigation workbooks (sheets D1 and D2)."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

_NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
_OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_TARGET_SHEETS = ("D1", "D2")
_DATA_START_ROW = 8
_DAILY_TOTAL_ROW = 69
_MOTOR_COL = 3  # Excel column C
VEHICLE_TYPE_COUNT = 18  # Excel columns C through T
_TOTAL_COL = 21  # Excel column U
_TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})\s*$")

TRAFFIC_COUNT_HOUR_MULTIPLIERS = {
    "12h": 1.0,
    "24h": 1.2,
}


def traffic_count_hour_multiplier(count_hour: str) -> float:
    """Return power factor for Traffic Count Hour selection."""
    return TRAFFIC_COUNT_HOUR_MULTIPLIERS.get(str(count_hour).strip(), 1.0)


def build_summary_total_row(
    daily_totals: dict[str, list[int]],
    *,
    count_hour: str = "12h",
) -> list:
    """Sum D1 and D2 daily totals (row 69) and apply Traffic Count Hour power."""
    power = traffic_count_hour_multiplier(count_hour)
    summed = [0] * VEHICLE_TYPE_COUNT
    sheet_total = 0
    for sheet_name in _TARGET_SHEETS:
        values = daily_totals.get(sheet_name) or []
        for index in range(VEHICLE_TYPE_COUNT):
            if index < len(values):
                summed[index] += int(values[index])
        if len(values) > VEHICLE_TYPE_COUNT:
            sheet_total += int(values[VEHICLE_TYPE_COUNT])

    adjusted = [int(round(value * power)) for value in summed]
    grand_total = int(round(sheet_total * power)) if sheet_total else sum(adjusted)
    return ["Total", *adjusted, grand_total]


def read_traffic_investigation_workbook(path: str | Path, *, count_hour: str = "12h") -> dict:
    """
    Read hourly traffic rows from sheets D1 and D2.

    Returns temporary session data:
    {
        "source_path": "...",
        "sheets": {"D1": [...], "D2": [...]},
        "daily_totals": {"D1": [...], "D2": [...]},
        "summary_total_row": ["Total", ...],
        "traffic_count_rows": [...],  # hourly rows for chart
        "traffic_count_hour": "12h",
    }
    """
    path = Path(path)
    if path.suffix.lower() != ".xlsx":
        raise ValueError("Only .xlsx traffic investigation files are supported.")

    with zipfile.ZipFile(path) as archive:
        shared_strings = _read_shared_strings(archive)
        sheet_paths = _sheet_paths_by_name(archive)

    sheets_data: dict[str, list[list]] = {}
    daily_totals: dict[str, list[int]] = {}
    missing: list[str] = []
    for sheet_name in _TARGET_SHEETS:
        sheet_path = sheet_paths.get(sheet_name)
        if not sheet_path:
            missing.append(sheet_name)
            continue
        with zipfile.ZipFile(path) as archive:
            grid = _read_sheet_grid(archive, sheet_path, shared_strings)
        sheets_data[sheet_name] = _extract_hourly_rows(grid)
        daily_totals[sheet_name] = _extract_daily_total_row(grid)

    if not sheets_data and not daily_totals:
        missing_text = ", ".join(missing) if missing else "D1, D2"
        raise ValueError(f"Could not find sheet(s): {missing_text}")

    combined = _combine_hourly_rows(
        sheets_data.get("D1", []),
        sheets_data.get("D2", []),
    )
    summary_total_row = build_summary_total_row(daily_totals, count_hour=count_hour)
    if not combined and not any(daily_totals.values()):
        raise ValueError(
            "No traffic data was found in sheets D1 and D2 (hourly rows or daily total row 69)."
        )

    return {
        "source_path": str(path),
        "sheets": sheets_data,
        "daily_totals": daily_totals,
        "summary_total_row": summary_total_row,
        "traffic_count_rows": combined,
        "traffic_count_hour": count_hour,
        "missing_sheets": missing,
    }


def read_traffic_count_rows(path: str | Path) -> list[list]:
    """Backward-compatible helper returning combined hourly rows."""
    return read_traffic_investigation_workbook(path)["traffic_count_rows"]


def _extract_daily_total_row(grid: dict[tuple[int, int], str]) -> list[int]:
    """Read Daily Total row (C69:T69 + U69)."""
    row_index = _find_daily_total_row(grid)
    values: list[int] = []
    for offset in range(VEHICLE_TYPE_COUNT):
        column_index = _MOTOR_COL + offset
        text = _cell_text(grid, row_index, column_index).strip()
        values.append(_to_int(text) if _is_number(text) else 0)

    total_text = _cell_text(grid, row_index, _TOTAL_COL).strip()
    values.append(_to_int(total_text) if _is_number(total_text) else 0)
    return values


def _find_daily_total_row(grid: dict[tuple[int, int], str]) -> int:
    max_row = max((row for row, _column in grid), default=0)
    for row_index in range(_DAILY_TOTAL_ROW - 5, max_row + 1):
        label = _cell_text(grid, row_index, 1).strip().lower()
        if label == "daily total":
            return row_index
    return _DAILY_TOTAL_ROW


def _extract_hourly_rows(grid: dict[tuple[int, int], str]) -> list[list]:
    """Read hourly totals from investigation sheet starting at row 8."""
    hourly_rows: list[list] = []
    current_block: str | None = None
    max_row = max((row for row, _column in grid), default=0)

    for row_index in range(_DATA_START_ROW, max_row + 1):
        time_label = _time_label_at_row(grid, row_index)
        if time_label:
            current_block = _hour_block_from_interval(time_label)

        first_cell = _cell_text(grid, row_index, 1).strip().lower()
        second_cell = _cell_text(grid, row_index, 2).strip().lower()
        is_total_row = first_cell == "total" or second_cell == "total"

        direct_hour = _direct_hour_label(time_label) if time_label else None
        if direct_hour:
            counts = _read_vehicle_counts(grid, row_index)
            if counts and any(counts):
                hourly_rows.append([direct_hour, *counts])
            current_block = direct_hour
            continue

        if is_total_row and current_block:
            counts = _read_vehicle_counts(grid, row_index)
            if counts and any(counts):
                hourly_rows.append([current_block, *counts])
            current_block = None

    return _dedupe_hourly_rows(hourly_rows)


def _read_vehicle_counts(grid: dict[tuple[int, int], str], row_index: int) -> list[int]:
    values: list[int] = []
    for offset in range(VEHICLE_TYPE_COUNT):
        column_index = _MOTOR_COL + offset
        text = _cell_text(grid, row_index, column_index).strip()
        values.append(_to_int(text) if _is_number(text) else 0)

    total_text = _cell_text(grid, row_index, _TOTAL_COL).strip()
    values.append(_to_int(total_text) if _is_number(total_text) else 0)
    return values


def _time_label_at_row(grid: dict[tuple[int, int], str], row_index: int) -> str:
    for column_index in (1, 2):
        text = _cell_text(grid, row_index, column_index).strip()
        if _TIME_RE.match(text):
            return text
    return ""


def _direct_hour_label(time_label: str) -> str | None:
    match = _TIME_RE.match(time_label.strip())
    if not match:
        return None
    start_h, start_m, end_h, end_m = map(int, match.groups())
    if end_h == start_h + 1 and end_m == start_m:
        return f"{start_h}:{start_m:02d}-{end_h}:{end_m:02d}"
    return None


def _hour_block_from_interval(time_label: str) -> str:
    match = _TIME_RE.match(time_label.strip())
    if not match:
        return time_label.strip()
    start_h = int(match.group(1))
    end_h = start_h + 1
    return f"{start_h}:00-{end_h}:00"


def _dedupe_hourly_rows(rows: list[list]) -> list[list]:
    by_time: dict[str, list] = {}
    for row in rows:
        by_time[row[0]] = row
    return [by_time[label] for label in sorted(by_time, key=_time_sort_key)]


def _combine_hourly_rows(d1_rows: list[list], d2_rows: list[list]) -> list[list]:
    if not d1_rows:
        return list(d2_rows)
    if not d2_rows:
        return list(d1_rows)

    by_time: dict[str, list] = {}
    for row in d1_rows + d2_rows:
        label = row[0]
        if label not in by_time:
            by_time[label] = [label, *row[1:]]
            continue
        combined = by_time[label]
        for index in range(1, len(row)):
            combined[index] += row[index]
    return [by_time[label] for label in sorted(by_time, key=_time_sort_key)]


def _time_sort_key(label: str) -> tuple[int, int]:
    match = _TIME_RE.match(label)
    if not match:
        return (99, 99)
    return int(match.group(1)), int(match.group(2))


def _sheet_paths_by_name(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("rel:Relationship", _REL_NS)
    }

    paths: dict[str, str] = {}
    for sheet in workbook.findall(".//main:sheet", _NS):
        name = sheet.attrib.get("name", "")
        rel_id = sheet.attrib.get(f"{{{_OFFICE_REL_NS}}}id")
        if not rel_id or rel_id not in rel_map:
            continue
        target = rel_map[rel_id].replace("\\", "/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        paths[name] = target
    return paths


def _read_sheet_grid(
    archive: zipfile.ZipFile,
    sheet_path: str,
    shared_strings: list[str],
) -> dict[tuple[int, int], str]:
    root = ET.fromstring(archive.read(sheet_path))
    grid: dict[tuple[int, int], str] = {}
    for row in root.findall(".//main:sheetData/main:row", _NS):
        row_index = int(row.attrib.get("r", "0") or 0)
        for cell in row.findall("main:c", _NS):
            column_index = _column_index(cell.attrib.get("r", ""))
            grid[(row_index, column_index)] = _cell_value(cell, shared_strings)
    return grid


def _cell_text(grid: dict[tuple[int, int], str], row_index: int, column_index: int) -> str:
    return str(grid.get((row_index, column_index), ""))


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        xml = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    root = ET.fromstring(xml)
    values: list[str] = []
    for item in root.findall("main:si", _NS):
        text_parts = [node.text or "" for node in item.findall(".//main:t", _NS)]
        values.append("".join(text_parts))
    return values


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value_node = cell.find("main:v", _NS)
    if cell_type == "inlineStr":
        text_parts = [node.text or "" for node in cell.findall(".//main:t", _NS)]
        return "".join(text_parts)
    if value_node is None or value_node.text is None:
        return ""
    value = value_node.text
    if cell_type == "s":
        index = int(value)
        return shared_strings[index] if 0 <= index < len(shared_strings) else ""
    return value


def _column_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha()).upper()
    index = 0
    for ch in letters:
        index = index * 26 + ord(ch) - ord("A") + 1
    return index or 1


def _is_number(value: object) -> bool:
    try:
        float(str(value).strip())
    except ValueError:
        return False
    return True


def _to_int(value: object) -> int:
    return int(round(float(str(value).strip())))
