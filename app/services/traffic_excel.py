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
_DATA_END_ROW = 127
_DAILY_TOTAL_ROW = 69
_MOTOR_COL = 3  # Excel column C
_END_VEHICLE_COL = 20  # Excel column T
VEHICLE_TYPE_COUNT = 18  # Excel columns C through T
_TOTAL_COL = 21  # Excel column U
_TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})\s*$")

TRAFFIC_COUNT_HOUR_MULTIPLIERS = {
    "12h": 1.0,
    "24h": 1.2,
}

# Vehicle groups for summary pie chart (Excel columns C–T indices).
VEHICLE_GROUP_YELLOW = (0, 1, 2)  # Class 1A–1C
VEHICLE_GROUP_ORANGE = (3, 4, 5, 6, 7, 8)  # Class 1E–1J
VEHICLE_GROUP_GREEN = tuple(range(9, VEHICLE_TYPE_COUNT))  # Heavy vehicles

VEHICLE_GROUP_DEFINITIONS: tuple[tuple[str, tuple[int, ...], str], ...] = (
    ("Class 1A–1C", VEHICLE_GROUP_YELLOW, "#f1c40f"),
    ("Class 1E–1J", VEHICLE_GROUP_ORANGE, "#e67e22"),
    ("Heavy Vehicles", VEHICLE_GROUP_GREEN, "#2ecc71"),
)


def sum_d1_d2_vehicle_group_totals(
    daily_totals: dict[str, list[int]] | None,
) -> list[tuple[str, int, str]]:
    """Sum D1 + D2 counts into three vehicle groups for the summary pie chart."""
    if not daily_totals:
        return [(label, 0, color) for label, _indices, color in VEHICLE_GROUP_DEFINITIONS]

    per_type = [0] * VEHICLE_TYPE_COUNT
    for sheet_name in _TARGET_SHEETS:
        values = daily_totals.get(sheet_name) or []
        for index in range(VEHICLE_TYPE_COUNT):
            if index < len(values):
                per_type[index] += int(values[index])

    groups: list[tuple[str, int, str]] = []
    for label, indices, color in VEHICLE_GROUP_DEFINITIONS:
        total = sum(per_type[index] for index in indices)
        groups.append((label, total, color))
    return groups


def traffic_count_hour_multiplier(
    count_hour: str,
    *,
    survey_hours: int = 12,
) -> float:
    """
    Return AADT power factor for the selected count period.

    - 12h selection always uses power 1.0.
    - 24h selection uses 1.2 only when the Excel survey is 12h (extrapolation).
    - 24h selection on a 24h Excel survey uses 1.0 (data already covers 24h).
    """
    if str(count_hour).strip() != "24h":
        return 1.0
    if survey_hours >= 24:
        return 1.0
    return TRAFFIC_COUNT_HOUR_MULTIPLIERS["24h"]


def select_daily_totals(
    daily_totals_12h: dict[str, list[int]],
    daily_totals_24h: dict[str, list[int]],
    *,
    survey_hours: int,
    count_hour: str,
) -> dict[str, list[int]]:
    """Pick 12h or 24h sheet totals based on Excel survey length and UI selection."""
    if str(count_hour).strip() == "24h" and survey_hours >= 24:
        return daily_totals_24h
    return daily_totals_12h


def average_vehicle_totals(
    *,
    daily_totals_12h: dict[str, list[int]] | None = None,
    daily_totals_24h: dict[str, list[int]] | None = None,
    daily_totals: dict[str, list[int]] | None = None,
    survey_hours: int = 12,
    count_hour: str = "12h",
) -> list[int]:
    """
    Base-year AADT per vehicle type = average of D1 and D2, then count-hour power.

    Uses the first 12 survey hours when 12h is selected, or when 24h is selected on
  a 12h Excel survey. Uses all 24 survey hours when 24h is selected on a 24h Excel.
    """
    if daily_totals_12h is None and daily_totals_24h is None:
        daily_totals_12h = daily_totals or {}
        daily_totals_24h = daily_totals or {}
    elif daily_totals_12h is None:
        daily_totals_12h = daily_totals_24h or {}
    elif daily_totals_24h is None:
        daily_totals_24h = daily_totals_12h or {}

    source = select_daily_totals(
        daily_totals_12h,
        daily_totals_24h,
        survey_hours=survey_hours,
        count_hour=count_hour,
    )
    power = traffic_count_hour_multiplier(count_hour, survey_hours=survey_hours)
    averaged = [0.0] * VEHICLE_TYPE_COUNT
    sheet_values: list[list[int]] = []
    for sheet_name in _TARGET_SHEETS:
        if sheet_name not in source:
            continue
        values = source.get(sheet_name) or []
        sheet_values.append(values)

    divisor = max(len(sheet_values), 1)
    for values in sheet_values:
        for index in range(VEHICLE_TYPE_COUNT):
            if index < len(values):
                averaged[index] += int(values[index])

    return [int(round(value / divisor * power)) for value in averaged]


def build_summary_total_row(
    *,
    daily_totals_12h: dict[str, list[int]] | None = None,
    daily_totals_24h: dict[str, list[int]] | None = None,
    daily_totals: dict[str, list[int]] | None = None,
    survey_hours: int = 12,
    count_hour: str = "12h",
) -> list:
    """Average D1 and D2 totals for the selected count period and apply power."""
    adjusted = average_vehicle_totals(
        daily_totals_12h=daily_totals_12h,
        daily_totals_24h=daily_totals_24h,
        daily_totals=daily_totals,
        survey_hours=survey_hours,
        count_hour=count_hour,
    )
    grand_total = sum(adjusted)
    return ["Total", *adjusted, grand_total]


def filter_traffic_count_rows(
    rows: list[list],
    *,
    survey_hours: int,
    count_hour: str,
) -> list[list]:
    """Limit chart rows to the selected survey window."""
    if not rows:
        return []
    if str(count_hour).strip() == "24h" and survey_hours >= 24:
        return list(rows)

    sorted_rows = sorted(rows, key=lambda row: _time_sort_key(str(row[0])))
    return sorted_rows[:12]


def count_hour_power_description(count_hour: str, *, survey_hours: int) -> str:
    """Human-readable note for Excel read success dialog."""
    selected = str(count_hour).strip()
    power = traffic_count_hour_multiplier(selected, survey_hours=survey_hours)
    if selected == "24h" and survey_hours >= 24:
        return f"{selected} selected on {survey_hours}h Excel survey (power x{power:g}, full survey used)"
    if selected == "24h":
        return f"{selected} selected on {survey_hours}h Excel survey (power x{power:g}, 12h data extrapolated)"
    if survey_hours >= 24:
        return f"{selected} selected on {survey_hours}h Excel survey (power x{power:g}, first 12 survey hours used)"
    return f"{selected} selected on {survey_hours}h Excel survey (power x{power:g})"


def read_traffic_investigation_workbook(path: str | Path, *, count_hour: str = "12h") -> dict:
    """
    Read hourly traffic rows from sheets D1 and D2.

    Returns temporary session data:
    {
        "source_path": "...",
        "sheets": {"D1": [...], "D2": [...]},
        "daily_totals": {"D1": [...], "D2": [...]},  # summed C8:T127 per sheet
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
    daily_totals_12h: dict[str, list[int]] = {}
    daily_totals_24h: dict[str, list[int]] = {}
    survey_hours = 12
    missing: list[str] = []
    for sheet_name in _TARGET_SHEETS:
        sheet_path = sheet_paths.get(sheet_name)
        if not sheet_path:
            missing.append(sheet_name)
            continue
        with zipfile.ZipFile(path) as archive:
            grid = _read_sheet_grid(archive, sheet_path, shared_strings)
        sheets_data[sheet_name] = _extract_hourly_rows(grid)
        daily_totals_12h[sheet_name] = _extract_summed_vehicle_totals(grid, max_survey_hours=12)
        daily_totals_24h[sheet_name] = _extract_summed_vehicle_totals(grid, max_survey_hours=None)
        survey_hours = max(survey_hours, _detect_survey_hours(grid))

    daily_totals = select_daily_totals(
        daily_totals_12h,
        daily_totals_24h,
        survey_hours=survey_hours,
        count_hour=count_hour,
    )

    if not sheets_data and not daily_totals_12h and not daily_totals_24h:
        missing_text = ", ".join(missing) if missing else "D1, D2"
        raise ValueError(f"Could not find sheet(s): {missing_text}")

    combined = _combine_hourly_rows(
        sheets_data.get("D1", []),
        sheets_data.get("D2", []),
    )
    traffic_count_rows = filter_traffic_count_rows(
        combined,
        survey_hours=survey_hours,
        count_hour=count_hour,
    )
    summary_total_row = build_summary_total_row(
        daily_totals_12h=daily_totals_12h,
        daily_totals_24h=daily_totals_24h,
        survey_hours=survey_hours,
        count_hour=count_hour,
    )
    if not combined and not any(daily_totals_12h.values()) and not any(daily_totals_24h.values()):
        raise ValueError(
            "No traffic data was found in sheets D1 and D2 (C8:T127 or daily total row)."
        )

    return {
        "source_path": str(path),
        "sheets": sheets_data,
        "daily_totals": daily_totals,
        "daily_totals_12h": daily_totals_12h,
        "daily_totals_24h": daily_totals_24h,
        "survey_hours": survey_hours,
        "summary_total_row": summary_total_row,
        "traffic_count_rows_all": combined,
        "traffic_count_rows": traffic_count_rows,
        "traffic_count_hour": count_hour,
        "missing_sheets": missing,
    }


def read_traffic_count_rows(path: str | Path) -> list[list]:
    """Backward-compatible helper returning combined hourly rows."""
    return read_traffic_investigation_workbook(path)["traffic_count_rows"]


def _extract_summed_vehicle_totals(
    grid: dict[tuple[int, int], str],
    *,
    start_row: int = _DATA_START_ROW,
    end_row: int = _DATA_END_ROW,
    max_survey_hours: int | None = None,
) -> list[int]:
    """
    Sum vehicle counts from C8:T127 on the investigation form.

    When max_survey_hours is set, only rows in the first N survey hours are included.
    Sums all data rows in the range; hourly Total rows are used only when no
    other data rows exist. Falls back to the Daily Total row (row 69) if empty.
    """
    interval_totals = [0] * VEHICLE_TYPE_COUNT
    hourly_totals = [0] * VEHICLE_TYPE_COUNT
    current_block_start: int | None = None
    survey_start: int | None = None

    for row_index in range(start_row, end_row + 1):
        time_label = _time_label_at_row(grid, row_index)
        if time_label:
            current_block_start = _hour_block_start_hour(time_label)
            if survey_start is None:
                survey_start = current_block_start

        vehicle_counts = _read_vehicle_count_columns(grid, row_index)
        if not any(vehicle_counts):
            continue

        if max_survey_hours is not None and survey_start is not None:
            row_hour = current_block_start
            if row_hour is None:
                continue
            if not _within_first_survey_hours(survey_start, row_hour, max_survey_hours):
                continue

        if _is_hourly_total_row(grid, row_index):
            for index, value in enumerate(vehicle_counts):
                hourly_totals[index] += value
        else:
            for index, value in enumerate(vehicle_counts):
                interval_totals[index] += value

    if any(interval_totals):
        values = interval_totals
    elif any(hourly_totals):
        values = hourly_totals
    else:
        if max_survey_hours is not None:
            return [0] * (VEHICLE_TYPE_COUNT + 1)
        return _extract_daily_total_row(grid)

    values = list(values)
    values.append(sum(values))
    return values


def _detect_survey_hours(grid: dict[tuple[int, int], str]) -> int:
    """Return 24 when the sheet contains more than 12 hours of counted traffic."""
    hour_blocks_with_data: set[int] = set()
    current_block_start: int | None = None

    for row_index in range(_DATA_START_ROW, _DATA_END_ROW + 1):
        time_label = _time_label_at_row(grid, row_index)
        if time_label:
            current_block_start = _hour_block_start_hour(time_label)

        vehicle_counts = _read_vehicle_count_columns(grid, row_index)
        if any(vehicle_counts) and current_block_start is not None:
            hour_blocks_with_data.add(current_block_start)

    if not hour_blocks_with_data:
        return 12
    if len(hour_blocks_with_data) > 12:
        return 24
    span = max(hour_blocks_with_data) - min(hour_blocks_with_data) + 1
    return 24 if span > 12 else 12


def _hour_block_start_hour(time_label: str) -> int:
    match = _TIME_RE.match(time_label.strip())
    if not match:
        return 0
    return int(match.group(1))


def _within_first_survey_hours(survey_start: int, hour: int, count_hours: int) -> bool:
    offset = (hour - survey_start) % 24
    return offset < count_hours


def _is_hourly_total_row(grid: dict[tuple[int, int], str], row_index: int) -> bool:
    first_cell = _cell_text(grid, row_index, 1).strip().lower()
    second_cell = _cell_text(grid, row_index, 2).strip().lower()
    return first_cell == "total" or second_cell == "total"


def _read_vehicle_count_columns(grid: dict[tuple[int, int], str], row_index: int) -> list[int]:
    """Read vehicle counts from columns C through T for one row."""
    values: list[int] = []
    for column_index in range(_MOTOR_COL, _END_VEHICLE_COL + 1):
        text = _cell_text(grid, row_index, column_index).strip()
        values.append(_to_int(text) if _is_number(text) else 0)
    return values


def _extract_daily_total_row(grid: dict[tuple[int, int], str]) -> list[int]:
    """Read Daily Total row (C69:T69 + U69)."""
    row_index = _find_daily_total_row(grid)
    values = _read_vehicle_count_columns(grid, row_index)
    total_text = _cell_text(grid, row_index, _TOTAL_COL).strip()
    if _is_number(total_text):
        values.append(_to_int(total_text))
    else:
        values.append(sum(values))
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
    values = _read_vehicle_count_columns(grid, row_index)
    total_text = _cell_text(grid, row_index, _TOTAL_COL).strip()
    values.append(_to_int(total_text) if _is_number(total_text) else sum(values))
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
