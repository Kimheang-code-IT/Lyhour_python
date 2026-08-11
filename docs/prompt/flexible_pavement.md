# Page Prompt — Flexible Pavement

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Flexible pavement design tools: **Catalog/Analysis** (future) and **AASHTO** (inputs + effective roadbed soil resilient modulus from monthly CBR).

## Status

**Partial** — Catalog/Analysis lookup + design chart implemented; AASHTO tab implemented; MPWT thickness / SN tab implemented.

## Catalog / Analysis (current)

- Input left: Seal type (`AC` / `DBST`), Traffic (filtered by catalog), Subgrade CBR (%)
- Input right:
  - Select 1 = Foundation class `F1 (S3)` … `F4 (S6)` (suggested from CBR)
  - Select 2 = Catalog structure family (depends on seal type)
- Design block: engineering cross-section chart (hatched layers + thickness labels on the right) + bottom legend
- Data: `app/data/pavement_catalog.py` (`MATERIAL_COLORS` / `MATERIAL_HATCHES`)
- Chart: `app/chart/pavement_catalog.py` → `draw_pavement_catalog_section`
- Lookup keys: seal + catalog + traffic + foundation → layer thicknesses (drawn 1:1 on the section)

## Route & files

| Item | Value |
|------|--------|
| Route key | `flexible_pavement` |
| Stack index | `FLEXIBLE_PAVEMENT` |
| Package | `app/pages/Flexible_Pavement/` |
| Shell | `Flexible_Pavement/page.py` → `FlexiblePavementPage` |

### Subpages

| Tab | Module | Class |
|-----|--------|-------|
| Catalog/Analysis | `catalog_analysis.py` | `CatalogAnalysisPage` |
| AASHTO | `aashto.py` | `AashtoPage` |
| MPWT | `mpwt.py` | `MpwtPage` |

Shared helpers: `Flexible_Pavement/common.py`  
Data: `app/data/aashto_resilient_modulus.py`, `app/data/mpwt_thickness.py`  
Export: `from app.pages.Flexible_Pavement import FlexiblePavementPage, AashtoPage, CatalogAnalysisPage, MpwtPage`

Fixed right panel: **yes**.

> Note: Prefer the **package** `app/pages/Flexible_Pavement/` as source of truth. Avoid maintaining a parallel `Flexible_Pavement.py` module that conflicts with the package.

## AASHTO logic (current)

- Given parameters: ESAL, Pt, P0, S0, R0, h4
- Layer moduli E1/E2/E3 (HMA / base / subbase) + subgrade CBR
- Monthly CBR → CBR_eff → MR (psi) → relative damage uf
- Effective MR from average uf (AASHTO resilient modulus workflow)
- Quick results: ESAL, P0, Pt, R0, Effective MR, Average uf

## MPWT logic (current)

- Section 3.1: drainage coefficients `m2`, `m3` only — **do not** show `a1`/`a2`/`a3` ln/log formulas (red-marked in source sheet)
- Section 3.2: min thickness reference (AASHTO vs Japan) + AASHTO SN principle equation
- Section 3.3: design params (ESAL, R0, S0, P0, Pt, MR, E1–E3) + selected `h1`/`h2`/`h3`
  - SN labels omit struck-through `a1`/`a2`/`m2`/`a3`/`m3` text; coefficients still computed internally
  - `a1 = 0.17·ln(E1_MPa) − 0.9259`
  - `a2 = 0.249·log10(E2_psi) − 0.977`
  - `a3 = 0.227·log10(E3_psi) − 0.839`
  - `SNi` uses thickness in inches (`cm / 2.54`)
- Check: Total SN ≥ Required SN → OK / NG
- Data: `app/data/mpwt_thickness.py`

## Agent rules

1. Extend Catalog/Analysis inside `catalog_analysis.py`, not inside the shell.
2. Modulus table styling helpers live in `common.py` (font, row height, summary HTML).
3. Keep MR formulas in `aashto_resilient_modulus.py`.
4. Keep MPWT SN / thickness math in `mpwt_thickness.py`; UI in `mpwt.py`.
5. If Catalog needs charts, add `app/chart/...` drawers and reuse `MatplotlibChartWidget`.
6. Connect input changes through `AashtoPage.connect_inputs_changed` / `MpwtPage.connect_inputs_changed` for Quick Panel updates.
