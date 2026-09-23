# KIEC Engineering Consulting — Project Overview

> Single-file context for AI assistants (ChatGPT, Claude, Copilot). Read this top
> to bottom to understand the whole app. Detailed per-page notes live in
> [`docs/prompt/`](prompt/) — this file is the consolidated summary.

---

## 1. What this app is

A **Windows desktop engineering design tool** for road/highway and pavement
design. It is used by civil engineers to run standard calculations (traffic
analysis, road geometry, subgrade, flexible/rigid pavement, intersections),
view engineering diagrams, and export PDF reports.

- **Product name:** KIEC ENGINEERING & CONSULTING
- **Version:** 1.0.0 (`app/config/settings.py`)
- **Type:** Offline desktop GUI (no web server, no database)
- **Project file extension:** `.bcproj` (JSON)

---

## 2. Tech stack

| Area | Technology |
|------|------------|
| Language | Python 3.12 |
| GUI framework | PyQt6 6.6.1 |
| UI theme/widgets | PyQt6-Fluent-Widgets (qfluentwidgets) |
| Icons | qtawesome |
| Charts | Matplotlib (QtAgg backend) + pyqtgraph |
| Data | numpy, pandas |
| Excel I/O | openpyxl, xlsxwriter |
| PDF | reportlab, PyMuPDF (pymupdf) |
| Caching | diskcache, cachetools |
| Logging | loguru |
| Packaging | PyInstaller |

Full list: [`requirements.txt`](../requirements.txt).

---

## 3. Run & build (Windows / PowerShell)

Run **from the project root** (package imports like `app.core...` require it):

```powershell
# Run the app
.\.venv\Scripts\python.exe -m app.main

# Pre-build check
.\.venv\Scripts\python.exe scripts\check_before_build.py

# Build the EXE
.\.venv\Scripts\python.exe scripts\build_exe.py
```

- EXE output: `dist\KIEC Engineering Consulting\KIEC Engineering Consulting.exe`
- Entry point: `app/main.py`
- Tests: `python -m pytest tests` (plain `test_*.py` functions)

---

## 4. Architecture (important)

The project follows a **strict layered separation**. Respect it when adding code.

```text
app/
  main.py        # entry point: QApplication, theme, MainWindow
  config/        # APP_NAME, version, shortcuts, topbar actions
  core/          # window, sidebar, topbar, theme, i18n, page_registry,
                 # quick_panel, preview_panel, search, ui_scale
  data/          # CALCULATIONS ONLY — dataclasses, formulas, lookup tables
  chart/         # DRAWING ONLY — reusable matplotlib draw_* functions
  pages/         # UI pages (compose data + chart + widgets)
  widgets/       # shared reusable UI controls
  services/      # Excel, PDF, settings, sessions, report generation
  layouts/       # BasePage + define_page (Nuxt-style layout slots)
docs/
  prompt/        # per-page knowledge base (load 00_common_context.md first)
scripts/         # build + pre-build checks
tests/           # pytest tests for data modules
```

### Layer rules

| Layer | Put here | Never put here |
|-------|----------|----------------|
| `app/data/` | Pure compute, dataclasses, tables, summaries | Qt widgets, matplotlib |
| `app/chart/` | Reusable `draw_*` chart logic | Business formulas |
| `app/pages/` | Layout, inputs, wiring | Duplicated formulas/charts |
| `app/widgets/` | Generic controls | Page-specific engineering logic |
| `app/services/` | Excel/PDF/session side effects | Engineering formulas |

**Golden rule:** calculations live in `app/data/`, drawing lives in
`app/chart/`, pages only wire them together.

---

## 5. Layout & page system

Pages subclass `BasePage` and declare a layout with `@define_page`:

```python
from app.layouts import BasePage, define_page

@define_page("default", title="My Page")
class MyPage(BasePage):
    def setup(self, content):        # content is a QVBoxLayout slot
        content.addWidget(...)
```

Available layouts: `default` (title + content), `blank` (no chrome),
`scroll` (scrollable content). Layout registry: `app/layouts/registry.py`.

### Page registry — `app/core/page_registry.py`

Central source of truth for stack indices, route keys, and right-panel behavior.

| Index | Route key | Page | Layout |
|------:|-----------|------|--------|
| 0 | `traffic_input` | Traffic Input | blank |
| 1 | `traffic_analysis_result` | Traffic Analysis | blank |
| 2 | `rgd_cross_section` | Cross Section | blank |
| 3 | `rgd_horizontal_curvature` | Horizontal Curvature | blank |
| 4 | `rgd_superelevation_design` | Superelevation | blank |
| 5 | `rgd_vertical_curve` | Vertical Curve | blank |
| 6 | `subgrade_dcp` | Subgrade DCP | blank |
| 7 | `subgrade_cbr_equivalent` | CBR Equivalent | blank |
| 8 | `subgrade_fwd_bb` | FWD/BB | blank |
| 9 | `flexible_pavement` | Flexible Pavement | blank |
| 10 | `rigid_pavement` | Rigid Pavement | blank |
| 11 | `material_design` | Material Design | default |
| 12 | `pavement_evaluation` | Pavement Evaluation | default |
| 13 | `intersection_taper` | Taper | default |
| 14 | `intersection_accelerations` | Accelerations | default |
| 15 | `intersection_decelerations` | Decelerations | default |

Special sets:
- `FIXED_RIGHT_PANEL_PAGES` — pages with a fixed right **Quick Result** panel
  (Horizontal Curvature, Superelevation, Vertical Curve, all Subgrade pages,
  Flexible Pavement, Rigid Pavement).
- `PAGES_WITHOUT_PREVIEW` — pages where the right preview panel is hidden
  (Traffic pages, Cross Section, Pavement Evaluation).
- `TRAFFIC_PAGES` — Traffic Input + Analysis.

### Main window — `app/core/main_window.py`

Three columns: **left sidebar** (`Sidebar_left.py`) → **center page stack** →
**right panel** (`quick_panel.py` or `preview_panel.py`). Pages are lazy-loaded
via factories (`build_page_factories()`).

---

## 6. Navigation map (sidebar)

| Section | Pages |
|---------|-------|
| Traffic Analysis | Input, Analysis |
| Road Geometry Design | Cross Section, Horizontal Curvature, Superelevation, Vertical Curve |
| Subgrade Design | DCP, CBR Equivalent, FWD/BB (indented sub-items) |
| Pavement and Material Design | Flexible Pavement, Rigid Pavement, Material Design |
| Pavement Evaluation | Pavement Evaluation |
| Intersection Design | Taper, Accelerations, Decelerations |

Nav labels are localized (English + Khmer) in `app/core/i18n.py`.

---

## 7. Features by page (status)

Legend: **Implemented** = usable end-to-end · **Partial** = core exists, some
tabs incomplete · **Placeholder** = shell only.

| Page | Status | Summary |
|------|--------|---------|
| Traffic Input | Implemented | Excel import + manual traffic entry (count hours, area type, design year, growth, LOS) |
| Traffic Analysis | Implemented | Summary counts, AADT/PCU, road classification, number of lanes, ESAL (segmented tabs) |
| Cross Section | Partial | Input + live design cross-section diagram (lanes, shoulders, median, slopes) |
| Horizontal Curvature | Implemented | R_min from speed/e/f tables, verification, simple-curve diagram, Geometric Summary + Stakeout tabs |
| Superelevation | Implemented | Full superelevation graph (Tro, Sro, Le, Lc) with edge-transition profiles |
| Vertical Curve | Implemented | Equal-tangent parabolic crest/sag (K-values, PVC/PVI/PVT, sight-distance, stakeout) |
| Subgrade DCP | Implemented | DCP blows/penetration → CBR, layered CBR summary (200 mm) |
| CBR Equivalent | Implemented | Weighted CBR_eq from DCP layers or user-defined layers |
| FWD/BB | Placeholder | To be implemented (share FWD engine with Pavement Evaluation) |
| Flexible Pavement | Partial | Tabs: **Catalog**, **AASHTO** (resilient modulus), **MPWT Analysis** (thickness/SN) |
| Rigid Pavement | Implemented | Tabs: **MPWT** and **AASHTO 1993** concrete thickness design |
| Material Design | Placeholder | Material specification helpers (planned) |
| Pavement Evaluation | Implemented | Traffic-class (T1–T8) structure table with auto-filled thickness + FWD/LWD/B_Beam |
| Intersection Taper | Placeholder | Taper length geometry (planned) |
| Accelerations | Placeholder | Acceleration lane length (planned) |
| Decelerations | Placeholder | Deceleration/turning lane length (planned) |

Detailed per-page notes: [`docs/prompt/`](prompt/).

---

## 8. Data modules (`app/data/`) — the calculations

These are pure Python (no Qt) and unit-testable.

| Module | Concern |
|--------|---------|
| `tables_Horizontal_Curvature.py` | R_min formula + Table 7.5/7.6/7.7 lookups, side friction |
| `simple_curve_geometry.py` | Simple horizontal curve elements (TL, L, C, E, M) + stakeout |
| `vertical_curve.py` | Parabolic crest/sag vertical curve, K-values, sight distance, stakeout |
| `superelevation_profile.py` | Tro/Sro/Le/Lc and edge elevations, `format_station` |
| `cross_section.py` | `build_cross_section` — lanes, shoulders, median, slopes |
| `dcp_analysis.py` | DCP penetration index → CBR, layered summary |
| `cbr_equivalent.py` | Weighted `CBR_eq = Σ(CBR_i·h_i)/Σh_i` |
| `pavement_catalog.py` | Foundation × traffic → layer stack; material colors/hatches/labels |
| `aashto_resilient_modulus.py` | Monthly CBR → MR, effective roadbed resilient modulus |
| `mpwt_thickness.py` | Structural/drainage coefficients, required SN, layer SN check |
| `mpwt_rigid.py` | MPWT rigid pavement (fatigue/erosion) |
| `aashto_rigid.py` | AASHTO 1993 rigid pavement (effective/corrected k, D) |
| `pavement_evaluation.py` | Traffic-class evaluation table (T1–T8) + FWD/LWD/B_Beam |
| `road_classification.py` | Road class from traffic |
| `level_of_service.py`, `area_type.py` | LOS + area-type tables |

Convention: functions/`@dataclass` returning results; no printing, no Qt.

---

## 9. Chart modules (`app/chart/`) — the drawings

Import from `app.chart` (re-exported in `__init__.py`). All charts are
theme-aware via `theme_tokens()`.

| Function | Used by |
|----------|---------|
| `MatplotlibChartWidget` | Base widget embedding a matplotlib canvas |
| `draw_cross_section` | Cross Section |
| `draw_simple_curve_diagram` | Horizontal Curvature |
| `draw_superelevation_profile` | Superelevation |
| `draw_vertical_curve` | Vertical Curve |
| `draw_dcp_depth_vs_blows`, `draw_dcp_depth_vs_cbr` | Subgrade DCP |
| `draw_cbr_equivalent_profile` | CBR Equivalent |
| `draw_pavement_catalog_section` | Flexible Pavement Catalog |

`app/chart/base.py` provides `apply_axes_theme`, `draw_empty_message`,
`make_matplotlib_chart`.

---

## 10. Services (`app/services/`)

| Module | Responsibility |
|--------|----------------|
| `app_settings.py` | User preferences (theme, accent), persisted |
| `excel_io.py`, `excel_session.py` | Excel import/export + session state |
| `traffic_excel.py`, `traffic_tld_excel.py` | Traffic workbook parsing |
| `traffic_aadt_pcu.py`, `traffic_esal.py`, `traffic_lane_projection.py`, `esal_calculator.py` | Traffic computations shared by Analysis tabs |
| `traffic_quick_results.py` | Quick panel result assembly |
| `pdf_export.py`, `pdf_preview.py`, `report_generator.py` | PDF generation/preview/report |
| `file_history.py`, `import_session_utils.py` | Session-only recent imports |
| `tld_io.py` | TLD data I/O |

---

## 11. Shared widgets & UI conventions (`app/widgets/`)

| Widget/helper | Purpose |
|---------------|---------|
| `form_controls.py` | `make_combo`, `make_double_spin`, `make_radio`, `make_switch` (wheel-safe) |
| `labeled_input.py` | `add_labeled_row` — label + control grid row |
| `button.py` | `primary_button`, `secondary_button` |
| `scroll_utils.py` | `configure_page_scroll`, `fit_scroll_content` (hidden scrollbars) |
| `excel_paste_table.py` | Paste-from-Excel table |
| `loading_overlay.py`, `skeleton_screen.py` | Heavy-op loading UI |
| `settings_dialog.py`, `dialog.py` | Dialogs |
| `traffic_charts.py`, `traffic_results.py`, `traffic_summary_table.py` | Traffic-specific views |

### UI rules
- **Theme:** dark/light through `theme_tokens()`; charts must use theme colors.
- **Forms:** use the factories above — do **not** change spin/combo values with
  the mouse wheel (project convention).
- **Scroll:** call `fit_scroll_content(content)` then
  `configure_page_scroll(scroll)` after `setWidget`. Scrollbars are hidden but
  wheel/trackpad scrolling works.
- **Tables:** reuse existing styling helpers; prefer `ExcelPasteTable` for inputs.
- **Engineering tone:** charts look like design drawings (stationing `16+200`,
  labeled dimensions, legends), units always visible (`%`, `mm`, `m`, `km/h`,
  `psi`, `MPa`).

---

## 12. Theme & i18n

- `app/core/theme.py` — `theme_tokens()`, `ThemeTokens`, palette, global
  stylesheet, `apply_theme_to_app`.
- `app/core/ui_style.py` — `title_style`, `section_title_style`, `label_style`.
- `app/core/ui_scale.py` — DPI-aware `px()` / `pt()` scaling.
- `app/core/i18n.py` — nav labels English + Khmer.

---

## 13. Testing

- Tests live in `tests/` and target **data modules** (pure functions).
- Style: plain functions named `test_*` using `pytest` (no Qt needed).
- Examples: `test_simple_curve_geometry.py`, `test_pavement_catalog.py`,
  `test_pavement_evaluation.py`, `test_superelevation_profile.py`,
  `test_dcp_analysis.py`, `test_esal_calculator.py`.
- Add tests when you add formulas in `app/data/`.

---

## 14. Conventions for contributors / AI assistants

1. **Match existing patterns** before inventing new ones; prefer reuse
   (`app/chart`, page folders, shared widgets).
2. **Never mix layers** — no calculation in UI files, no drawing in `app/data`.
3. **Do not expand scope** beyond the requested page/feature.
4. After UI/chart changes, keep them **theme-aware** and responsive.
5. Keep **engineering units explicit** and round only for display.
6. Placeholders must clearly state what will be added later.
7. Before coding a page, read `docs/prompt/00_common_context.md` + that page's
   prompt in `docs/prompt/`.
8. Don't create documentation files unless asked.

---

## 15. Glossary

| Term | Meaning |
|------|---------|
| R_min | Minimum horizontal curve radius |
| SSD | Stopping sight distance |
| PVC / PVI / PVT | Vertical curve point of vertical curve / intersection / tangent |
| K-factor | Vertical curve rate `L / abs(A)` |
| TL, L, C, E, M | Horizontal curve tangent length, curve length, chord, external, middle ordinate |
| DCP | Dynamic Cone Penetrometer |
| CBR | California Bearing Ratio |
| FWD / LWD | Falling / Light Weight Deflectometer (MPa) |
| B_Beam | Benkelman Beam deflection (mm) |
| ESAL | Equivalent Single Axle Load |
| AADT / PCU | Annual Average Daily Traffic / Passenger Car Unit |
| SN | Structural Number (flexible pavement) |
| k | Modulus of subgrade reaction (rigid pavement) |
| MPWT | Ministry of Public Works and Transport (design standard) |
| AASHTO | American Association of State Highway and Transportation Officials |
