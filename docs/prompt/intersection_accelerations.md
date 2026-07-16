# Page Prompt — Intersection Accelerations

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Intersection Design — acceleration lane length for merging / entering traffic.

## Status

**Placeholder** (BasePage shell only).

## Route & files

| Item | Value |
|------|--------|
| Route key | `intersection_accelerations` |
| Stack index | `INTERSECTION_ACCELERATIONS` |
| Page file | `app/pages/Intersection_Accelerations.py` |
| Layout | `default` |

## Planned direction (when implementing)

- Inputs: highway speed, entrance speed, grade, acceleration rate / AASHTO tables
- Output: La length, stations, schematic
- Share intersection geometry utilities with Taper / Decelerations when possible

## Agent rules

1. Do not invent one-off UI kits — reuse form controls and section frames.
2. Put table lookups in `app/data/`, not in the page class.
3. Keep naming consistent: Accelerations (plural) matches nav i18n key.
4. Update this prompt when logic ships.
