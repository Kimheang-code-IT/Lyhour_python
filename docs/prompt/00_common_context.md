# Kickout — Common System Context

> Load this first for every task on this codebase. Then load the page-specific prompt.

## Product

- **App name:** KIEC ENGINEERING & CONSULTING
- **Type:** Desktop engineering design tool (Windows)
- **Stack:** Python 3.12 + PyQt6 + QFluentWidgets + Matplotlib
- **Domain:** Road geometry, traffic analysis, subgrade, pavement, intersection design

## Architecture (must follow)

```text
app/
  main.py                 # entry
  config/                 # APP_NAME, version
  core/                   # window, nav, theme, i18n, page_registry, quick_panel
  data/                   # CALCULATIONS ONLY (models, formulas, tables)
  chart/                  # DRAWING ONLY (reusable matplotlib charts)
  pages/                  # UI pages (compose data + chart + widgets)
  widgets/                # shared UI controls
  services/               # Excel, PDF, settings, sessions
  layouts/                # BasePage + define_page
docs/
  prompt/                 # this knowledge base
  runing.md               # run / build commands
```

### Separation rules

| Layer | Responsibility | Do not put here |
|-------|----------------|-----------------|
| `app/data/` | Pure compute, dataclasses, summaries | Qt widgets, matplotlib draw |
| `app/chart/` | Reusable `draw_*` chart logic | Business formulas |
| `app/pages/` | Layout, inputs, wiring | Duplicate formulas / chart code |
| `app/widgets/` | Generic controls | Page-specific engineering logic |

### Reusable charts

Import from `app.chart`:

```python
from app.chart import (
    MatplotlibChartWidget,
    draw_dcp_depth_vs_blows,
    draw_dcp_depth_vs_cbr,
    draw_cbr_equivalent_profile,
    draw_superelevation_profile,
    draw_simple_curve_diagram,
)
```

New charts → add under `app/chart/`, keep formulas in `app/data/`.

### Page packages (folder pattern)

Heavy multi-tab pages use folders of reusable subpages:

- `app/pages/Subgrade_Design/` → DCP, CBR, FWD
- `app/pages/Flexible_Pavement/` → Catalog/Analysis, AASHTO
- `app/pages/Analysis/` → Summary, AADT/PCU, Road Class, Lanes, ESAL

Shell pages compose those subpages (segmented tabs + quick panel).

## Navigation map

| Section | Pages |
|---------|-------|
| Traffic Analysis | Input, Analysis |
| Road Geometry Design | Cross Section, Horizontal Curvature, Superelevation, Vertical Curve |
| Subgrade Design | DCP, CBR Equivalent, FWD/BB |
| Pavement and Material Design | Flexible, Rigid, Material Design |
| Pavement Evaluation | Pavement Evaluation |
| Intersection Design | Taper, Accelerations, Decelerations |

Route keys live in `app/core/page_registry.py`.

## UI conventions

- **Theme:** dark/light via `theme_tokens()`; charts must use theme colors.
- **Quick Result panel:** fixed right panel on Horizontal Curvature, Superelevation, Subgrade Design (DCP / CBR / FWD/BB), Flexible Pavement (`FIXED_RIGHT_PANEL_PAGES`).
- **Forms:** use `make_double_spin`, `make_combo`, `add_labeled_row`, `secondary_button`.
- **Tables:** prefer `ExcelPasteTable` for paste-from-Excel inputs; style consistently.
- **Mouse wheel:** do not change spin/combo values via wheel (project convention).
- **i18n:** nav labels in `app/core/i18n.py` (EN + KM).
- **Loading:** full-window loading only for heavy ops (import/settings), not normal page navigation.
- **File menu:** session-only recent imports (no disk persist for history).

## Engineering UI tone

- Prefer engineering diagrams (stationing `16+200`, labeled dimensions, legends).
- Charts should look like design drawings, not generic dashboards.
- Keep units visible (`%`, `mm`, `m`, `km/h`, `psi`, `MPa`).

## Run & build

From project root (`D:\Lyhour_python\Win_UI`):

```powershell
.\.venv\Scripts\python.exe -m app.main
.\.venv\Scripts\python.exe scripts\check_before_build.py
.\.venv\Scripts\python.exe scripts\build_exe.py
```

EXE output: `dist\KIEC Engineering Consulting\KIEC Engineering Consulting.exe`

## Shared scroll (all pages)

- Use `configure_page_scroll(scroll)` **after** `scroll.setWidget(content)`.
- Call `fit_scroll_content(content)` so the page can grow taller than the viewport.
- **No scrollbar UI** (bars hidden); mouse-wheel / trackpad still scrolls smoothly.
- Wheel over charts/blocks is forwarded to the page scroller (tables still scroll when they need to).
- `ScrollStackWidget` when a tab stack lives inside a `QScrollArea`.

## Agent rules (global)

1. Match existing patterns before inventing new ones.
2. Prefer reuse (`app/chart`, page folders, shared widgets).
3. Do not mix calculation into UI files or drawing into `app/data`.
4. Do not expand scope beyond the requested page/feature.
5. Do not create docs the user did not ask for (except when asked, like this folder).
6. After UI/chart changes, keep theme-aware and responsive.
7. Placeholders should say clearly what will be added later.
8. Before coding a page, load this common context + that page’s prompt from `docs/prompt/`.

## Status legend (used in page prompts)

- **Implemented** — usable end-to-end
- **Partial** — core UI/logic exists; some tabs incomplete
- **Placeholder** — shell page only
