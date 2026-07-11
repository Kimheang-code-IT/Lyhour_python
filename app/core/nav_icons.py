"""Sidebar menu icons keyed by navigation route."""
from qfluentwidgets import FluentIcon

NAV_ROUTE_ICONS: dict[str, FluentIcon] = {
    # Traffic Analysis
    "traffic_analysis": FluentIcon.CAR,
    "traffic_input": FluentIcon.EDIT,
    "traffic_analysis_result": FluentIcon.PIE_SINGLE,
    # Road Geometry Design
    "road_geometry_design": FluentIcon.ALIGNMENT,
    "rgd_cross_section": FluentIcon.FIT_PAGE,
    "rgd_horizontal_curvature": FluentIcon.CONNECT,
    "rgd_superelevation_design": FluentIcon.SPEED_HIGH,
    "rgd_vertical_curve": FluentIcon.CARE_UP_SOLID,
    # Subgrade Design (main nav)
    "rgd_subgrade_design": FluentIcon.GLOBE,
    # Pavement and Material Design
    "pavement_material_design": FluentIcon.BRUSH,
    "flexible_pavement": FluentIcon.BRUSH,
    "rigid_pavement": FluentIcon.TILES,
    "material_design": FluentIcon.LIBRARY,
    "pavement_evaluation": FluentIcon.SEARCH,
    # Intersection Design
    "intersection_design": FluentIcon.LINK,
    "intersection_taper": FluentIcon.ZOOM_IN,
    "intersection_accelerations": FluentIcon.SPEED_HIGH,
    "intersection_decelerations": FluentIcon.SPEED_OFF,
}


def nav_icon(route_key: str, *, folder: bool = False) -> FluentIcon:
    """Return the menu icon for a route, with folder fallback."""
    icon = NAV_ROUTE_ICONS.get(route_key)
    if icon is not None:
        return icon
    return FluentIcon.FOLDER if folder else FluentIcon.DOCUMENT
