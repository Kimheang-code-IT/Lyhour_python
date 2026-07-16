# Page Prompt — Cross Section

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Road Geometry Design — typical / design cross-section tools (lane width, shoulders, slopes, etc.).

## Status

**Placeholder** (BasePage shell only).

## Route & files

| Item | Value |
|------|--------|
| Route key | `rgd_cross_section` |
| Stack index | `RGD_CROSS_SECTION` |
| Page file | `app/pages/RGD_Cross_Section.py` |
| Layout | `default` |

## Planned direction (when implementing)

- Input: road class, lane/shoulder widths, crossfall, side slopes
- Output: dimensioned cross-section diagram
- Chart: new reusable drawer in `app/chart/` (e.g. `cross_section.py`)
- Data: `app/data/` for geometry calculations

## Agent rules

1. Do not leave a silent empty page — keep a clear section title when adding UI.
2. Follow Horizontal Curvature / Superelevation patterns for Input + Analysis blocks.
3. Prefer engineering diagram style (labels, dimensions), not dashboard cards.
4. Register any new chart in `app/chart/__init__.py`.
