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
SUBGRADE_DCP = 6
SUBGRADE_CBR = 7
SUBGRADE_FWD = 8
FLEXIBLE_PAVEMENT = 9
RIGID_PAVEMENT = 10
MATERIAL_DESIGN = 11
PAVEMENT_EVALUATION = 12
INTERSECTION_TAPER = 13
INTERSECTION_ACCELERATIONS = 14
INTERSECTION_DECELERATIONS = 15

PAGE_COUNT = 16

# Back-compat aliases
RGD_SUBGRADE_DESIGN = SUBGRADE_DCP
RIGID_MPWT = RIGID_PAVEMENT
RIGID_AASHTO = RIGID_PAVEMENT

TRAFFIC_PAGES = frozenset({TRAFFIC_INPUT, TRAFFIC_ANALYSIS})
PAGES_WITHOUT_PREVIEW = frozenset({
    TRAFFIC_INPUT,
    TRAFFIC_ANALYSIS,
    RGD_CROSS_SECTION,
})
FIXED_RIGHT_PANEL_PAGES = frozenset({
    RGD_HORIZONTAL_CURVATURE,
    RGD_SUPERELEVATION,
    RGD_VERTICAL_CURVE,
    SUBGRADE_DCP,
    SUBGRADE_CBR,
    SUBGRADE_FWD,
    FLEXIBLE_PAVEMENT,
    RIGID_PAVEMENT,
})

ROUTE_TO_PAGE: dict[str, int] = {
    "traffic_input": TRAFFIC_INPUT,
    "traffic_analysis_result": TRAFFIC_ANALYSIS,
    "rgd_cross_section": RGD_CROSS_SECTION,
    "rgd_horizontal_curvature": RGD_HORIZONTAL_CURVATURE,
    "rgd_superelevation_design": RGD_SUPERELEVATION,
    "rgd_vertical_curve": RGD_VERTICAL_CURVE,
    "subgrade_dcp": SUBGRADE_DCP,
    "subgrade_cbr_equivalent": SUBGRADE_CBR,
    "subgrade_fwd_bb": SUBGRADE_FWD,
    "flexible_pavement": FLEXIBLE_PAVEMENT,
    "rigid_pavement": RIGID_PAVEMENT,
    "material_design": MATERIAL_DESIGN,
    "pavement_evaluation": PAVEMENT_EVALUATION,
    "intersection_taper": INTERSECTION_TAPER,
    "intersection_accelerations": INTERSECTION_ACCELERATIONS,
    "intersection_decelerations": INTERSECTION_DECELERATIONS,
}

PAGE_TO_ROUTE: dict[int, str] = {index: route for route, index in ROUTE_TO_PAGE.items()}

PAGE_LAYOUTS: dict[int, str] = {
    TRAFFIC_INPUT: "blank",
    TRAFFIC_ANALYSIS: "blank",
    RGD_CROSS_SECTION: "blank",
    RGD_HORIZONTAL_CURVATURE: "blank",
    RGD_SUPERELEVATION: "blank",
    RGD_VERTICAL_CURVE: "blank",
    SUBGRADE_DCP: "blank",
    SUBGRADE_CBR: "blank",
    SUBGRADE_FWD: "blank",
    FLEXIBLE_PAVEMENT: "blank",
    RIGID_PAVEMENT: "blank",
    MATERIAL_DESIGN: "default",
    PAVEMENT_EVALUATION: "default",
    INTERSECTION_TAPER: "default",
    INTERSECTION_ACCELERATIONS: "default",
    INTERSECTION_DECELERATIONS: "default",
}

NAV_FOLDER_ROUTE_KEYS = frozenset({
    "traffic_analysis",
    "road_geometry_design",
    "subgrade_design",
    "pavement_material_design",
    "intersection_design",
})

NAV_FOLDER_LABELS = frozenset({
    "Traffic Analysis",
    "Road Geometry Design",
    "Subgrade Design",
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
    SearchPageEntry("subgrade_dcp", "subgrade_design", SUBGRADE_DCP),
    SearchPageEntry("subgrade_cbr_equivalent", "subgrade_design", SUBGRADE_CBR),
    SearchPageEntry("subgrade_fwd_bb", "subgrade_design", SUBGRADE_FWD),
    SearchPageEntry("flexible_pavement", "pavement_material_design", FLEXIBLE_PAVEMENT),
    SearchPageEntry("rigid_pavement", "pavement_material_design", RIGID_PAVEMENT),
    SearchPageEntry("material_design", "pavement_material_design", MATERIAL_DESIGN),
    SearchPageEntry("pavement_evaluation", "pavement_evaluation", PAVEMENT_EVALUATION),
    SearchPageEntry("intersection_taper", "intersection_design", INTERSECTION_TAPER),
    SearchPageEntry("intersection_accelerations", "intersection_design", INTERSECTION_ACCELERATIONS),
    SearchPageEntry("intersection_decelerations", "intersection_design", INTERSECTION_DECELERATIONS),
)


def build_page_factories() -> list[Callable[[QWidget], QWidget]]:
    def _traffic_input(parent: QWidget) -> QWidget:
        from app.pages.Traffic_Analysis_input import TrafficAnalysisInputPage

        return TrafficAnalysisInputPage(parent)

    def _traffic_analysis(parent: QWidget) -> QWidget:
        from app.pages.Traffic_Analysis_Detail_Result import TrafficAnalysisDetailResultPage

        return TrafficAnalysisDetailResultPage(parent)

    def _cross_section(parent: QWidget) -> QWidget:
        from app.pages.RGD_Cross_Section import RGDCrossSectionPage

        return RGDCrossSectionPage(parent)

    def _horizontal(parent: QWidget) -> QWidget:
        from app.pages.RGD_Horizontal_Curvature import RGDHorizontalCurvaturePage

        return RGDHorizontalCurvaturePage(parent)

    def _superelevation(parent: QWidget) -> QWidget:
        from app.pages.RGD_Superelevation_Design import RGDSuperelevationDesignPage

        return RGDSuperelevationDesignPage(parent)

    def _vertical(parent: QWidget) -> QWidget:
        from app.pages.RGD_Vertical_Curve import RGDVerticalCurvePage

        return RGDVerticalCurvePage(parent)

    def _subgrade_dcp(parent: QWidget) -> QWidget:
        from app.pages.Subgrade_DCP import SubgradeDcpPage

        return SubgradeDcpPage(parent)

    def _subgrade_cbr(parent: QWidget) -> QWidget:
        from app.pages.Subgrade_CBR import SubgradeCbrPage

        return SubgradeCbrPage(parent)

    def _subgrade_fwd(parent: QWidget) -> QWidget:
        from app.pages.Subgrade_FWD import SubgradeFwdPage

        return SubgradeFwdPage(parent)

    def _flexible(parent: QWidget) -> QWidget:
        from app.pages.Flexible_Pavement import FlexiblePavementPage

        return FlexiblePavementPage(parent)

    def _rigid(parent: QWidget) -> QWidget:
        from app.pages.Rigid_Pavement import RigidPavementPage

        return RigidPavementPage(parent)

    def _material(parent: QWidget) -> QWidget:
        from app.pages.Material_Design import MaterialDesignPage

        return MaterialDesignPage(parent)

    def _pavement_eval(parent: QWidget) -> QWidget:
        from app.pages.Pavement_Evaluation import PavementEvaluationPage

        return PavementEvaluationPage(parent)

    def _taper(parent: QWidget) -> QWidget:
        from app.pages.Intersection_Taper import IntersectionTaperPage

        return IntersectionTaperPage(parent)

    def _accel(parent: QWidget) -> QWidget:
        from app.pages.Intersection_Accelerations import IntersectionAccelerationsPage

        return IntersectionAccelerationsPage(parent)

    def _decel(parent: QWidget) -> QWidget:
        from app.pages.Intersection_Decelerations import IntersectionDecelerationsPage

        return IntersectionDecelerationsPage(parent)

    return [
        _traffic_input,
        _traffic_analysis,
        _cross_section,
        _horizontal,
        _superelevation,
        _vertical,
        _subgrade_dcp,
        _subgrade_cbr,
        _subgrade_fwd,
        _flexible,
        _rigid,
        _material,
        _pavement_eval,
        _taper,
        _accel,
        _decel,
    ]
