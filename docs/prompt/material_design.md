# Page Prompt — Material Design

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Pavement material selection / specification helpers (aggregates, asphalt, concrete mixes).

## Status

**Placeholder** (BasePage shell only).

## Route & files

| Item | Value |
|------|--------|
| Route key | `material_design` |
| Stack index | `MATERIAL_DESIGN` |
| Page file | `app/pages/Material_Design.py` |
| Layout | `default` |

## Planned direction (when implementing)

- Spec tables, gradation charts, mix design inputs
- Reuse Excel paste tables and chart package
- Keep material standards/tables under `app/data/`

## Agent rules

1. Prefer data-driven tables over hardcoding long grade lists in the page.
2. Use shared table styling patterns from Subgrade/Flexible pages.
3. Any gradation plot → `app/chart/`.
4. Update status in this file when features land.
