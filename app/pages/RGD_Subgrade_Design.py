"""Subgrade Design (DCP / CBR Equivalent / FWD)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import SegmentedWidget

from app.core.ui_style import title_style
from app.layouts import BasePage, define_page
from app.pages.Subgrade_Design.common import (
    TAB_CBR_EQUIVALENT,
    TAB_DCP,
    TAB_FWD,
    expand_vertical,
)
from app.widgets.button import secondary_button
from app.widgets.scroll_utils import ScrollStackWidget, configure_page_scroll, fit_scroll_content


@define_page("blank", title="Subgrade Design")
class RGDSubgradeDesignPage(BasePage):
    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._page_title = QLabel("Subgrade Design")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        content.addLayout(title_row)

        self.segmented = SegmentedWidget(self)
        self.segmented.setObjectName("subgradeDesignSegmented")
        self.stack = ScrollStackWidget(self)
        expand_vertical(self.stack)

        # Lazy tab pages — build only when first opened.
        self.dcp_page = None
        self.cbr_equivalent_page = None
        self.fwd_page = None

        tab_defs = (
            ("dcp", "DCP"),
            ("cbr_equivalent", "CBR Equivalent"),
            ("fwd", "FWD"),
        )
        for index, (route_key, text) in enumerate(tab_defs):
            self.segmented.addItem(
                route_key,
                text,
                onClick=lambda _=None, tab_index=index: self._set_tab(tab_index),
            )
            self.stack.addWidget(QWidget())

        content.addWidget(self.segmented)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.scroll_area.setWidget(self.stack)
        configure_page_scroll(self.scroll_area)
        content.addWidget(self.scroll_area, 1)

        self.segmented.setCurrentItem("dcp")
        self._ensure_tab(TAB_DCP)
        self.stack.setCurrentIndex(TAB_DCP)
        self._sync_scroll_for_tab(TAB_DCP)
        self._push_quick_results()

    def _replace_stack_page(self, index: int, page: QWidget) -> None:
        old = self.stack.widget(index)
        self.stack.removeWidget(old)
        if old is not None:
            old.deleteLater()
        self.stack.insertWidget(index, page)
        self.stack.setCurrentIndex(index)

    def _ensure_tab(self, index: int) -> None:
        if index == TAB_DCP:
            if self.dcp_page is not None:
                return
            from app.pages.Subgrade_Design import DcpPage

            self.dcp_page = DcpPage()
            fit_scroll_content(self.dcp_page)
            self._replace_stack_page(TAB_DCP, self.dcp_page)
            self.dcp_page.input_table.data_changed.connect(self._on_dcp_data_changed)
            return

        if index == TAB_CBR_EQUIVALENT:
            if self.cbr_equivalent_page is not None:
                return
            self._ensure_tab(TAB_DCP)
            from app.pages.Subgrade_Design import CbrPage

            self.cbr_equivalent_page = CbrPage(self.dcp_page)
            expand_vertical(self.cbr_equivalent_page)
            self._replace_stack_page(TAB_CBR_EQUIVALENT, self.cbr_equivalent_page)
            self.cbr_equivalent_page.results_changed.connect(self._push_quick_results)
            return

        if index == TAB_FWD:
            if self.fwd_page is not None:
                return
            from app.pages.Subgrade_Design import FwdPage

            self.fwd_page = FwdPage()
            fit_scroll_content(self.fwd_page)
            self._replace_stack_page(TAB_FWD, self.fwd_page)

    def _on_dcp_data_changed(self) -> None:
        if self.cbr_equivalent_page is not None:
            self.cbr_equivalent_page.refresh_analysis()
        self._push_quick_results()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._setup_quick_panel()
        self._sync_quick_panel_button()
        self._sync_scroll_for_tab(self.stack.currentIndex())

    def activate_page(self) -> None:
        self._setup_quick_panel()
        self._sync_quick_panel_button()
        self._sync_scroll_for_tab(self.stack.currentIndex())

    def _set_tab(self, index: int) -> None:
        self._ensure_tab(index)
        self.stack.setCurrentIndex(index)
        self._sync_scroll_for_tab(index)
        self._setup_quick_panel()

    def _sync_scroll_for_tab(self, index: int) -> None:
        """CBR fills the page (no scroll); other tabs scroll with hidden bars."""
        if index == TAB_CBR_EQUIVALENT and self.cbr_equivalent_page is not None:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            expand_vertical(self.stack)
            expand_vertical(self.cbr_equivalent_page)
            self.stack.setMinimumHeight(0)
            self.stack.updateGeometry()
            self.scroll_area.verticalScrollBar().setValue(0)
        else:
            configure_page_scroll(self.scroll_area)
            fit_scroll_content(self.stack)
            self.stack.updateGeometry()

    def _results(self) -> dict[str, str]:
        index = self.stack.currentIndex()
        if index == TAB_DCP and self.dcp_page is not None:
            return self.dcp_page.quick_results()
        if index == TAB_CBR_EQUIVALENT and self.cbr_equivalent_page is not None:
            return self.cbr_equivalent_page.quick_results()
        if self.fwd_page is not None:
            return self.fwd_page.quick_results()
        return {}

    def _setup_quick_panel(self) -> None:
        mw = self.window()
        if not hasattr(mw, "quick_panel"):
            return
        index = self.stack.currentIndex()
        if index == TAB_CBR_EQUIVALENT and hasattr(mw.quick_panel, "set_subgrade_cbr_equivalent_schema"):
            mw.quick_panel.set_subgrade_cbr_equivalent_schema()
        elif hasattr(mw.quick_panel, "set_subgrade_schema"):
            mw.quick_panel.set_subgrade_schema()
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
