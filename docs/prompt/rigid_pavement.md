# Page Prompt — Rigid Pavement

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Concrete / rigid pavement thickness and joint design (AASHTO or catalog methods).

## Status

**Placeholder** (BasePage shell only).

## Route & files

| Item | Value |
|------|--------|
| Route key | `rigid_pavement` |
| Stack index | `RIGID_PAVEMENT` |
| Page file | `app/pages/Rigid_Pavement.py` |
| Layout | `default` |

## Planned direction (when implementing)

- Prefer folder pattern like Flexible Pavement if multiple methods/tabs:
  - `app/pages/Rigid_Pavement/` with method subpages
- Data in `app/data/`, charts in `app/chart/`
- Consider Quick Panel for key thickness / joint results

## Agent rules

1. Do not dump a large single-file UI if multiple design methods are planned — use a package.
2. Mirror Flexible Pavement input section framing and form controls.
3. Keep engineering units explicit (mm, MPa, psi).
4. Update this prompt when the first real tab ships.
