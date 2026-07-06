"""Left navigation built with QFluentWidgets NavigationInterface."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QApplication, QFrame, QSizePolicy, QVBoxLayout

from qfluentwidgets import NavigationInterface, NavigationItemPosition
from qfluentwidgets.components.navigation.navigation_widget import NavigationTreeWidget, NavigationWidget
from qfluentwidgets.components.widgets.scroll_bar import ScrollBarHandleDisplayMode

from app.core.i18n import nav_label
from app.core.nav_icons import nav_icon
from app.core.theme import shell_stylesheet, theme_tokens
from app.core.page_registry import (
    FLEXIBLE_PAVEMENT,
    INTERSECTION_ACCELERATIONS,
    INTERSECTION_DECELERATIONS,
    INTERSECTION_TAPER,
    MATERIAL_DESIGN,
    NAV_FOLDER_ROUTE_KEYS,
    PAGE_TO_ROUTE,
    PAVEMENT_EVALUATION,
    RIGID_PAVEMENT,
    RGD_CROSS_SECTION,
    RGD_HORIZONTAL_CURVATURE,
    RGD_SUPERELEVATION,
    RGD_VERTICAL_CURVE,
    TRAFFIC_ANALYSIS,
    TRAFFIC_INPUT,
)

_MIN_SIDEBAR_WIDTH = 250
_MAX_SIDEBAR_WIDTH = 320
_ICON_TEXT_PADDING = 80


class SidebarLeft(QFrame):
    """Left navigation; emits pageChanged(int) and toggleRequested."""

    pageChanged = pyqtSignal(int)
    toggleRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sidebar_width = _MIN_SIDEBAR_WIDTH
        self.setObjectName("navPanel")
        self._apply_sidebar_width(self._sidebar_width)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

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
        self.navigation.setMinimumWidth(self._sidebar_width)
        self.navigation.setExpandWidth(self._sidebar_width)
        self.navigation.setMinimumExpandWidth(0)
        self.navigation.setAcrylicEnabled(False)
        self.navigation.expand(True)

        layout.addWidget(self.navigation, 1)
        self._build_navigation()
        self._configure_navigation_panel()
        QTimer.singleShot(0, self._apply_default_state)
        self.apply_theme()

    def apply_theme(self) -> None:
        tokens = theme_tokens()
        nav_extra = f"""
            NavigationItemHeader {{
                padding-left: 16px;
                padding-top: 4px;
                padding-bottom: 2px;
            }}
            NavigationTreeWidget, NavigationTreeItem, NavigationToolButton {{
                border-radius: 4px;
                min-height: 36px;
                max-height: 36px;
                font-size: 14px;
            }}
        """
        self.setStyleSheet(shell_stylesheet(tokens) + nav_extra)
        self.navigation.setStyleSheet(shell_stylesheet(tokens) + nav_extra)

    def _scroll_position(self) -> NavigationItemPosition:
        return NavigationItemPosition.SCROLL

    def _apply_sidebar_width(self, width: int) -> None:
        self._sidebar_width = max(_MIN_SIDEBAR_WIDTH, min(_MAX_SIDEBAR_WIDTH, width))
        self.setMinimumWidth(self._sidebar_width)
        self.setMaximumWidth(self._sidebar_width)
        if not hasattr(self, "navigation"):
            return
        self.navigation.setMinimumWidth(self._sidebar_width)
        self.navigation.setExpandWidth(self._sidebar_width)
        NavigationWidget.EXPAND_WIDTH = self._sidebar_width - 10
        panel = self.navigation.panel
        panel.setExpandWidth(self._sidebar_width)

    def _compute_sidebar_width(self) -> int:
        app = QApplication.instance()
        font = app.font() if app is not None else QFont()
        metrics = QFontMetrics(font)
        panel = self.navigation.panel
        max_row = 0
        for route_key in panel.items:
            try:
                widget = panel.widget(route_key)
            except Exception:
                continue
            depth = getattr(widget, "nodeDepth", 0)
            indent = depth * 28 + _ICON_TEXT_PADDING
            text_width = metrics.horizontalAdvance(nav_label(route_key))
            max_row = max(max_row, indent + text_width)
        return max(_MIN_SIDEBAR_WIDTH, min(_MAX_SIDEBAR_WIDTH, max_row + 16))

    def _configure_navigation_panel(self) -> None:
        panel = self.navigation.panel
        self._apply_sidebar_width(self._sidebar_width)
        panel.scrollLayout.setSpacing(0)
        panel.scrollLayout.setContentsMargins(4, 0, 4, 0)
        panel.vBoxLayout.setSpacing(0)
        panel.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        scroll = panel.scrollArea
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.scrollDelagate.vScrollBar.setHandleDisplayMode(ScrollBarHandleDisplayMode.ON_HOVER)

        menu_font = QFont()
        menu_font.setPointSize(10)
        for item in panel.items.values():
            item.widget.setFont(menu_font)
            if hasattr(item.widget, "itemWidget"):
                item.widget.itemWidget.setFont(menu_font)

    def _refresh_navigation_layout(self) -> None:
        panel = self.navigation.panel
        panel.scrollWidget.adjustSize()
        panel.scrollWidget.updateGeometry()
        panel.scrollArea.updateGeometry()

    def _navigate_to(self, page_index: int) -> None:
        self.pageChanged.emit(page_index)

    def _add_page_item(
        self,
        *,
        route_key: str,
        text: str,
        page_index: int,
        parent_route_key: str,
    ) -> None:
        self.navigation.addItem(
            routeKey=route_key,
            icon=nav_icon(route_key),
            text=text,
            onClick=lambda *_args, index=page_index: self._navigate_to(index),
            parentRouteKey=parent_route_key,
        )

    def _add_folder(self, *, route_key: str, text: str, default_page_index: int | None = None) -> None:
        on_click = None
        if default_page_index is not None:
            on_click = lambda *_args, index=default_page_index: self._navigate_to(index)
        self.navigation.addItem(
            routeKey=route_key,
            icon=nav_icon(route_key, folder=True),
            text=text,
            selectable=False,
            onClick=on_click,
            position=self._scroll_position(),
        )

    def _build_navigation(self) -> None:
        scroll = self._scroll_position()
        self._add_folder(
            route_key="traffic_analysis",
            text=nav_label("traffic_analysis"),
            default_page_index=TRAFFIC_INPUT,
        )
        self._add_page_item(
            route_key="traffic_input",
            text=nav_label("traffic_input"),
            page_index=TRAFFIC_INPUT,
            parent_route_key="traffic_analysis",
        )
        self._add_page_item(
            route_key="traffic_analysis_result",
            text=nav_label("traffic_analysis_result"),
            page_index=TRAFFIC_ANALYSIS,
            parent_route_key="traffic_analysis",
        )

        self._add_folder(
            route_key="road_geometry_design",
            text=nav_label("road_geometry_design"),
            default_page_index=RGD_CROSS_SECTION,
        )
        self._add_page_item(
            route_key="rgd_cross_section",
            text=nav_label("rgd_cross_section"),
            page_index=RGD_CROSS_SECTION,
            parent_route_key="road_geometry_design",
        )
        self._add_page_item(
            route_key="rgd_horizontal_curvature",
            text=nav_label("rgd_horizontal_curvature"),
            page_index=RGD_HORIZONTAL_CURVATURE,
            parent_route_key="road_geometry_design",
        )
        self._add_page_item(
            route_key="rgd_superelevation_design",
            text=nav_label("rgd_superelevation_design"),
            page_index=RGD_SUPERELEVATION,
            parent_route_key="road_geometry_design",
        )
        self._add_page_item(
            route_key="rgd_vertical_curve",
            text=nav_label("rgd_vertical_curve"),
            page_index=RGD_VERTICAL_CURVE,
            parent_route_key="road_geometry_design",
        )

        self._add_folder(
            route_key="pavement_material_design",
            text=nav_label("pavement_material_design"),
            default_page_index=FLEXIBLE_PAVEMENT,
        )
        self._add_page_item(
            route_key="flexible_pavement",
            text=nav_label("flexible_pavement"),
            page_index=FLEXIBLE_PAVEMENT,
            parent_route_key="pavement_material_design",
        )
        self._add_page_item(
            route_key="rigid_pavement",
            text=nav_label("rigid_pavement"),
            page_index=RIGID_PAVEMENT,
            parent_route_key="pavement_material_design",
        )
        self._add_page_item(
            route_key="material_design",
            text=nav_label("material_design"),
            page_index=MATERIAL_DESIGN,
            parent_route_key="pavement_material_design",
        )

        self.navigation.addItem(
            routeKey="pavement_evaluation",
            icon=nav_icon("pavement_evaluation"),
            text=nav_label("pavement_evaluation"),
            onClick=lambda *_args: self._navigate_to(PAVEMENT_EVALUATION),
            position=scroll,
        )

        self._add_folder(
            route_key="intersection_design",
            text=nav_label("intersection_design"),
            default_page_index=INTERSECTION_TAPER,
        )
        self._add_page_item(
            route_key="intersection_taper",
            text=nav_label("intersection_taper"),
            page_index=INTERSECTION_TAPER,
            parent_route_key="intersection_design",
        )
        self._add_page_item(
            route_key="intersection_accelerations",
            text=nav_label("intersection_accelerations"),
            page_index=INTERSECTION_ACCELERATIONS,
            parent_route_key="intersection_design",
        )
        self._add_page_item(
            route_key="intersection_decelerations",
            text=nav_label("intersection_decelerations"),
            page_index=INTERSECTION_DECELERATIONS,
            parent_route_key="intersection_design",
        )

    def _apply_default_state(self) -> None:
        self.navigation.expand(True)
        panel = self.navigation.panel
        for route_key in NAV_FOLDER_ROUTE_KEYS:
            try:
                widget = panel.widget(route_key)
            except Exception:
                continue
            if hasattr(widget, "setExpanded"):
                widget.setExpanded(True, ani=False)

        self._apply_sidebar_width(self._compute_sidebar_width())
        self._configure_navigation_panel()
        self._refresh_navigation_layout()
        self.navigation.setCurrentItem("traffic_input")

    def _capture_folder_expand_state(self) -> dict[str, bool]:
        panel = self.navigation.panel
        state: dict[str, bool] = {}
        for route_key in NAV_FOLDER_ROUTE_KEYS:
            try:
                widget = panel.widget(route_key)
            except Exception:
                continue
            state[route_key] = bool(getattr(widget, "isExpanded", True))
        return state

    def _force_tree_resize(self, widget: NavigationTreeWidget) -> None:
        widget.setFixedSize(widget.sizeHint())
        parent = widget.treeParent
        while parent is not None:
            parent.setFixedSize(parent.sizeHint())
            parent = parent.treeParent

    def _relayout_navigation_tree(self) -> None:
        panel = self.navigation.panel
        current_route = panel._currentRouteKey
        folder_state = self._capture_folder_expand_state()

        for route_key in panel.items:
            try:
                widget = panel.widget(route_key)
            except Exception:
                continue
            if hasattr(widget, "setText"):
                widget.setText(nav_label(route_key))

        tree_widgets = [
            panel.widget(route_key)
            for route_key in panel.items
            if isinstance(panel.widget(route_key), NavigationTreeWidget)
        ]
        tree_widgets.sort(key=lambda w: w.nodeDepth, reverse=True)
        for widget in tree_widgets:
            self._force_tree_resize(widget)

        for route_key, expanded in folder_state.items():
            try:
                widget = panel.widget(route_key)
            except Exception:
                continue
            if not hasattr(widget, "setExpanded"):
                continue
            if expanded:
                widget.isExpanded = False
                widget.setExpanded(True, ani=False)
            else:
                widget.isExpanded = True
                widget.setExpanded(False, ani=False)

        self._apply_sidebar_width(self._compute_sidebar_width())
        self._configure_navigation_panel()
        self.navigation.expand(True)
        self._refresh_navigation_layout()

        if current_route and current_route in panel.items:
            panel.setCurrentItem(current_route)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_navigation_layout()

    def set_current_index(self, index: int) -> None:
        route_key = PAGE_TO_ROUTE.get(index)
        if route_key:
            self.navigation.setCurrentItem(route_key)

    def retranslate_ui(self) -> None:
        self.apply_theme()
        self._relayout_navigation_tree()
