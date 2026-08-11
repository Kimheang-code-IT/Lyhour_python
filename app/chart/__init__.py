"""Reusable engineering charts for pages across the app.

Import charts from here so any page can reuse the same drawing logic:

    from app.chart import (
        MatplotlibChartWidget,
        draw_dcp_depth_vs_blows,
        draw_dcp_depth_vs_cbr,
        draw_cbr_equivalent_profile,
        draw_superelevation_profile,
        draw_simple_curve_diagram,
    )
"""

from app.chart.base import MatplotlibChartWidget, apply_axes_theme, draw_empty_message, make_matplotlib_chart
from app.chart.cbr_equivalent import draw_cbr_equivalent_profile
from app.chart.cross_section import draw_cross_section
from app.chart.dcp import draw_dcp_depth_vs_blows, draw_dcp_depth_vs_cbr
from app.chart.pavement_catalog import draw_pavement_catalog_section
from app.chart.simple_curve import draw_simple_curve_diagram
from app.chart.superelevation import (
    Y_AXIS_MAX,
    Y_AXIS_MIN,
    Y_AXIS_TICK_STEP,
    configure_superelevation_y_axis,
    draw_superelevation_profile,
    edge_elevations,
    format_y_tick,
)

__all__ = (
    "MatplotlibChartWidget",
    "Y_AXIS_MAX",
    "Y_AXIS_MIN",
    "Y_AXIS_TICK_STEP",
    "apply_axes_theme",
    "configure_superelevation_y_axis",
    "draw_cbr_equivalent_profile",
    "draw_cross_section",
    "draw_dcp_depth_vs_blows",
    "draw_dcp_depth_vs_cbr",
    "draw_empty_message",
    "draw_pavement_catalog_section",
    "draw_simple_curve_diagram",
    "draw_superelevation_profile",
    "edge_elevations",
    "format_y_tick",
    "make_matplotlib_chart",
)
