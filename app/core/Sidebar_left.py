"""Left navigation built with QFluentWidgets NavigationInterface."""

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QSizePolicy

from qfluentwidgets import FluentIcon, NavigationInterface, NavigationItemPosition


class SidebarLeft(QFrame):
    """Left navigation; emits pageChanged(int) and toggleRequested."""

    pageChanged = pyqtSignal(int)
    toggleRequested = pyqtSignal()

    _ROUTE_TO_PAGE = {
        "traffic_input": 0,
        "traffic_detail_result": 1,
        "rgd_horizontal_curvature": 2,
        "rgd_superelevation_design": 3,
    }
    _PAGE_TO_ROUTE = {page: route for route, page in _ROUTE_TO_PAGE.items()}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navPanel")
        self.setMinimumWidth(300)
        self.setMaximumWidth(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet("""
            #navPanel {
                background-color: #2d2d30;
                border: none;
                border-right: 1px solid #3a3a3d;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.navigation = NavigationInterface(
            self,
            showMenuButton=False,
            showReturnButton=False,
            collapsible=False,
        )
        self.navigation.setObjectName("leftNavigationInterface")
        self.navigation.setMinimumWidth(300)
        self.navigation.setExpandWidth(300)
        self.navigation.setMinimumExpandWidth(0)
        self.navigation.setAcrylicEnabled(False)
        self.navigation.expand(True)
        self.navigation.setStyleSheet("""
            NavigationInterface,
            NavigationPanel {
                background-color: #2d2d30;
                border: none;
            }
            NavigationItemHeader {
                color: #b5bac8;
                font-size: 13px;
                font-weight: 500;
                padding-left: 20px;
                padding-top: 10px;
                padding-bottom: 6px;
            }
            NavigationTreeWidget,
            NavigationTreeItem,
            NavigationToolButton {
                color: #ffffff;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                min-height: 44px;
                font-size: 16px;
            }
        """)

        layout.addWidget(self.navigation, 1)
        self._build_navigation()
        QTimer.singleShot(0, self._apply_default_state)

    def _build_navigation(self) -> None:
        self.navigation.addItemHeader("Analysis", NavigationItemPosition.TOP)
        self.navigation.addItem(
            routeKey="traffic_analysis",
            icon=FluentIcon.FOLDER,
            text="Traffic Analysis",
            selectable=False,
            position=NavigationItemPosition.TOP,
        )
        self.navigation.addItem(
            routeKey="traffic_input",
            icon=FluentIcon.DOCUMENT,
            text="Input",
            onClick=lambda: self.pageChanged.emit(0),
            parentRouteKey="traffic_analysis",
        )
        self.navigation.addItem(
            routeKey="traffic_detail_result",
            icon=FluentIcon.DOCUMENT,
            text="Detail Result",
            onClick=lambda: self.pageChanged.emit(1),
            parentRouteKey="traffic_analysis",
        )

        self.navigation.addItemHeader("Design", NavigationItemPosition.TOP)
        self.navigation.addItem(
            routeKey="road_geometry_design",
            icon=FluentIcon.FOLDER,
            text="Road Geometry Design",
            selectable=False,
            position=NavigationItemPosition.TOP,
        )
        self.navigation.addItem(
            routeKey="rgd_horizontal_curvature",
            icon=FluentIcon.DOCUMENT,
            text="Horizontal Curvature",
            onClick=lambda: self.pageChanged.emit(2),
            parentRouteKey="road_geometry_design",
        )
        self.navigation.addItem(
            routeKey="rgd_superelevation_design",
            icon=FluentIcon.DOCUMENT,
            text="Superelevation Design",
            onClick=lambda: self.pageChanged.emit(3),
            parentRouteKey="road_geometry_design",
        )

    def _apply_default_state(self) -> None:
        self.navigation.expand(True)
        for child in self.navigation.findChildren(object):
            if type(child).__name__ != "NavigationTreeWidget":
                continue
            if not hasattr(child, "text") or not hasattr(child, "setExpanded"):
                continue
            try:
                if child.text() in {"Traffic Analysis", "Road Geometry Design"}:
                    if hasattr(child, "setRememberExpandState"):
                        child.setRememberExpandState(False)
                    child.setExpanded(True)
            except Exception:
                continue
        self.navigation.setCurrentItem("traffic_input")

    def set_current_index(self, index: int):
        route_key = self._PAGE_TO_ROUTE.get(index)
        if route_key:
            self._apply_default_state()
            self.navigation.setCurrentItem(route_key)