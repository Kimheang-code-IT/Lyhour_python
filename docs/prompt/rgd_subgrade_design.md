# Page Prompt — Subgrade Design

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Subgrade strength tools from field tests: **DCP**, **CBR Equivalent**, and **FWD/BB** (placeholder), with charts and Quick Results.

## Status

**Partial** — DCP + CBR Equivalent implemented; FWD/BB placeholder.

## Navigation

Indented sidebar folder (not top tabs):

| Sidebar item | Route key | Stack index |
|--------------|-----------|-------------|
| Subgrade Design (folder) | `subgrade_design` | — |
| DCP | `subgrade_dcp` | `SUBGRADE_DCP` |
| CBR Equivalent | `subgrade_cbr_equivalent` | `SUBGRADE_CBR` |
| FWD/BB | `subgrade_fwd_bb` | `SUBGRADE_FWD` |

## Route & files

| Item | Value |
|------|--------|
| Shell pages | `app/pages/Subgrade_DCP.py`, `Subgrade_CBR.py`, `Subgrade_FWD.py` |
| Content widgets | `app/pages/Subgrade_Design/` |

### Subpages

| Nav item | Shell | Content |
|----------|-------|---------|
| DCP | `SubgradeDcpPage` | `Subgrade_Design/dcp.py` → `DcpPage` |
| CBR Equivalent | `SubgradeCbrPage` | `Subgrade_Design/cbr.py` → `CbrPage` |
| FWD/BB | `SubgradeFwdPage` | `Subgrade_Design/fwd.py` → `FwdPage` |

Shared UI helpers: `Subgrade_Design/common.py`.

### Data & charts

| Concern | Module |
|---------|--------|
| DCP compute | `app/data/dcp_analysis.py` |
| CBR Equivalent compute | `app/data/cbr_equivalent.py` |
| Depth vs Blows / CBR charts | `app/chart/dcp.py` |
| CBR profile chart | `app/chart/cbr_equivalent.py` |

Fixed right panel: **yes** (all three subgrade pages).

## Logic notes

- DCP: blows + cumulative penetration → penetration index → empirical CBR (`221 / PI`)
- DCP Layered CBR Summary (below charts): aggregate every **200 mm**
  - Columns: Depth, Layer Thickness, Total Blows, Blows/300 mm, Layered-CBR (%), Remark
  - “Blows / 300 mm” column shows penetration index (mm/blow), matching typical MPWT sheets
  - Layered-CBR uses TRL: `log10(CBR) = 2.48 − 1.057·log10(PI)`
- CBR Equivalent modes:
  - **Use DCP data** — read-only table loaded from DCP **Layered CBR Summary** (not raw DCP input)
    - Depth, Thickness, Total Blows, Penetration Rate, Layered-CBR, Evaluation
    - CBR_eq weighted from Layered-CBR × Thickness of those summary layers
    - Auto-refreshes when DCP input changes
  - **User define** — editable `CBR (%)` + `Hi (mm)` layers (+ Add row)
- Formula: `CBR_eq = Σ (CBR_i × h_i) / Σ h_i` over all layers (no design-depth filter)
- Input block shows layered CBR/h reference image (`app/assets/image/image.png`)

## Agent rules

1. Keep content widgets under `Subgrade_Design/`; shell pages only compose title + quick panel + content.
2. CBR **Use DCP data** must read from DCP `read_layered_cbr_summary()` / Layered CBR Summary — never rebuild from raw DCP input rows.
3. Chart drawing stays in `app/chart/`; analysis stays in `app/data/`.
4. When implementing FWD/BB, add data + chart modules first, then flesh out `fwd.py`.
5. Preserve table font/row-height helpers in `common.py`.
6. Do not reintroduce SegmentedWidget tabs for Subgrade — use indented sidebar items.
