"""Subgrade Design > DCP (sidebar page)."""
from __future__ import annotations

from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
)

from app.core.page_registry import SUBGRADE_CBR
from app.core.ui_style import title_style
from app.layouts import BasePage, define_page
from app.pages.Subgrade_Design.dcp import DcpPage
from app.widgets.button import secondary_button
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content


@define_page("blank", title="DCP")
class SubgradeDcpPage(BasePage):
    """DCP analysis page with Quick Result toggle."""

    def setup(self, content: QVBoxLayout) -> None:
        content.setContentsMargins(24, 24, 24, 24)
        content.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._page_title = QLabel("DCP")
        self._page_title.setStyleSheet(title_style(22))
        title_row.addWidget(self._page_title)
        title_row.addStretch()
        self.quick_panel_btn = secondary_button("Show Quick Result", min_height=36)
        self.quick_panel_btn.clicked.connect(self._toggle_quick_panel)
        title_row.addWidget(self.quick_panel_btn)
        content.addLayout(title_row)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.dcp_page = DcpPage()
        fit_scroll_content(self.dcp_page)
        scroll.setWidget(self.dcp_page)
        configure_page_scroll(scroll)
        content.addWidget(scroll, 1)

        self.dcp_page.input_table.data_changed.connect(self._on_dcp_data_changed)
        self._push_quick_results()

    def read_input_rows(self):
        return self.dcp_page.read_input_rows()

    def quick_results(self) -> dict[str, str]:
        return self.dcp_page.quick_results()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def activate_page(self) -> None:
        self._setup_quick_panel()
        self._sync_quick_panel_button()

    def _on_dcp_data_changed(self) -> None:
        self._push_quick_results()
        mw = self.window()
        pages = getattr(mw, "_page_widgets", None)
        if not pages or SUBGRADE_CBR >= len(pages):
            return
        cbr_shell = pages[SUBGRADE_CBR]
        if cbr_shell is not None and hasattr(cbr_shell, "refresh_from_dcp"):
            cbr_shell.refresh_from_dcp()

    def _results(self) -> dict[str, str]:
        return self.quick_results()

    def _setup_quick_panel(self) -> None:
        mw = self.window()
        if not hasattr(mw, "quick_panel"):
            return
        if hasattr(mw.quick_panel, "set_subgrade_schema"):
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
