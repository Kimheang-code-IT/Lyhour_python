# Page Prompt — Rigid Pavement

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Concrete / rigid pavement thickness design under **Pavement and Material Design → Rigid Pavement**, with **MPWT** and **AASHTO** as page tabs (same pattern as Flexible Pavement).

## Status

**Implemented** (MPWT + AASHTO 1993 tabs).

## Route & files

| Item | Value |
|------|--------|
| Route key | `rigid_pavement` |
| Stack index | `RIGID_PAVEMENT=10` |
| Page shell | `app/pages/Rigid_Pavement/page.py` |
| Tabs | `mpwt.py`, `aashto.py` (+ `common.py`) |
| Calculation | `app/data/mpwt_rigid.py`, `app/data/aashto_rigid.py` |
| Layout | `blank` |

## Tabs

1. **MPWT** — Input Parameter → Analysis & Result (base / min thickness + fatigue & erosion side-by-side) → Reinforcement Design  
2. **AASHTO** — Given params, monthly CBR table, effective/corrected k, Dcal, verification, final thickness  

Logic stays in `app/data/`; UI only binds inputs and displays results.

## Agent rules

1. Keep MPWT and AASHTO as tabs on one Rigid Pavement page (not sidebar sub-pages).  
2. Keep calculation modules separate from UI.  
3. Keep engineering units explicit (mm, cm, MPa, psi, pci).  
4. Preserve full precision internally; round only displayed values.
