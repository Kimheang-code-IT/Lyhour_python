"""Read TLD (Truck Load Distribution) workbooks for ESAL calculations."""
from __future__ import annotations

from pathlib import Path

from app.services.traffic_esal import AXLE_TABLE_GROUPS

_TLD_AXLE_LABELS = {
    "SAST": "steering_sast",
    "SADT": "sadt",
    "TAST": "tast",
    "TADT": "tadt",
    "TRDT": "trdt",
}


def read_tld_workbook(path: str | Path) -> dict:
    """
    Load a TLD Excel file for the ESAL tab.

    Returns axle group numbers keyed like traffic_esal.AXLE_TABLE_GROUPS.
    Parsing is intentionally tolerant: when structured values are not found,
    the file is still accepted and ESAL can fall back to session traffic data.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"TLD file not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix not in {".xlsx", ".xlsm", ".xls"}:
        raise ValueError("TLD file must be an Excel workbook (.xlsx, .xlsm, or .xls).")

    axle_numbers = {key: 0 for key, _ in AXLE_TABLE_GROUPS}
    parsed_values = _try_parse_xlsx_axle_numbers(file_path)
    for key, value in parsed_values.items():
        if key in axle_numbers:
            axle_numbers[key] = max(0, int(value))

    return {
        "source_path": str(file_path.resolve()),
        "axle_numbers": axle_numbers,
        "has_parsed_values": any(axle_numbers.values()),
    }


def _try_parse_xlsx_axle_numbers(path: Path) -> dict[str, int]:
    """Best-effort parse of axle labels and numeric values from the first worksheet."""
    if path.suffix.lower() not in {".xlsx", ".xlsm"}:
        return {}

    try:
        import zipfile
        from xml.etree import ElementTree as ET
    except Exception:
        return {}

    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel_ns = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}
    office_rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

    try:
        with zipfile.ZipFile(path) as archive:
            shared_strings: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                for item in root.findall(".//main:si", ns):
                    text_parts = [node.text or "" for node in item.findall(".//main:t", ns)]
                    shared_strings.append("".join(text_parts))

            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            rel_map = {
                rel.attrib["Id"]: rel.attrib["Target"]
                for rel in rels.findall("rel:Relationship", rel_ns)
            }
            first_sheet = workbook.find(".//main:sheet", ns)
            if first_sheet is None:
                return {}
            target = rel_map.get(first_sheet.attrib.get(f"{{{office_rel}}}id", ""), "")
            if not target:
                return {}
            sheet_path = f"xl/{target.lstrip('/')}"
            if sheet_path not in archive.namelist():
                return {}

            sheet = ET.fromstring(archive.read(sheet_path))
            cells: dict[str, str] = {}
            for cell in sheet.findall(".//main:c", ns):
                ref = cell.attrib.get("r", "")
                cell_type = cell.attrib.get("t")
                value_node = cell.find("main:v", ns)
                if value_node is None or value_node.text is None:
                    continue
                if cell_type == "s":
                    index = int(value_node.text)
                    cells[ref] = shared_strings[index] if index < len(shared_strings) else ""
                else:
                    cells[ref] = value_node.text

            return _extract_axle_numbers_from_cells(cells)
    except Exception:
        return {}


def _extract_axle_numbers_from_cells(cells: dict[str, str]) -> dict[str, int]:
    """Map nearby label/value pairs such as SAST -> 287."""
    import re

    label_to_key = {label.upper(): key for label, key in _TLD_AXLE_LABELS.items()}
    values: dict[str, int] = {}

    for ref, text in cells.items():
        normalized = str(text).strip().upper()
        if normalized not in label_to_key:
            continue
        key = label_to_key[normalized]
        row = re.match(r"^([A-Z]+)", ref)
        if not row:
            continue
        row_digits = re.search(r"(\d+)$", ref)
        if not row_digits:
            continue
        row_number = int(row_digits.group(1))
        column = row.group(1)
        for offset in (1, 2):
            neighbor_ref = f"{_column_after(column, offset)}{row_number}"
            neighbor_value = cells.get(neighbor_ref, "").strip()
            if _looks_numeric(neighbor_value):
                values[key] = int(round(float(neighbor_value.replace(",", ""))))
                break
    return values


def _column_after(column: str, offset: int) -> str:
    letters = list(column)
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    index += offset
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _looks_numeric(value: str) -> bool:
    if not value:
        return False
    try:
        float(value.replace(",", ""))
        return True
    except ValueError:
        return False
