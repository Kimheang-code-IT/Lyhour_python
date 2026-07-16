# Page Prompt — Intersection Decelerations

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Intersection Design — deceleration / turning-lane length for exiting traffic.

## Status

**Placeholder** (BasePage shell only).

## Route & files

| Item | Value |
|------|--------|
| Route key | `intersection_decelerations` |
| Stack index | `INTERSECTION_DECELERATIONS` |
| Page file | `app/pages/Intersection_Decelerations.py` |
| Layout | `default` |

## Planned direction (when implementing)

- Inputs: design speed, exit speed, grade, deceleration rate / tables
- Output: Ld length, taper + storage if applicable, schematic
- Align with Accelerations page patterns for consistency

## Agent rules

1. Share calculation modules with Accelerations where formulas are symmetric.
2. Prefer one intersection chart style across Taper / Accel / Decel.
3. Keep Quick Panel optional unless user requests fixed right panel for this section.
4. Update status in this file when implemented.
