# Prompt Knowledge Base

Use these prompts as **system knowledge** when working on KIEC Engineering Consulting (Win_UI).

## How to use

1. Always load **common (kickout) context** first:
   - [`00_common_context.md`](00_common_context.md)
2. Then load the **page prompt** for the feature you are editing.

| Page | Prompt file |
|------|-------------|
| Shared / kickout | [`00_common_context.md`](00_common_context.md) |
| Traffic Input | [`traffic_input.md`](traffic_input.md) |
| Traffic Analysis | [`traffic_analysis.md`](traffic_analysis.md) |
| Cross Section | [`rgd_cross_section.md`](rgd_cross_section.md) |
| Horizontal Curvature | [`rgd_horizontal_curvature.md`](rgd_horizontal_curvature.md) |
| Superelevation | [`rgd_superelevation.md`](rgd_superelevation.md) |
| Vertical Curve | [`rgd_vertical_curve.md`](rgd_vertical_curve.md) |
| Subgrade Design | [`rgd_subgrade_design.md`](rgd_subgrade_design.md) |
| Flexible Pavement | [`flexible_pavement.md`](flexible_pavement.md) |
| Rigid Pavement | [`rigid_pavement.md`](rigid_pavement.md) |
| Material Design | [`material_design.md`](material_design.md) |
| Pavement Evaluation | [`pavement_evaluation.md`](pavement_evaluation.md) |
| Intersection Taper | [`intersection_taper.md`](intersection_taper.md) |
| Accelerations | [`intersection_accelerations.md`](intersection_accelerations.md) |
| Decelerations | [`intersection_decelerations.md`](intersection_decelerations.md) |

## Prompt contract

Each page prompt includes:

- **Purpose** — what the page does for engineers
- **Status** — implemented / partial / placeholder
- **Route & files** — where code lives
- **Inputs / outputs** — UI fields and results
- **Charts & data** — reusable modules
- **Agent rules** — what to do / not do when editing

When adding a new page: create a matching prompt file here and add it to this index.
