# Page Prompt — Pavement Evaluation

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Evaluate existing pavement condition / remaining life. Current implementation:
traffic-class pavement structure table with auto-filled layer thicknesses and
FWD / LWD / B_Beam targets.

## Status

**Implemented** — traffic-class evaluation table (T1–T8).

## Route & files

| Item | Value |
|------|--------|
| Route key | `pavement_evaluation` |
| Stack index | `PAVEMENT_EVALUATION` |
| Page file | `app/pages/Pavement_Evaluation.py` |
| Data | `app/data/pavement_evaluation.py` |
| Layout | `default` |

Right preview panel is hidden for this page (`PAGES_WITHOUT_PREVIEW`).

## Traffic-class evaluation table

- Traffic Class combo: **T1–T8**.
- Rows: AC, Base Course (CBR ≥ 80%), Subbase (CBR ≥ 30%),
  Selected Sub grade (CBR ≥ 10%, fixed 500 mm), Sub grade / Embankment (CBR ≥ 2%).
- Columns: Layer, Thickness (mm), Section, FWD (MPa), LWD (MPa), B_Beam (mm).
- Section column paints the layer hatch via `HatchSwatch`, reusing
  `MATERIAL_COLORS` / `MATERIAL_HATCHES` from `app/data/pavement_catalog.py`.
- Selecting a traffic class auto-fills thicknesses and FWD / LWD / B_Beam.

## Data note

Thickness and FWD / LWD / B_Beam values in `pavement_evaluation.py` are
**project placeholders** — replace `DESIGN_THICKNESS_MM` and
`FIELD_TEST_VALUES` with the values from the standard being applied.

## Agent rules

1. Coordinate with Subgrade FWD tab to avoid duplicated FWD engines — share `app/data` + `app/chart`.
2. Use session Excel import patterns from Traffic Input.
3. Keep evaluation formulas testable in `app/data/` / `tests/`.
4. Keep the traffic-class tables in `app/data/pavement_evaluation.py` (not in the page).
