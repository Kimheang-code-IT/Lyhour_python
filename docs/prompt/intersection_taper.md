# Page Prompt — Intersection Taper

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Intersection Design — taper length geometry for lane drops / merges / turn-lane tapers.

## Status

**Placeholder** (BasePage shell only).

## Route & files

| Item | Value |
|------|--------|
| Route key | `intersection_taper` |
| Stack index | `INTERSECTION_TAPER` |
| Page file | `app/pages/Intersection_Taper.py` |
| Layout | `default` |

## Planned direction (when implementing)

- Inputs: design speed, shift width, taper ratio / formula (e.g. L = W×S / …)
- Output: required taper length, plan sketch
- Chart: plan-view taper diagram in `app/chart/`

## Agent rules

1. Keep Intersection pages visually consistent with each other (Taper / Accel / Decel).
2. Prefer shared geometry helpers if formulas overlap across the three pages.
3. Use blank/default layout conventions already set in `page_registry`.
4. Update status here when implemented.
