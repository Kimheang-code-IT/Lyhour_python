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
- Sections 3.1–3.3 (thickness / SN) live on this tab (not MPWT)
- Quick results: ESAL, P0, Pt, R0, Effective MR, Average uf, Required SN, Total SN, layer thicknesses, Design check

## Thickness / SN (sections 3.1–3.3, AASHTO tab)

- Section 3.1: structural coefficients `a1`/`a2`/`a3` and drainage coefficients `m2`/`m3`
- Section 3.2: min thickness reference (AASHTO vs Japan) + AASHTO SN principle equation
- Section 3.3: required SN + selected `h1`/`h2`/`h3` → SN₁ / SN₂ / SN₃ and Total SN check
- Check: Total SN ≥ Required SN → OK / NG
- Data: `app/data/mpwt_thickness.py`
- UI: `app/pages/Flexible_Pavement/mpwt.py` (`ThicknessSnPanel`) embedded in `aashto.py`

## MPWT tab

- Placeholder only. Thickness design was moved to the AASHTO tab.

## Agent rules

1. Extend Catalog/Analysis inside `catalog_analysis.py`, not inside the shell.
2. Modulus table styling helpers live in `common.py` (font, row height, summary HTML).
3. Keep MR formulas in `aashto_resilient_modulus.py`.
4. Keep SN / thickness math in `mpwt_thickness.py`; UI panel in `mpwt.py` (`ThicknessSnPanel`), shown on the AASHTO tab.
5. If Catalog needs charts, add `app/chart/...` drawers and reuse `MatplotlibChartWidget`.
6. Connect input changes through `AashtoPage.connect_inputs_changed` for Quick Panel updates.
