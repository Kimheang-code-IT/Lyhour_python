# Page Prompt — Vertical Curve

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Road Geometry Design — crest/sag vertical curves (K-values, lengths, sight distance, grade transitions).

## Status

**Placeholder** (BasePage shell only).

## Route & files

| Item | Value |
|------|--------|
| Route key | `rgd_vertical_curve` |
| Stack index | `RGD_VERTICAL_CURVE` |
| Page file | `app/pages/RGD_Vertical_Curve.py` |
| Layout | `default` |

## Planned direction (when implementing)

- Inputs: V, grades g1/g2, A, required SSD/headlight distance, design K
- Outputs: L required, PVC/PVI/PVT stations, profile plot
- Data: `app/data/vertical_curve.py` (new)
- Chart: `app/chart/vertical_curve.py` (new)

## Agent rules

1. Mirror Superelevation page structure: Input block + Analysis chart.
2. Keep formulas out of the page file.
3. Stationing format should match `format_station` style used elsewhere.
4. Prefer one clear profile chart with PVC/PVI/PVT markers.
