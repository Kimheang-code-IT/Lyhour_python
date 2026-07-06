"""Main window: 3-column layout (Sidebar_left, stack, preview_panel). Lazy-loads pages."""
import json
import os
import tempfile
from pathlib import Path
from typing import Callable

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QLabel,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QFont

from app.core.Sidebar_left import SidebarLeft
from app.core.Topbar_nav import TopbarNav
from app.core.preview_panel import PreviewPanel
from app.core.quick_panel import QuickPanel
from app.core.ui_scale import UiScale
from app.core.theme import apply_drop_shadow, apply_theme_to_app, shell_stylesheet, theme_tokens
from app.core.i18n import tr
from app.services.app_settings import AppSettings, AppSettingsData
from app.widgets.settings_dialog import SettingsDialog
from app.widgets.loading_overlay import LoadingOverlay
from app.widgets.dialog import info
from app.services.pdf_export import export_pdf
from app.services.excel_io import ExcelIOService
from app.services.tld_io import TldIOService
from app.services.file_history import FileHistoryStore
from app.services.excel_session import ExcelSessionCache
from app.widgets.file_tab_bar import FileTabBar
from app.widgets.recent_imports_dialog import pick_recent_import
from loguru import logger
from app.services.traffic_excel import (
    build_summary_total_row,
    filter_traffic_count_rows,
    select_daily_totals,
)
from app.data.road_classification import road_classification_code
from app.services.traffic_aadt_pcu import (
    AadtPcuResult,
    compute_aadt_pcu,
    compute_aadt_pcu_from_direct_input,
    parse_design_years,
)
from app.services.traffic_lane_projection import (
    DEFAULT_GROWTH_RATE,
    LaneProjectionResult,
    compute_lane_projection_from_workbook_data,
)
from app.services.traffic_esal import EsalResult, compute_esal_from_workbook_data
from app.services.traffic_quick_results import build_traffic_quick_results
from app.config.settings import APP_NAME, APP_DISPLAY_NAME, PROJECT_EXTENSION, PROJECT_FILTER

from app.core.page_registry import (
    FIXED_RIGHT_PANEL_PAGES,
    RGD_HORIZONTAL_CURVATURE,
    TRAFFIC_ANALYSIS,
    TRAFFIC_INPUT,
    TRAFFIC_PAGES,
    build_page_factories,
)

_PAGE_FACTORIES: list[Callable[[QWidget], QWidget]] = []
_PAGES_WITHOUT_PREVIEW = TRAFFIC_PAGES
_PAGES_WITH_FIXED_RIGHT_PANEL = FIXED_RIGHT_PANEL_PAGES
_RIGHT_PANEL_MIN_WIDTH = 400
_RIGHT_PANEL_MAX_WIDTH = 430
_RIGHT_PANEL_DEFAULT_MAX_WIDTH = 16777215


def _register_pages() -> None:
    if _PAGE_FACTORIES:
        return
    _PAGE_FACTORIES.extend(build_page_factories())


def _placeholder_page(title: str, description: str, parent: QWidget) -> QWidget:
    page = QWidget(parent)
    layout = QVBoxLayout(page)
    layout.setContentsMargins(24, 24, 24, 24)
    lbl = QLabel(title)
    lbl.setStyleSheet("font-size: 22px; font-weight: bold;")
    layout.addWidget(lbl)
    desc = QLabel(description)
    desc.setStyleSheet("color: #888;")
    layout.addWidget(desc)
    layout.addStretch()
    return page


class MainWindow(QMainWindow):
    """Main window with 3-column layout: Sidebar_left, stack, preview_panel. Pages lazy-loaded."""

    settingsApplyFinished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = TopbarNav(self)
        self.title_bar.connect_window(self)
        root_layout.addWidget(self.title_bar)

        self.file_tab_bar = FileTabBar(self)
        self.file_tab_bar.hide()
        root_layout.addWidget(self.file_tab_bar)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(6)

        self.nav = SidebarLeft(self)
        self.nav.setMinimumWidth(120)
        self.splitter.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.stack.setObjectName("centerStack")
        self.stack.setMinimumWidth(200)

        _register_pages()
        self._page_widgets: list[QWidget | None] = [None] * len(_PAGE_FACTORIES)
        for i in range(len(_PAGE_FACTORIES)):
            self.stack.addWidget(_placeholder_page("Loading...", "", self))

        self.splitter.addWidget(self.stack)

        self.preview_panel = PreviewPanel(self)
        self.preview_panel.setMinimumWidth(120)
        self.splitter.addWidget(self.preview_panel)

        self.quick_panel = QuickPanel(self)
        self.quick_panel.hide()
        self.splitter.addWidget(self.quick_panel)

        self.splitter.setSizes([250, 510, 480, 280])

        apply_drop_shadow(self.nav)
        apply_drop_shadow(self.preview_panel)
        apply_drop_shadow(self.quick_panel)

        content_layout.addWidget(self.splitter)
        root_layout.addWidget(content, 1)

        self._content = content
        self._settings_busy_overlay = LoadingOverlay(content)
        self._settings_applying = False

        self.calc_state = {"inputs": {}, "results": {}}
        self.current_file_path: str | None = None
        self._active_excel_session: str | None = None
        self._active_tld_session: str | None = None
        self._open_excel_sessions: list[str] = []
        self._excel_io = ExcelIOService.instance()
        self._tld_io = TldIOService.instance()
        self._pending_road_classification: tuple[str | None, int | None, int | None] = (
            None,
            None,
            None,
        )
        self._pending_lane_projection: LaneProjectionResult | None = None
        self._pending_esal_result: EsalResult | None = None
        self._pending_aadt_pcu_result: AadtPcuResult | None = None

        self.title_bar.connect_file_actions(self)
        self.file_tab_bar.tabActivated.connect(self.activate_excel_session)
        self.file_tab_bar.tabClosed.connect(self.close_excel_session)
        self.file_tab_bar.importRequested.connect(self.import_excel_dialog)
        self.title_bar.toggleSidebarRequested.connect(self.toggle_sidebar)
        self.title_bar.togglePreviewRequested.connect(self.toggle_preview)
        self.title_bar.settingsRequested.connect(self.open_settings_dialog)
        self.title_bar.helpRequested.connect(self.open_help_dialog)
        self.nav.toggleRequested.connect(self.toggle_sidebar)
        self.title_bar.connect_shortcuts(self)
        self.title_bar.connect_search_palette(self)
        self.nav.pageChanged.connect(self._on_page_changed)
        AppSettings.instance().changed.connect(self._on_settings_changed)
        self._quick_panel_visible = False
        self._apply_saved_settings(apply_workspace=True)
        self.nav.set_current_index(0)
        self._update_window_title()

        self._ensure_page(0)
        self.stack.setCurrentIndex(0)
        self._apply_preview_visibility(0)
        self._activate_page(0)
        QTimer.singleShot(0, self.refresh_road_classification)
        QTimer.singleShot(0, self.refresh_traffic_quick_results)
        self.splitter.splitterMoved.connect(lambda *_args: self._maybe_refresh_ui_scale())
        QTimer.singleShot(0, self._maybe_refresh_ui_scale)
        self.refresh_file_tabs()

    def refresh_file_tabs(self) -> None:
        history = FileHistoryStore.instance()
        open_entries = []
        for session_id in self._open_excel_sessions:
            entry = history.get(session_id)
            if entry is not None:
                open_entries.append(entry)
        self.file_tab_bar.set_tabs(open_entries, active_session_id=self._active_excel_session)
        self.file_tab_bar.hide()

    def open_recent_imports_dialog(self) -> None:
        history = FileHistoryStore.instance()

        def on_remove_entry(session_id: str) -> None:
            entry = history.get(session_id)
            self.remove_import(session_id)
            if entry is not None:
                self.statusBar().showMessage(tr("file.recent.removed").format(name=entry.file_name), 4000)

        session_id = pick_recent_import(
            self,
            lambda: history.entries,
            on_remove=on_remove_entry,
        )
        if not session_id:
            return
        entry = history.get(session_id)
        if entry is not None and entry.is_tld:
            self.activate_tld_session(session_id)
        else:
            self.activate_excel_session(session_id)

    def remove_import(self, session_id: str) -> None:
        """Remove a traffic or TLD import from cache/history."""
        entry = FileHistoryStore.instance().get(session_id)
        if entry is not None and entry.is_tld:
            was_active = self._active_tld_session == session_id
            self._tld_io.remove_from_history(session_id)
            if was_active:
                self._clear_active_tld_import()
            return

        self.remove_excel_import(session_id)

    def remove_excel_import(self, session_id: str) -> None:
        """Remove cached import data and history entry so the file can be re-imported."""
        was_active = self._active_excel_session == session_id
        self._excel_io.remove_from_history(session_id)
        if session_id in self._open_excel_sessions:
            self._open_excel_sessions.remove(session_id)
        if was_active:
            self._clear_active_traffic_import()
        self.refresh_file_tabs()

    def _clear_active_traffic_import(self) -> None:
        self._active_excel_session = None
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        tld_data = traffic_state.get("tld_data")
        tld_session = self._active_tld_session
        traffic_state.clear()
        if tld_data is not None:
            traffic_state["tld_data"] = tld_data
        if tld_session:
            self._active_tld_session = tld_session
        self._apply_traffic_summary([], None)
        self.refresh_lane_projection()
        self.refresh_esal()

    def _clear_active_tld_import(self) -> None:
        self._active_tld_session = None
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        traffic_state.pop("tld_data", None)
        if traffic_state.get("esal_load_mode") == "tld":
            traffic_state.pop("esal_load_mode", None)
        self.refresh_esal()
        detail_page = self._page_widgets[1] if len(self._page_widgets) > 1 else None
        if detail_page is not None and hasattr(detail_page, "esal_page"):
            esal_page = detail_page.esal_page
            if hasattr(esal_page, "clear_tld_excel"):
                esal_page.clear_tld_excel()

    def _open_excel_tab(self, session_id: str) -> None:
        if session_id in self._open_excel_sessions:
            self._open_excel_sessions.remove(session_id)
        self._open_excel_sessions.insert(0, session_id)

    def _active_count_hour(self) -> str:
        traffic_state = self.calc_state.get("traffic_analysis") or {}
        return str(traffic_state.get("traffic_count_hour") or "12h")

    def import_excel_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("menu.file.import_excel"),
            "",
            ExcelIOService.excel_filter(),
        )
        if path:
            self.import_excel_file(path)

    def import_excel_file(self, path: str, *, count_hour: str | None = None) -> bool:
        try:
            result = self._excel_io.import_traffic_workbook(
                path,
                count_hour=count_hour or self._active_count_hour(),
            )
        except Exception as exc:
            logger.exception("Excel import failed")
            QMessageBox.warning(self, tr("menu.file.import_excel"), f"{tr('file.import.failed')}\n{exc}")
            return False

        data = self._excel_io.load_session(result.session_id)
        if not data:
            QMessageBox.warning(self, tr("menu.file.import_excel"), tr("file.import.failed"))
            return False

        self._active_excel_session = result.session_id
        self._open_excel_tab(result.session_id)
        self.set_traffic_excel_data(data)
        self.refresh_file_tabs()
        self._navigate_to_traffic_input()
        self.statusBar().showMessage(tr("file.import.ok").format(name=result.file_name), 5000)
        return True

    def import_tld_file(self, path: str) -> bool:
        try:
            result = self._tld_io.import_tld_workbook(path)
        except Exception as exc:
            logger.exception("TLD import failed")
            QMessageBox.warning(self, "Read TLD Excel", f"Could not read TLD data:\n{exc}")
            return False

        data = self._tld_io.load_session(result.session_id)
        if not data:
            QMessageBox.warning(self, "Read TLD Excel", tr("file.import.failed"))
            return False

        self._active_tld_session = result.session_id
        self.set_tld_excel_data(data)
        self._present_tld_import(data)
        self._navigate_to_traffic_esal()
        self.statusBar().showMessage(tr("file.tld.import.ok").format(name=result.file_name), 5000)
        return True

    def activate_tld_session(self, session_id: str) -> None:
        data = self._tld_io.load_session(session_id)
        if not data:
            QMessageBox.information(self, "Read TLD Excel", tr("file.session.missing"))
            self.remove_import(session_id)
            return
        self._active_tld_session = str(data.get("session_id") or session_id)
        self.set_tld_excel_data(data)
        self._present_tld_import(data)
        self._navigate_to_traffic_esal()

    def _present_tld_import(self, data: dict) -> None:
        source_path = str(data.get("source_path") or "")
        detail_page = self._page_widgets[1] if len(self._page_widgets) > 1 else None
        if detail_page is not None and hasattr(detail_page, "esal_page"):
            esal_page = detail_page.esal_page
            if hasattr(esal_page, "restore_tld_import"):
                esal_page.restore_tld_import(source_path or None)

    def _navigate_to_traffic_esal(self) -> None:
        from app.core.page_registry import TRAFFIC_ANALYSIS

        self._on_page_changed(TRAFFIC_ANALYSIS)
        self.nav.set_current_index(TRAFFIC_ANALYSIS)
        detail_page = self._page_widgets[1] if len(self._page_widgets) > 1 else None
        if detail_page is not None and hasattr(detail_page, "show_esal_tab"):
            detail_page.show_esal_tab()

    def activate_excel_session(self, session_id: str) -> None:
        entry = FileHistoryStore.instance().get(session_id)
        if entry is not None and entry.is_tld:
            self.activate_tld_session(session_id)
            return
        data = self._excel_io.load_session(session_id)
        if not data:
            QMessageBox.information(self, tr("menu.file.import_excel"), tr("file.session.missing"))
            self.close_excel_session(session_id)
            return
        effective_id = str(data.get("session_id") or session_id)
        if effective_id != session_id and session_id in self._open_excel_sessions:
            self._open_excel_sessions.remove(session_id)
        self._active_excel_session = effective_id
        self._open_excel_tab(effective_id)
        self.set_traffic_excel_data(data)
        self.refresh_file_tabs()
        self._navigate_to_traffic_input()

    def close_excel_session(self, session_id: str) -> None:
        self._excel_io.close_session(session_id)
        if session_id in self._open_excel_sessions:
            self._open_excel_sessions.remove(session_id)
        if self._active_excel_session == session_id:
            self._clear_active_traffic_import()
        self.refresh_file_tabs()

    def clear_excel_history(self) -> None:
        FileHistoryStore.instance().clear()
        ExcelSessionCache.instance().clear()
        self._open_excel_sessions.clear()
        self._clear_active_traffic_import()
        self._clear_active_tld_import()
        self.refresh_file_tabs()

    def export_excel_summary_dialog(self) -> None:
        traffic_state = self.calc_state.get("traffic_analysis") or {}
        rows = traffic_state.get("traffic_count_rows") or []
        summary = traffic_state.get("summary_total_row")
        if not rows and not summary:
            QMessageBox.information(self, tr("menu.file.export_excel"), tr("file.session.missing"))
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("menu.file.export_excel"),
            "",
            ExcelIOService.excel_filter(),
        )
        if not path:
            return
        try:
            out = self._excel_io.export_traffic_summary(
                path,
                traffic_count_rows=rows,
                summary_total_row=summary,
            )
            self.statusBar().showMessage(tr("file.export.excel.ok").format(path=out.name), 5000)
        except Exception as exc:
            QMessageBox.warning(self, tr("menu.file.export_excel"), str(exc))

    def _navigate_to_traffic_input(self) -> None:
        from app.core.page_registry import TRAFFIC_INPUT

        self._on_page_changed(TRAFFIC_INPUT)
        self.nav.set_current_index(TRAFFIC_INPUT)

    def _apply_saved_settings(self, *, apply_workspace: bool = False) -> None:
        prefs = AppSettings.current()
        self._sidebar_visible = prefs.sidebar_visible
        self._preview_visible = prefs.preview_visible

        UiScale.set_user_font_scale(prefs.font_scale)
        UiScale.set_compact_mode(prefs.compact_mode)

        app = QApplication.instance()
        if app is not None:
            apply_theme_to_app(app, theme=prefs.theme, accent=prefs.accent_color)

        self._apply_app_font(prefs.language)

        if apply_workspace:
            self.nav.setVisible(self._sidebar_visible)
            self._apply_preview_visibility()

        QTimer.singleShot(0, self._retranslate_shell_ui)
        self._apply_shell_theme()
        self._refresh_ui_scale_all_pages()

    def _apply_shell_theme(self) -> None:
        tokens = theme_tokens()
        self.splitter.setStyleSheet(
            f"QSplitter::handle {{ background-color: {tokens.splitter_handle}; width: 6px; }}"
        )
        self.stack.setStyleSheet(shell_stylesheet(tokens))
        self.title_bar.apply_theme()
        self.nav.apply_theme()
        self.preview_panel.apply_theme()
        self.quick_panel.apply_theme()
        palette = self.title_bar._search_palette
        if palette is not None:
            palette.apply_theme()
        if hasattr(self, "file_tab_bar"):
            self.file_tab_bar.apply_theme()

    def _retranslate_shell_ui(self) -> None:
        self._apply_shell_theme()
        self.title_bar.retranslate_ui()
        if hasattr(self.nav, "retranslate_ui"):
            self.nav.retranslate_ui()
        palette = self.title_bar._search_palette
        if palette is not None:
            palette.retranslate_ui()
        self.title_bar.apply_shortcut_settings()
        self.refresh_file_tabs()

    def _apply_app_font(self, language: str) -> None:
        app = QApplication.instance()
        if app is None:
            return
        font = QFont(app.font())
        if language == "km":
            font.setFamilies(["Khmer OS", "Khmer OS System", "Leelawadee UI", "Segoe UI"])
        else:
            font.setFamilies(["Segoe UI", "Arial", "sans-serif"])
        app.setFont(font)

    def _on_settings_changed(self, _prefs: AppSettingsData) -> None:
        if self._settings_applying:
            return
        self._settings_applying = True
        self._settings_busy_overlay.show_busy(tr("settings.applying"))
        QApplication.processEvents()
        QTimer.singleShot(0, self._finish_settings_apply)

    def _finish_settings_apply(self) -> None:
        try:
            self._apply_saved_settings(apply_workspace=True)
            self.statusBar().showMessage(tr("settings.apply.ok"), 4000)
        finally:
            self._settings_busy_overlay.hide_busy()
            self._settings_applying = False
            self.settingsApplyFinished.emit()

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def open_help_dialog(self) -> None:
        info(self, tr("help.title"), tr("help.body"))

    def closeEvent(self, event: QCloseEvent) -> None:
        prefs = AppSettings.current()
        if prefs.confirm_exit:
            box = QMessageBox(self)
            box.setWindowTitle(APP_DISPLAY_NAME)
            box.setText(tr("settings.confirm_exit.message"))
            box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            box.setDefaultButton(QMessageBox.StandardButton.No)
            if box.exec() != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        ExcelSessionCache.instance().clear()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._maybe_refresh_ui_scale()

    def _maybe_refresh_ui_scale(self) -> None:
        width = self.stack.width() or self.width()
        if UiScale.update(width):
            self._refresh_ui_scale_all_pages()

    def _refresh_ui_scale_all_pages(self) -> None:
        for page in self._page_widgets:
            if page is not None and hasattr(page, "refresh_ui_scale"):
                page.refresh_ui_scale()
            if page is not None and hasattr(page, "refresh_theme"):
                page.refresh_theme()

    def _on_page_changed(self, index: int) -> None:
        if index < 0 or index >= len(_PAGE_FACTORIES):
            return
        self._ensure_page(index)
        self.stack.setCurrentIndex(index)
        if index not in _PAGES_WITHOUT_PREVIEW:
            self._quick_panel_visible = False
        self._apply_preview_visibility(index)
        self.nav.set_current_index(index)
        self._activate_page(index)

    def _activate_page(self, index: int) -> None:
        """Refresh page data and side panels when a menu item is opened."""
        page = self._page_widgets[index]
        if page is None:
            return

        if index == TRAFFIC_INPUT:
            self.refresh_traffic_quick_results()
        elif index == TRAFFIC_ANALYSIS:
            self._refresh_traffic_analysis_views()
        elif hasattr(page, "activate_page"):
            page.activate_page()

    def _refresh_traffic_analysis_views(self) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        self._apply_traffic_summary(
            traffic_state.get("traffic_count_rows", []),
            traffic_state.get("summary_total_row"),
        )
        self._apply_pending_road_classification()
        self._apply_pending_lane_projection()
        self._apply_pending_esal_result()
        self._apply_pending_aadt_pcu_result()
        self.refresh_traffic_quick_results()

    def _apply_preview_visibility(self, index: int | None = None) -> None:
        if index is None:
            index = self.stack.currentIndex()
        is_traffic_page = index in _PAGES_WITHOUT_PREVIEW
        if index in _PAGES_WITH_FIXED_RIGHT_PANEL:
            self.preview_panel.setMinimumWidth(_RIGHT_PANEL_MIN_WIDTH)
            self.preview_panel.setMaximumWidth(_RIGHT_PANEL_MAX_WIDTH)
        else:
            self.preview_panel.setMinimumWidth(120)
            self.preview_panel.setMaximumWidth(_RIGHT_PANEL_DEFAULT_MAX_WIDTH)
        self.preview_panel.setVisible(self._preview_visible and not is_traffic_page)
        self.quick_panel.setVisible(is_traffic_page and self._quick_panel_visible)
        if 0 <= index < len(self._page_widgets):
            page = self._page_widgets[index]
            if page is not None and hasattr(page, "sync_quick_panel_button"):
                page.sync_quick_panel_button(self.is_quick_panel_visible())

    def _ensure_page(self, index: int) -> None:
        if index < 0 or index >= len(_PAGE_FACTORIES):
            return
        if self._page_widgets[index] is not None:
            return
        try:
            page = _PAGE_FACTORIES[index](self.stack)
            self._page_widgets[index] = page
            self.stack.removeWidget(self.stack.widget(index))
            self.stack.insertWidget(index, page)
            if hasattr(page, "refresh_ui_scale"):
                page.refresh_ui_scale()
        except Exception as exc:
            import traceback

            traceback.print_exc()
            QMessageBox.warning(self, "Page Error", f"Could not open this page.\n\n{exc}")

    @property
    def calculator_page(self) -> QWidget | None:
        self._ensure_page(RGD_HORIZONTAL_CURVATURE)
        return self._page_widgets[RGD_HORIZONTAL_CURVATURE]

    def toggle_sidebar(self):
        self._sidebar_visible = not self._sidebar_visible
        self.nav.setVisible(self._sidebar_visible)

    def toggle_preview(self):
        self._preview_visible = not self._preview_visible
        self._apply_preview_visibility()

    def toggle_quick_panel(self):
        self._quick_panel_visible = not self._quick_panel_visible
        self._apply_preview_visibility()
        return self.is_quick_panel_visible()

    def is_quick_panel_visible(self) -> bool:
        return self.stack.currentIndex() in _PAGES_WITHOUT_PREVIEW and self._quick_panel_visible

    @property
    def traffic_input_page(self):
        self._ensure_page(0)
        return self._page_widgets[0]

    def refresh_road_classification(self) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        aadt_pcu = traffic_state.get("aadt_pcu") or {}
        design_year = ""
        input_page = self._page_widgets[0]
        if input_page is not None and hasattr(input_page, "active_geometry_design_year"):
            design_year = input_page.active_geometry_design_year()
        traffic_state["geometry_design_year"] = design_year
        projected_aadt = aadt_pcu.get("projected_aadt", aadt_pcu.get("total_aadt"))
        projected_pcu = aadt_pcu.get("projected_pcu", aadt_pcu.get("total_pcu"))
        if projected_aadt:
            traffic_state["road_classification"] = road_classification_code(
                int(projected_aadt),
                int(projected_pcu) if projected_pcu else None,
            )
        self._apply_road_classification(
            design_year,
            projected_aadt,
            projected_pcu,
        )
        self.refresh_traffic_quick_results()

    def refresh_traffic_quick_results(self) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        input_page = self._page_widgets[0]
        geometry_design_year = ""
        pavement_design_year = ""
        if input_page is not None and hasattr(input_page, "active_geometry_design_year"):
            geometry_design_year = input_page.active_geometry_design_year()
        if input_page is not None and hasattr(input_page, "active_pavement_design_year"):
            pavement_design_year = input_page.active_pavement_design_year()

        results = build_traffic_quick_results(
            traffic_state,
            geometry_design_year=geometry_design_year,
            pavement_design_year=pavement_design_year,
        )
        self.quick_panel.set_results(results)

    def _aadt_pcu_inputs(self) -> tuple[float, str, int]:
        growth_rate = DEFAULT_GROWTH_RATE
        design_year_label = ""
        design_years = 0
        input_page = self._page_widgets[0]
        if input_page is not None and hasattr(input_page, "active_growth_rate"):
            growth_rate = input_page.active_growth_rate()
        if input_page is not None and hasattr(input_page, "active_geometry_design_year"):
            design_year_label = input_page.active_geometry_design_year()
            design_years = parse_design_years(design_year_label)
        return growth_rate, design_year_label, design_years

    def _apply_pending_aadt_pcu_result(self) -> None:
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_aadt_pcu_result"):
            detail_page.set_aadt_pcu_result(self._pending_aadt_pcu_result)

    def refresh_aadt_pcu(self) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        daily_totals = traffic_state.get("daily_totals")
        summary_total_row = traffic_state.get("summary_total_row")
        growth_rate, design_year_label, design_years = self._aadt_pcu_inputs()
        input_page = self._page_widgets[0]
        area_type = ""
        if input_page is not None and hasattr(input_page, "active_area_type"):
            area_type = input_page.active_area_type()
        traffic_state["area_type"] = area_type

        if (
            input_page is not None
            and hasattr(input_page, "is_direct_input_mode")
            and input_page.is_direct_input_mode()
        ):
            base_aadt = 0
            base_pcu = 0.0
            if hasattr(input_page, "active_direct_aadt"):
                base_aadt = input_page.active_direct_aadt()
            if hasattr(input_page, "active_direct_pcu"):
                base_pcu = input_page.active_direct_pcu()
            result = compute_aadt_pcu_from_direct_input(
                base_aadt,
                base_pcu,
                design_years=design_years,
                growth_rate=growth_rate,
                design_year_label=design_year_label,
                area_type=area_type,
            )
        elif not daily_totals and not summary_total_row:
            result = compute_aadt_pcu(
                design_years=design_years,
                growth_rate=growth_rate,
                design_year_label=design_year_label,
                area_type=area_type,
            )
        else:
            try:
                result = compute_aadt_pcu(
                    daily_totals,
                    daily_totals_12h=traffic_state.get("daily_totals_12h"),
                    daily_totals_24h=traffic_state.get("daily_totals_24h"),
                    survey_hours=int(traffic_state.get("survey_hours") or 12),
                    count_hour=traffic_state.get("traffic_count_hour", "12h"),
                    summary_total_row=summary_total_row,
                    design_years=design_years,
                    growth_rate=growth_rate,
                    design_year_label=design_year_label,
                    area_type=area_type,
                )
            except Exception:
                result = compute_aadt_pcu(
                    design_years=design_years,
                    growth_rate=growth_rate,
                    design_year_label=design_year_label,
                    area_type=area_type,
                )

        traffic_state["aadt_pcu"] = {
            "base_aadt": result.base_total_aadt,
            "base_pcu": result.base_total_pcu,
            "projected_aadt": result.projected_total_aadt,
            "projected_pcu": result.projected_total_pcu,
            "total_aadt": result.total_aadt,
            "total_pcu": result.total_pcu,
            "design_year_label": result.design_year_label,
            "design_years": result.design_years,
            "growth_rate": result.growth_rate,
            "input_source": result.input_source,
            "area_type": area_type,
        }
        self._apply_aadt_pcu_result(result)

    def _apply_aadt_pcu_result(self, result: AadtPcuResult | None) -> None:
        self._pending_aadt_pcu_result = result
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_aadt_pcu_result"):
            detail_page.set_aadt_pcu_result(result)
        self.refresh_road_classification()

    def _apply_road_classification(
        self,
        design_year: str | None,
        total_aadt: int | None,
        total_pcu: int | None,
    ) -> None:
        self._pending_road_classification = (design_year, total_aadt, total_pcu)
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_road_classification"):
            detail_page.set_road_classification(design_year, total_aadt, total_pcu)

    def _apply_pending_road_classification(self) -> None:
        design_year, total_aadt, total_pcu = self._pending_road_classification
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_road_classification"):
            detail_page.set_road_classification(design_year, total_aadt, total_pcu)

    def _apply_pending_lane_projection(self) -> None:
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_lane_projection"):
            detail_page.set_lane_projection(self._pending_lane_projection)

    def refresh_lane_projection(self) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        sheets = traffic_state.get("sheets")
        if not sheets:
            traffic_state["lane_projection"] = {
                "d1_peak_volume": 0,
                "d2_peak_volume": 0,
                "projection_rows": [],
            }
            self._apply_lane_projection(None)
            self.refresh_esal()
            return

        growth_rate = DEFAULT_GROWTH_RATE
        input_page = self._page_widgets[0]
        if input_page is not None and hasattr(input_page, "active_growth_rate"):
            growth_rate = input_page.active_growth_rate()

        try:
            result = compute_lane_projection_from_workbook_data(
                traffic_state,
                growth_rate=growth_rate,
                save_outputs=False,
                print_table=False,
            )
        except Exception:
            result = None

        traffic_state["lane_projection"] = {
            "d1_peak_volume": result.d1_peak_volume if result else 0,
            "d2_peak_volume": result.d2_peak_volume if result else 0,
            "projection_rows": list(result.projection_rows) if result else [],
        }
        self._apply_lane_projection(result)
        self.refresh_esal()

    def _apply_pending_esal_result(self) -> None:
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_esal_result"):
            detail_page.set_esal_result(self._pending_esal_result)

    def refresh_esal(self) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        daily_totals = traffic_state.get("daily_totals")
        daily_totals_12h = traffic_state.get("daily_totals_12h")
        daily_totals_24h = traffic_state.get("daily_totals_24h")

        growth_rate = DEFAULT_GROWTH_RATE
        input_page = self._page_widgets[0]
        if input_page is not None and hasattr(input_page, "active_growth_rate"):
            growth_rate = input_page.active_growth_rate()

        load_mode = traffic_state.get("esal_load_mode", "standard_load")
        lane_count = int(traffic_state.get("standard_lane_count") or 1)
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "esal_page"):
            esal_page = detail_page.esal_page
            load_mode = esal_page.active_esal_load_mode()
            lane_count = esal_page.active_standard_lane_count()

        traffic_state["esal_load_mode"] = load_mode
        traffic_state["standard_lane_count"] = lane_count

        geometry_design_years = 0
        pavement_design_years = 0
        if input_page is not None and hasattr(input_page, "active_geometry_design_year"):
            geometry_design_years = parse_design_years(input_page.active_geometry_design_year())
        if input_page is not None and hasattr(input_page, "active_pavement_design_year"):
            pavement_design_years = parse_design_years(input_page.active_pavement_design_year())
        traffic_state["geometry_design_years"] = geometry_design_years
        traffic_state["pavement_design_years"] = pavement_design_years

        has_traffic_data = bool(daily_totals or daily_totals_12h or daily_totals_24h)
        use_tld = load_mode == "tld"
        if not has_traffic_data and not use_tld:
            traffic_state["esal"] = None
            self._apply_esal_result(None)
            self.refresh_traffic_quick_results()
            return

        try:
            from app.services.traffic_esal import compute_esal_from_workbook_data

            use_tld = load_mode == "tld"
            tld_data = traffic_state.get("tld_data") if use_tld else None
            result = compute_esal_from_workbook_data(
                traffic_state,
                growth_rate=growth_rate,
                lane_count=lane_count,
                pavement_design_years=pavement_design_years,
                use_tld=use_tld,
                tld_data=tld_data,
            )
        except Exception:
            result = None

        if result is not None:
            traffic_state["esal"] = {
                "axle_numbers": dict(result.axle_numbers),
                "design_periods": [
                    {
                        "years": period.years,
                        "total_esal": period.total_esal,
                        "traffic_class": period.traffic_class,
                    }
                    for period in result.design_periods
                ],
            }
        else:
            traffic_state["esal"] = None
        self._apply_esal_result(result)
        self.refresh_traffic_quick_results()

    def _apply_esal_result(self, result: EsalResult | None) -> None:
        self._pending_esal_result = result
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_esal_result"):
            detail_page.set_esal_result(result)

    def _apply_lane_projection(self, result: LaneProjectionResult | None) -> None:
        self._pending_lane_projection = result
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_lane_projection"):
            detail_page.set_lane_projection(result)
        self.refresh_traffic_quick_results()

    def set_traffic_count_rows(self, rows: list[list]) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        traffic_state["traffic_count_rows"] = rows
        self._apply_traffic_count_rows(rows)

    def set_tld_excel_data(self, data: dict) -> None:
        """Store TLD workbook data for ESAL calculations."""
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        traffic_state["tld_data"] = data
        traffic_state["esal_load_mode"] = "tld"
        session_id = data.get("session_id")
        if session_id:
            self._active_tld_session = str(session_id)
        self.refresh_esal()

    def set_traffic_excel_data(self, data: dict) -> None:
        """Store temporary traffic investigation data for the current app session."""
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        traffic_state.update(data)
        self._apply_traffic_summary(
            data.get("traffic_count_rows", []),
            data.get("summary_total_row"),
        )
        self.refresh_lane_projection()
        self.refresh_esal()

    def refresh_traffic_summary(self, count_hour: str) -> None:
        """Recalculate summary table totals when Traffic Count Hour changes."""
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        daily_totals_12h = traffic_state.get("daily_totals_12h")
        daily_totals_24h = traffic_state.get("daily_totals_24h")
        daily_totals = traffic_state.get("daily_totals")
        if not daily_totals_12h and not daily_totals_24h and not daily_totals:
            return

        survey_hours = int(traffic_state.get("survey_hours") or 12)
        summary_total_row = build_summary_total_row(
            daily_totals_12h=daily_totals_12h,
            daily_totals_24h=daily_totals_24h,
            daily_totals=daily_totals,
            survey_hours=survey_hours,
            count_hour=count_hour,
        )
        combined_rows = traffic_state.get("traffic_count_rows_all") or traffic_state.get(
            "traffic_count_rows",
            [],
        )
        traffic_count_rows = filter_traffic_count_rows(
            combined_rows,
            survey_hours=survey_hours,
            count_hour=count_hour,
        )
        if daily_totals_12h or daily_totals_24h:
            daily_totals = select_daily_totals(
                daily_totals_12h or {},
                daily_totals_24h or {},
                survey_hours=survey_hours,
                count_hour=count_hour,
            )
        traffic_state["daily_totals"] = daily_totals
        traffic_state["summary_total_row"] = summary_total_row
        traffic_state["traffic_count_hour"] = count_hour
        traffic_state["traffic_count_rows"] = traffic_count_rows
        self._apply_traffic_summary(
            traffic_count_rows,
            summary_total_row,
        )
        self.refresh_lane_projection()

    def _pie_daily_totals(self, traffic_state: dict) -> dict[str, list[int]] | None:
        """Raw per-sheet totals (D1 + D2) for the summary pie chart."""
        return (
            traffic_state.get("daily_totals_24h")
            or traffic_state.get("daily_totals_12h")
            or traffic_state.get("daily_totals")
        )

    def _apply_traffic_summary(
        self,
        rows: list[list],
        summary_total_row: list | None,
    ) -> None:
        self._ensure_page(1)
        detail_page = self._page_widgets[1]
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        if detail_page is not None and hasattr(detail_page, "set_traffic_count_rows"):
            detail_page.set_traffic_count_rows(
                rows,
                summary_total_row=summary_total_row,
                pie_daily_totals=self._pie_daily_totals(traffic_state),
            )
        self.refresh_aadt_pcu()
        self.refresh_esal()

    def _apply_traffic_count_rows(self, rows: list[list]) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        self._apply_traffic_summary(rows, traffic_state.get("summary_total_row"))

    def _update_window_title(self):
        name = Path(self.current_file_path).name if self.current_file_path else None
        self.setWindowTitle(f"{APP_DISPLAY_NAME} - {name}" if name else APP_DISPLAY_NAME)

    def new_document(self):
        self.current_file_path = None
        self.calc_state = {"inputs": {}, "results": {}}
        self.preview_panel.set_results(None)
        self._ensure_page(0)
        self._apply_traffic_summary([], None)
        self._apply_lane_projection(None)
        self._apply_esal_result(None)
        self.refresh_traffic_quick_results()
        cp = self.calculator_page
        if cp is not None and hasattr(cp, "set_inputs"):
            cp.set_inputs({
                "V_km_h": 90, "e_percent": 5, "f": 0.12,
                "surface_type": "Sealed roads", "vehicle_type": "Cars and Trucks",
                "friction_factor_type": "Des max",
            })
        self._update_window_title()

    def open_document(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", PROJECT_FILTER)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            inp = data.get("inputs") or {}
            cp = self.calculator_page
            if cp is not None and hasattr(cp, "set_inputs"):
                cp.set_inputs(inp)
            self.current_file_path = path
            self._update_window_title()
        except Exception as e:
            QMessageBox.warning(self, "Open Failed", f"Could not open file.\n{e}")

    def save_document(self):
        if self.current_file_path:
            self._write_document_to(self.current_file_path)
            return
        self.save_document_as()

    def save_document_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project As", "", PROJECT_FILTER)
        if not path:
            return
        if not path.endswith(PROJECT_EXTENSION) and not path.endswith(".json"):
            path += PROJECT_EXTENSION
        if self._write_document_to(path):
            self.current_file_path = path
            self._update_window_title()

    def _write_document_to(self, path: str) -> bool:
        try:
            data = {"version": 1, "inputs": self.calc_state.get("inputs", {}), "results": self.calc_state.get("results", {})}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Could not save file.\n{e}")
            return False

    def export_pdf(self):
        inp = self.calc_state.get("inputs") or {}
        res = self.calc_state.get("results") or {}
        if not inp and not res:
            QMessageBox.information(self, "No data", "Run the Building Calculator first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF As", "", "PDF (*.pdf);;All Files (*)")
        if not path:
            return
        if not path.endswith(".pdf"):
            path += ".pdf"
        image_path = None
        try:
            pixmap = self.preview_panel.preview_label.pixmap()
            if pixmap and not pixmap.isNull():
                fd, image_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                pixmap.save(image_path)
            export_pdf(path, title=f"{APP_NAME} – Building Report", inputs=inp, results=res, image_path=image_path)
            self.statusBar().showMessage(tr("file.export.pdf.ok").format(path=Path(path).name), 5000)
        except Exception as e:
            QMessageBox.warning(self, "Export failed", str(e))
        finally:
            if image_path and Path(image_path).exists():
                try:
                    Path(image_path).unlink()
                except Exception:
                    pass
