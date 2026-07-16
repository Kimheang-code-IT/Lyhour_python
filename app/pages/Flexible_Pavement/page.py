"""Pavement and Material Design > Flexible Pavement."""
from __future__ import annotations

from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import SegmentedWidget

from app.core.ui_style import title_style
from app.layouts import BasePage, define_page
from app.pages.Flexible_Pavement.common import TAB_AASHTO, TAB_CATALOG
from app.widgets.button import secondary_button


@define_page("blank", title="Flexible Pavement")
class FlexiblePavementPage(BasePage):
    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._page_title = QLabel("Flexible Pavement")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        content.addLayout(title_row)

        self.segmented = SegmentedWidget(self)
        self.segmented.setObjectName("flexiblePavementSegmented")
        self.stack = QStackedWidget(self)
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.catalog_page = None
        self.aashto_page = None

        tab_defs = (
            ("catalog_analysis", "Catalog/Analysis"),
            ("aashto", "AASHTO"),
        )
        for index, (route_key, text) in enumerate(tab_defs):
            self.segmented.addItem(
                route_key,
                text,
                onClick=lambda _=None, tab_index=index: self._set_tab(tab_index),
            )
            self.stack.addWidget(QWidget())

        content.addWidget(self.segmented)
        content.addWidget(self.stack, 1)

        self.segmented.setCurrentItem("catalog_analysis")
        self._ensure_tab(TAB_CATALOG)
        self.stack.setCurrentIndex(TAB_CATALOG)
        self._push_quick_results()

    def _replace_stack_page(self, index: int, page: QWidget) -> None:
        old = self.stack.widget(index)
        self.stack.removeWidget(old)
        if old is not None:
            old.deleteLater()
        self.stack.insertWidget(index, page)
        self.stack.setCurrentIndex(index)

    def _ensure_tab(self, index: int) -> None:
        if index == TAB_CATALOG:
            if self.catalog_page is not None:
                return
            from app.pages.Flexible_Pavement.catalog_analysis import CatalogAnalysisPage

            self.catalog_page = CatalogAnalysisPage()
            self._replace_stack_page(TAB_CATALOG, self.catalog_page)
            self.catalog_page.connect_inputs_changed(self._push_quick_results)
            return

        if index == TAB_AASHTO:
            if self.aashto_page is not None:
                return
            from app.pages.Flexible_Pavement.aashto import AashtoPage

            self.aashto_page = AashtoPage()
            self._replace_stack_page(TAB_AASHTO, self.aashto_page)
            self.aashto_page.connect_inputs_changed(self._push_quick_results)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def activate_page(self) -> None:
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def _set_tab(self, index: int) -> None:
        self._ensure_tab(index)
        self.stack.setCurrentIndex(index)
        self._setup_quick_panel()

    def _results(self) -> dict[str, str]:
        if self.stack.currentIndex() == TAB_AASHTO and self.aashto_page is not None:
            return self.aashto_page.quick_results()
        if self.catalog_page is not None:
            return self.catalog_page.quick_results()
        return {}

    def _setup_quick_panel(self) -> None:
        mw = self.window()
        if not hasattr(mw, "quick_panel"):
            return
        index = self.stack.currentIndex()
        if index == TAB_CATALOG and hasattr(mw.quick_panel, "set_flexible_catalog_schema"):
            mw.quick_panel.set_flexible_catalog_schema()
        elif hasattr(mw.quick_panel, "set_flexible_pavement_schema"):
            mw.quick_panel.set_flexible_pavement_schema()
        mw.quick_panel.set_results(self._results())

    def _push_quick_results(self) -> None:
        self._setup_quick_panel()

    def _toggle_quick_panel(self) -> None:
        mw = self.window()
        if hasattr(mw, "toggle_quick_panel"):
            self.sync_quick_panel_button(mw.toggle_quick_panel())

    def sync_quick_panel_button(self, visible: bool | None = None) -> None:
        if visible is None:
            mw = self.window()
            visible = hasattr(mw, "is_quick_panel_visible") and mw.is_quick_panel_visible()
        self.quick_panel_btn.setText("Hide Quick Result" if visible else "Show Quick Result")

    def _sync_quick_panel_button(self) -> None:
        self.sync_quick_panel_button()
