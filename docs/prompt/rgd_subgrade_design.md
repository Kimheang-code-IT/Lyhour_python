# Page Prompt — Subgrade Design

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Subgrade strength tools from field tests: **DCP**, **CBR Equivalent**, and **FWD** (placeholder), with charts and Quick Results.

## Status

**Partial** — DCP + CBR Equivalent implemented; FWD placeholder.

## Route & files

| Item | Value |
|------|--------|
| Route key | `rgd_subgrade_design` |
| Stack index | `RGD_SUBGRADE_DESIGN` |
| Shell | `app/pages/RGD_Subgrade_Design.py` |
| Package | `app/pages/Subgrade_Design/` |

### Subpages

| Tab | Module | Class |
|-----|--------|-------|
| DCP | `dcp.py` | `DcpPage` |
| CBR Equivalent | `cbr.py` | `CbrPage` |
| FWD | `fwd.py` | `FwdPage` |

Shared UI helpers: `Subgrade_Design/common.py`.

### Data & charts

| Concern | Module |
|---------|--------|
| DCP compute | `app/data/dcp_analysis.py` |
| CBR Equivalent compute | `app/data/cbr_equivalent.py` |
| Depth vs Blows / CBR charts | `app/chart/dcp.py` |
| CBR profile chart | `app/chart/cbr_equivalent.py` |

Fixed right panel: **yes**.

## Logic notes

- DCP: blows + cumulative penetration → penetration index → empirical CBR (`221 / PI`)
- CBR Equivalent modes:
  - **Use DCP data** — read-only English table (Depth, Thickness, Total Blows, Penetration Rate, Layered-CBR, Evaluation) from DCP tab
  - **User define** — editable `CBR (%)` + `Hi (mm)` layers (+ Add row)
- Formula: `CBR_eq = Σ (CBR_i × h_i) / Σ h_i` over all layers (no design-depth filter)
- Input block shows layered CBR/h reference image (`app/assets/image/image.png`)
- Result line only in Input (`Result = …`); Analysis table/chart removed from this tab
- Tables: Excel paste + optional “+ Add row” footer (user-define mode)


## Agent rules

1. Keep tab pages reusable under `Subgrade_Design/`; shell only composes tabs + quick panel.
2. CBR must not copy DCP input tables — always read from `DcpPage`.
3. Chart drawing stays in `app/chart/`; analysis stays in `app/data/`.
4. When implementing FWD, add data + chart modules first, then flesh out `fwd.py`.
5. Preserve table font/row-height helpers in `common.py`.
