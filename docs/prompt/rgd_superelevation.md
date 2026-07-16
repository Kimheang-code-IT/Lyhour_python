# Page Prompt — Superelevation Design

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Compute and draw the **Full Superelevation Graph**: Tro, Sro, Le, Lc and outside/inside edge transition profiles with station markers (SSD, TS, SC, CS, ST, ESD).

## Status

**Implemented**.

## Route & files

| Item | Value |
|------|--------|
| Route key | `rgd_superelevation_design` |
| Stack index | `RGD_SUPERELEVATION` |
| Page file | `app/pages/RGD_Superelevation_Design.py` |
| Data | `app/data/superelevation_profile.py` |
| Chart | `app/chart/superelevation.py` → `draw_superelevation_profile` |

Fixed right panel: **yes**.

## Key formulas

- Tro = WR × e₁ / relative_gradient  
- Le = WR × (e₁ + e_max) / relative_gradient  
- Sro = Le − Tro  
- Lc = curve length (input)

### Edge elevations (rotation about centerline)

| Station | Outside | Inside |
|---------|---------|--------|
| SSD | −e₁ | −e₁ |
| TS | 0 | −e₁ |
| SC | +e_max | −e_max |
| CS | +e_max | −e_max |
| ST | 0 | −e₁ |
| ESD | −e₁ | −e₁ |

Stations formatted as chainage `16+200` via `format_station`.

## UI inputs

- Vehicle speed, gross fall e₁, e_max, road class, lane width WR
- Relative gradient, curve length Lc, start station

## Chart requirements

- Fixed Y-axis −10% … +15% (2.5 steps)
- Series: Alignment, Centerline, Inside Edge, Outside Edge
- Dimension arrows: Le, Lc, Tro, Sro
- Cross-section icons under key stations
- Outside legend, figure caption

## Agent rules

1. Never put drawing code back into `app/data/superelevation_profile.py`.
2. Change profile math in data; change visuals in `app/chart/superelevation.py`.
3. Keep chart margins large enough for icons/caption (`subplots_adjust`).
4. Quick panel keys: Transition Length Le, Tro, Sro, Curve length.
5. Match reference engineering drawing style when adjusting annotations.
