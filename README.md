# Traffic & Road Engineering Desktop Suite

A Windows desktop application for road and traffic engineering, built for
**KIEC Engineering Consulting**. It provides dedicated analysis pages for traffic
counting, pavement design and intersection geometry, with Excel and PDF export and
packaged delivery through PyInstaller.

## Stack

| Area | Technology |
| --- | --- |
| GUI | PyQt6, PyQt6-Fluent-Widgets, qtawesome |
| Numerics | NumPy, pandas |
| Plotting | pyqtgraph, Matplotlib |
| Export | openpyxl, xlsxwriter, ReportLab, PyMuPDF |
| Caching | diskcache, cachetools |
| Logging | loguru |
| Packaging | PyInstaller |
| Tests | pytest |

## Analysis pages

| Page | Purpose |
| --- | --- |
| Traffic Input | Raw vehicle count entry |
| Traffic Analysis | AADT, PCU and ESAL computations |
| Cross Section | Geometric cross-section design |
| Horizontal Curvature | Curve radius and transition design |
| Superelevation | Cross-slope design |
| Vertical Curve | Sag and crest curve geometry |
| Subgrade Design | Subgrade strength and required pavement structure |
| Flexible Pavement | Flexible pavement thickness design |
| Rigid Pavement | Rigid pavement slab design |
| Material Design | Material strength and mix design |
| Pavement Evaluation | Existing pavement condition evaluation |
| Intersection Taper | Taper and corner design |
| Accelerations / Decelerations | Speed-change and deceleration criteria |

## Repository layout

```text
app/            Application code
  pages/        One module per analysis page (Analysis/ and road-design pages)
docs/           Project documentation and per-page agent prompts
scripts/        Helper scripts
tests/          pytest suite
requirements.txt
```

`docs/prompt/` holds per-page knowledge-base prompts used with AI assistants.
Start from `docs/prompt/PROJECT_OVERVIEW.md`, then load the page-specific prompt for
the feature you are editing.

## Running

```bash
pip install -r requirements.txt
python main.py
```

## Tests

```bash
pytest
```

## Packaging

```bash
pyinstaller --noconfirm your_entrypoint.spec
```
