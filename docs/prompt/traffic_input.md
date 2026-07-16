# Page Prompt — Traffic Input

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Collect project traffic inputs for analysis: Excel import and/or direct manual entry (count hours, area type, design year, growth, LOS, vehicle class data).

## Status

**Implemented** (primary traffic entry flow).

## Route & files

| Item | Value |
|------|--------|
| Route key | `traffic_input` |
| Stack index | `TRAFFIC_INPUT` |
| Page file | `app/pages/Traffic_Analysis_input.py` |
| Related | `app/services/excel_io.py`, `app/data/area_type.py`, `app/data/level_of_service.py` |

## UI structure

- Title: Traffic Analysis input
- Sections with radios:
  - **Read Data (Excel)** — import workbook
  - **Direct Input** — manual fields
- Key fields: traffic count hours (12h/24h), area type, design year, growth rates, LOS options
- Uses shared form controls and theme-aware cards

## Inputs → outputs

- **In:** Excel path / typed traffic parameters
- **Out:** Session/cache values consumed by Traffic Analysis pages
- Import history is session-only (File menu recent imports)

## Agent rules

1. Keep Excel import path through `ExcelIOService` / excel session services.
2. Preserve radio show/hide section pattern.
3. Do not hardcode Khmer/English strings outside i18n when adding nav-facing labels.
4. After import changes, ensure Analysis pages still refresh from the same session source.
5. Avoid adding loading overlays on simple field edits; loading is for import ops.
