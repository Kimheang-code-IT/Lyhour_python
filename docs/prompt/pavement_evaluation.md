# Page Prompt — Pavement Evaluation

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Evaluate existing pavement condition / remaining life (e.g. FWD, IRI, distress, overlay design inputs).

## Status

**Placeholder** (BasePage shell only).

## Route & files

| Item | Value |
|------|--------|
| Route key | `pavement_evaluation` |
| Stack index | `PAVEMENT_EVALUATION` |
| Page file | `app/pages/Pavement_Evaluation.py` |
| Layout | `default` |

## Planned direction (when implementing)

- May reuse Subgrade FWD concepts and Flexible overlay methods
- Import measured deflection / condition data via Excel services
- Charts for deflection bowls / condition indices in `app/chart/`

## Agent rules

1. Coordinate with Subgrade FWD tab to avoid duplicated FWD engines — share `app/data` + `app/chart`.
2. Use session Excel import patterns from Traffic Input.
3. Keep evaluation formulas testable in `app/data/` / `tests/`.
4. Update this prompt when first evaluation workflow is added.
