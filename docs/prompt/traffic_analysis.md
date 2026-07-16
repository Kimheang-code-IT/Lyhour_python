# Page Prompt — Traffic Analysis (Detail Result)

> Load after [`00_common_context.md`](00_common_context.md).

## Purpose

Show computed traffic analysis results from Input data: summary counts, AADT/PCU, road classification, number of lanes, ESAL.

## Status

**Implemented** (segmented analysis subpages).

## Route & files

| Item | Value |
|------|--------|
| Route key | `traffic_analysis_result` |
| Stack index | `TRAFFIC_ANALYSIS` |
| Shell page | `app/pages/Traffic_Analysis_Detail_Result.py` |
| Subpages folder | `app/pages/Analysis/` |

### Subpages

| Tab | File | Role |
|-----|------|------|
| Summary Traffic count data | `summary_traffic_count.py` | Count summary |
| AADT && PCU | `aadt_pcu.py` | AADT / PCU tables & charts |
| Road Classification | `road_classification.py` | Class from traffic |
| Number of Lane | `number_of_lane.py` | Lane projection + result table |
| ESAL | `esal.py` | ESAL axle tables / design period |

Related data: `app/data/road_classification.py`, `app/data/level_of_service.py`, `app/services/traffic_lane_projection.py`.

## UI structure

- SegmentedWidget tabs + QStackedWidget (same pattern as Subgrade / Flexible)
- Quick Result button on shell
- Theme refresh via `refresh_theme_widgets`

## Agent rules

1. Put new analysis views as files under `app/pages/Analysis/`, then register in the shell.
2. Keep tab text careful with `&` (Fluent uses `&&` to show `&`).
3. Reuse existing traffic result widgets/services; do not duplicate projection math in the shell.
4. If adding charts, place draw logic in `app/chart/` and compute in `app/data/` or `app/services/`.
5. Number of Lane bottom table should stay consistent with AADT/PCU table styling.
