# Page Prompt — Horizontal Curvature

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Design and check horizontal curve geometry: minimum radius from speed/e/f tables, verification, simple-curve elements diagram (PC–PI–PT), PDF preview/download.

## Status

**Implemented**.

## Route & files

| Item | Value |
|------|--------|
| Route key | `rgd_horizontal_curvature` |
| Stack index | `RGD_HORIZONTAL_CURVATURE` |
| Page file | `app/pages/RGD_Horizontal_Curvature.py` |
| Data | `app/data/tables_Horizontal_Curvature.py`, `app/data/simple_curve_geometry.py` |
| Chart | `app/chart/simple_curve.py` → `draw_simple_curve_diagram` |
| Services | `app/services/pdf_preview.py` |

Fixed right panel: **yes** (`FIXED_RIGHT_PANEL_PAGES`).

## Key engineering logic

- \( R_{min} = V^2 / (127 \cdot (e + f)) \) with table lookups (Table 7.5 / 7.6 style)
- Surface type: Sealed / Unsealed → vehicle type + friction options
- Speed discrete: 25–130 km/h
- `e_max` pavement superelevation constraint (≥ 2.5%)
- Simple curve elements: TL, L, C, E, M from R and Δ

## UI structure

- Input section (speed, e, f, surface, vehicle, friction)
- Analysis / verification messages
- Matplotlib simple-curve diagram
- PDF preview + download actions
- Quick Result panel sync

## Agent rules

1. Keep table lookup functions in `tables_Horizontal_Curvature.py`.
2. Keep diagram drawing in `app/chart/simple_curve.py` (not in the page).
3. Theme-aware diagram lines/text via `theme_tokens()`.
4. Preserve PDF preview workflow through `pdf_preview` service.
5. When changing validation messages, keep engineering wording clear.
