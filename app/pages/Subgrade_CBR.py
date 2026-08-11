"""Subgrade Design > CBR Equivalent (sidebar page)."""
from __future__ import annotations

from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from app.core.page_registry import SUBGRADE_DCP
from app.core.ui_style import title_style
from app.layouts import BasePage, define_page
from app.pages.Subgrade_Design.cbr import CbrPage
from app.pages.Subgrade_Design.common import expand_vertical
from app.widgets.button import secondary_button


@define_page("blank", title="CBR Equivalent")
class SubgradeCbrPage(BasePage):
    """CBR Equivalent page; reads live DCP data from the DCP sidebar page."""

    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._page_title = QLabel("CBR Equivalent")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        content.addLayout(title_row)

        self.cbr_page = CbrPage(dcp_provider=self._resolve_dcp_page)
        expand_vertical(self.cbr_page)
        content.addWidget(self.cbr_page, 1)
        self.cbr_page.results_changed.connect(self._push_quick_results)
        self._push_quick_results()

    def _resolve_dcp_page(self):
        mw = self.window()
        if not hasattr(mw, "_ensure_page"):
            return None
        mw._ensure_page(SUBGRADE_DCP)
        pages = getattr(mw, "_page_widgets", None)
        if not pages or SUBGRADE_DCP >= len(pages):
            return None
        shell = pages[SUBGRADE_DCP]
        if shell is None:
            return None
        return getattr(shell, "dcp_page", shell)

    def refresh_from_dcp(self) -> None:
        self.cbr_page.refresh_analysis()

    def quick_results(self) -> dict[str, str]:
        return self.cbr_page.quick_results()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.refresh_from_dcp()
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def activate_page(self) -> None:
        self.refresh_from_dcp()
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def _results(self) -> dict[str, str]:
        return self.quick_results()

    def _setup_quick_panel(self) -> None:
        mw = self.window()
        if not hasattr(mw, "quick_panel"):
            return
        if hasattr(mw.quick_panel, "set_subgrade_cbr_equivalent_schema"):
            mw.quick_panel.set_subgrade_cbr_equivalent_schema()
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
