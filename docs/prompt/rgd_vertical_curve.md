# Page Prompt — Vertical Curve

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Road Geometry Design — equal-tangent **parabolic** crest/sag vertical curves (K-values, PVC/PVI/PVT, sight-distance check, stakeout).

## Status

**Implemented.**

## Route & files

| Item | Value |
|------|--------|
| Route key | `rgd_vertical_curve` |
| Stack index | `RGD_VERTICAL_CURVE` |
| Page file | `app/pages/RGD_Vertical_Curve.py` |
| Data | `app/data/vertical_curve.py` |
| Chart | `app/chart/vertical_curve.py` |
| Layout | `blank` |

## UI

Left inputs (concept layout):

- Design Parameters — curve type Crest/Sag, speed, sight criterion, AASHTO 2018
- Grade Data — g₁, g₂, algebraic difference A
- PVI Location — station, elevation
- Curve Length — design L **or** target K
- Calculate Geometry

Right:

- Profile canvas (PVC / PVI / PVT, parabola, optional tangents / high-low / SD envelope)
- Geometric Summary + Stakeout Data tabs

Selecting **Sag** (or **Crest**) swaps g₁/g₂ so the same parabolic equation draws the opposite curve.

## Geometry

\[
y = \frac{A}{200L}\,x^{2},\quad E(x)=E_{PVC}+\frac{g_1}{100}x+\frac{A_{signed}}{200L}x^{2}
\]

- \(A_{signed}=g_2-g_1\) (percent), \(K=L/|A|\)
- PVC = PVI − L/2, PVT = PVI + L/2
- Crest when \(g_1>g_2\); sag when \(g_1<g_2\)

## Agent rules

1. Keep formulas in `app/data/vertical_curve.py`.
2. Keep drawing in `app/chart/vertical_curve.py`.
3. Station labels use `format_station` (`1+250.00`).
4. Changing Crest ↔ Sag must only invert the parabola (swap grades), not replace the design method.
