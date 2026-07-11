"""Central page indices, route keys, and navigation metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PyQt6.QtWidgets import QWidget

# --- Page indices (stack order) ---
TRAFFIC_INPUT = 0
TRAFFIC_ANALYSIS = 1
RGD_CROSS_SECTION = 2
RGD_HORIZONTAL_CURVATURE = 3
RGD_SUPERELEVATION = 4
RGD_VERTICAL_CURVE = 5
RGD_SUBGRADE_DESIGN = 6
FLEXIBLE_PAVEMENT = 7
RIGID_PAVEMENT = 8
MATERIAL_DESIGN = 9
PAVEMENT_EVALUATION = 10
INTERSECTION_TAPER = 11
INTERSECTION_ACCELERATIONS = 12
INTERSECTION_DECELERATIONS = 13

PAGE_COUNT = 14

TRAFFIC_PAGES = frozenset({TRAFFIC_INPUT, TRAFFIC_ANALYSIS})
FIXED_RIGHT_PANEL_PAGES = frozenset({
    RGD_HORIZONTAL_CURVATURE,
    RGD_SUPERELEVATION,
    RGD_SUBGRADE_DESIGN,
    FLEXIBLE_PAVEMENT,
})

ROUTE_TO_PAGE: dict[str, int] = {
    "traffic_input": TRAFFIC_INPUT,
    "traffic_analysis_result": TRAFFIC_ANALYSIS,
    "rgd_cross_section": RGD_CROSS_SECTION,
    "rgd_horizontal_curvature": RGD_HORIZONTAL_CURVATURE,
    "rgd_superelevation_design": RGD_SUPERELEVATION,
    "rgd_vertical_curve": RGD_VERTICAL_CURVE,
    "rgd_subgrade_design": RGD_SUBGRADE_DESIGN,
    "flexible_pavement": FLEXIBLE_PAVEMENT,
    "rigid_pavement": RIGID_PAVEMENT,
    "material_design": MATERIAL_DESIGN,
    "pavement_evaluation": PAVEMENT_EVALUATION,
    "intersection_taper": INTERSECTION_TAPER,
    "intersection_accelerations": INTERSECTION_ACCELERATIONS,
    "intersection_decelerations": INTERSECTION_DECELERATIONS,
}

PAGE_TO_ROUTE: dict[int, str] = {index: route for route, index in ROUTE_TO_PAGE.items()}

# Nuxt-style layout name per stack index (see app/layouts/).
PAGE_LAYOUTS: dict[int, str] = {
    TRAFFIC_INPUT: "blank",
    TRAFFIC_ANALYSIS: "blank",
    RGD_CROSS_SECTION: "default",
    RGD_HORIZONTAL_CURVATURE: "blank",
    RGD_SUPERELEVATION: "blank",
    RGD_VERTICAL_CURVE: "default",
    RGD_SUBGRADE_DESIGN: "blank",
    FLEXIBLE_PAVEMENT: "blank",
    RIGID_PAVEMENT: "default",
    MATERIAL_DESIGN: "default",
    PAVEMENT_EVALUATION: "default",
    INTERSECTION_TAPER: "default",
    INTERSECTION_ACCELERATIONS: "default",
    INTERSECTION_DECELERATIONS: "default",
}

NAV_FOLDER_ROUTE_KEYS = frozenset({
    "traffic_analysis",
    "road_geometry_design",
    "pavement_material_design",
    "intersection_design",
})

NAV_FOLDER_LABELS = frozenset({
    "Traffic Analysis",
    "Road Geometry Design",
    "Pavement and Material Design",
    "Intersection Design",
})


@dataclass(frozen=True)
class SearchPageEntry:
    route_key: str
    section_route_key: str
    index: int


SEARCH_PAGES: tuple[SearchPageEntry, ...] = (
    SearchPageEntry("traffic_input", "traffic_analysis", TRAFFIC_INPUT),
    SearchPageEntry("traffic_analysis_result", "traffic_analysis", TRAFFIC_ANALYSIS),
    SearchPageEntry("rgd_cross_section", "road_geometry_design", RGD_CROSS_SECTION),
    SearchPageEntry("rgd_horizontal_curvature", "road_geometry_design", RGD_HORIZONTAL_CURVATURE),
    SearchPageEntry("rgd_superelevation_design", "road_geometry_design", RGD_SUPERELEVATION),
    SearchPageEntry("rgd_vertical_curve", "road_geometry_design", RGD_VERTICAL_CURVE),
    SearchPageEntry("rgd_subgrade_design", "rgd_subgrade_design", RGD_SUBGRADE_DESIGN),
    SearchPageEntry("flexible_pavement", "pavement_material_design", FLEXIBLE_PAVEMENT),
    SearchPageEntry("rigid_pavement", "pavement_material_design", RIGID_PAVEMENT),
    SearchPageEntry("material_design", "pavement_material_design", MATERIAL_DESIGN),
    SearchPageEntry("pavement_evaluation", "pavement_evaluation", PAVEMENT_EVALUATION),
    SearchPageEntry("intersection_taper", "intersection_design", INTERSECTION_TAPER),
    SearchPageEntry("intersection_accelerations", "intersection_design", INTERSECTION_ACCELERATIONS),
    SearchPageEntry("intersection_decelerations", "intersection_design", INTERSECTION_DECELERATIONS),
)


def build_page_factories() -> list[Callable[[QWidget], QWidget]]:
    """Return lazy page constructors in stack index order."""
    from app.pages.Traffic_Analysis_input import TrafficAnalysisInputPage
    from app.pages.Traffic_Analysis_Detail_Result import TrafficAnalysisDetailResultPage
    from app.pages.RGD_Cross_Section import RGDCrossSectionPage
    from app.pages.RGD_Horizontal_Curvature import RGDHorizontalCurvaturePage
    from app.pages.RGD_Superelevation_Design import RGDSuperelevationDesignPage
    from app.pages.RGD_Vertical_Curve import RGDVerticalCurvePage
    from app.pages.RGD_Subgrade_Design import RGDSubgradeDesignPage
    from app.pages.Flexible_Pavement import FlexiblePavementPage
    from app.pages.Rigid_Pavement import RigidPavementPage
    from app.pages.Material_Design import MaterialDesignPage
    from app.pages.Pavement_Evaluation import PavementEvaluationPage
    from app.pages.Intersection_Taper import IntersectionTaperPage
    from app.pages.Intersection_Accelerations import IntersectionAccelerationsPage
    from app.pages.Intersection_Decelerations import IntersectionDecelerationsPage

    return [
        lambda p: TrafficAnalysisInputPage(p),
        lambda p: TrafficAnalysisDetailResultPage(p),
        lambda p: RGDCrossSectionPage(p),
        lambda p: RGDHorizontalCurvaturePage(p),
        lambda p: RGDSuperelevationDesignPage(p),
        lambda p: RGDVerticalCurvePage(p),
        lambda p: RGDSubgradeDesignPage(p),
        lambda p: FlexiblePavementPage(p),
        lambda p: RigidPavementPage(p),
        lambda p: MaterialDesignPage(p),
        lambda p: PavementEvaluationPage(p),
        lambda p: IntersectionTaperPage(p),
        lambda p: IntersectionAccelerationsPage(p),
        lambda p: IntersectionDecelerationsPage(p),
    ]
