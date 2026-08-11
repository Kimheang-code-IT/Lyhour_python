# Page Prompt — Cross Section

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Road Geometry Design — typical / design cross-section tools (lane width, shoulders, slopes, etc.).

## Status

**Partial** — Input + live Design cross-section diagram implemented.

## Route & files

| Item | Value |
|------|--------|
| Route key | `rgd_cross_section` |
| Stack index | `RGD_CROSS_SECTION` |
| Page file | `app/pages/RGD_Cross_Section.py` |
| Layout | `blank` |
| Data | `app/data/cross_section.py` → `build_cross_section` |
| Chart | `app/chart/cross_section.py` → `draw_cross_section` |

## Current UI

- No Quick Result button, no right preview image (`PAGES_WITHOUT_PREVIEW`)
- **Input** block:
  - Road classification select: `R1/U1` … `R6/U6`
  - Design speed (km/h)
  - Lane (m)
  - Shoulder (m)
- **Design** block: dynamic cross-section (cut / shoulder / lanes / median / shoulder / fill)
  - Lane & shoulder widths from inputs
  - Lanes per direction + median width derived from road class / speed
  - Dimension labels, cross-slope %, direction arrows

## Agent rules

1. Keep Input + Design two-block layout.
2. Do not add Quick Result / preview image to this page.
3. Keep formulas in `app/data/cross_section.py`; drawing in `app/chart/cross_section.py`.
4. Prefer engineering diagram style (labels, dimensions), not dashboard cards.
