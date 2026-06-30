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
)
from PyQt6.QtCore import Qt

from app.core.Sidebar_left import SidebarLeft
from app.core.Topbar_nav import TopbarNav
from app.core.preview_panel import PreviewPanel
from app.core.quick_panel import QuickPanel
from app.core.theme import apply_drop_shadow
from app.services.pdf_export import export_pdf
from app.services.traffic_excel import build_summary_total_row
from app.services.traffic_aadt_pcu import AadtPcuResult, compute_aadt_pcu
from app.config.settings import APP_NAME, APP_DISPLAY_NAME, PROJECT_EXTENSION, PROJECT_FILTER

# Page order: 0=Input, 1=Detail Result, 2=Horizontal Curvature, 3=Superelevation Design
_PAGE_FACTORIES: list[Callable[[QWidget], QWidget]] = []
_PAGES_WITHOUT_PREVIEW = {0, 1}
_PAGES_WITH_FIXED_RIGHT_PANEL = {2, 3}
_RIGHT_PANEL_MIN_WIDTH = 400
_RIGHT_PANEL_MAX_WIDTH = 430
_RIGHT_PANEL_DEFAULT_MAX_WIDTH = 16777215


def _register_pages() -> None:
    if _PAGE_FACTORIES:
        return
    from app.pages.Traffic_Analysis_input import TrafficAnalysisInputPage
    from app.pages.Traffic_Analysis_Detail_Result import TrafficAnalysisDetailResultPage
    from app.pages.RGD_Horizontal_Curvature import RGDHorizontalCurvaturePage
    from app.pages.RGD_Superelevation_Design import RGDSuperelevationDesignPage
    _PAGE_FACTORIES.extend([
        lambda p: TrafficAnalysisInputPage(p),
        lambda p: TrafficAnalysisDetailResultPage(p),
        lambda p: RGDHorizontalCurvaturePage(p),
        lambda p: RGDSuperelevationDesignPage(p),
    ])


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

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(6)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #3e3e40; width: 6px; }")

        self.nav = SidebarLeft(self)
        self.nav.setMinimumWidth(120)
        self.splitter.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.stack.setObjectName("centerStack")
        self.stack.setStyleSheet("#centerStack { background-color: #2d2d30; }")
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

        self.splitter.setSizes([240, 480, 480, 320])

        apply_drop_shadow(self.nav)
        apply_drop_shadow(self.preview_panel)
        apply_drop_shadow(self.quick_panel)

        content_layout.addWidget(self.splitter)
        root_layout.addWidget(content, 1)

        self.calc_state = {"inputs": {}, "results": {}}
        self.current_file_path: str | None = None

        self.title_bar.connect_file_actions(self)
        self.title_bar.toggleSidebarRequested.connect(self.toggle_sidebar)
        self.title_bar.togglePreviewRequested.connect(self.toggle_preview)
        self.nav.toggleRequested.connect(self.toggle_sidebar)
        self.title_bar.connect_shortcuts(self)
        self.title_bar.connect_search_palette(self)
        self.nav.pageChanged.connect(self._on_page_changed)
        self.nav.set_current_index(0)
        self._sidebar_visible = True
        self._preview_visible = True
        self._quick_panel_visible = False
        self._update_window_title()

        self._ensure_page(0)
        self.stack.setCurrentIndex(0)
        self._apply_preview_visibility(0)

    def _on_page_changed(self, index: int):
        self._ensure_page(index)
        self.stack.setCurrentIndex(index)
        if index not in _PAGES_WITHOUT_PREVIEW:
            self._quick_panel_visible = False
        self._apply_preview_visibility(index)

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
            page = _PAGE_FACTORIES[index](self)
            self._page_widgets[index] = page
            self.stack.removeWidget(self.stack.widget(index))
            self.stack.insertWidget(index, page)
        except Exception:
            pass

    @property
    def calculator_page(self) -> QWidget | None:
        idx = 2
        self._ensure_page(idx)
        return self._page_widgets[idx]

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

    def set_traffic_count_rows(self, rows: list[list]) -> None:
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        traffic_state["traffic_count_rows"] = rows
        self._apply_traffic_count_rows(rows)

    def set_traffic_excel_data(self, data: dict) -> None:
        """Store temporary traffic investigation data for the current app session."""
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        traffic_state.update(data)
        count_hour = data.get("traffic_count_hour", "12h")
        daily_totals = data.get("daily_totals")
        summary_total_row = data.get("summary_total_row")
        aadt_pcu_result = compute_aadt_pcu(
            daily_totals,
            count_hour=count_hour,
            summary_total_row=summary_total_row,
        )
        traffic_state["aadt_pcu"] = {
            "total_aadt": aadt_pcu_result.total_aadt,
            "total_pcu": aadt_pcu_result.total_pcu,
        }
        self._apply_traffic_summary(
            data.get("traffic_count_rows", []),
            summary_total_row,
            aadt_pcu_result,
        )

    def refresh_traffic_summary(self, count_hour: str) -> None:
        """Recalculate summary table totals when Traffic Count Hour changes."""
        traffic_state = self.calc_state.setdefault("traffic_analysis", {})
        daily_totals = traffic_state.get("daily_totals")
        if not daily_totals:
            return
        summary_total_row = build_summary_total_row(daily_totals, count_hour=count_hour)
        traffic_state["summary_total_row"] = summary_total_row
        traffic_state["traffic_count_hour"] = count_hour
        aadt_pcu_result = compute_aadt_pcu(daily_totals, count_hour=count_hour)
        traffic_state["aadt_pcu"] = {
            "total_aadt": aadt_pcu_result.total_aadt,
            "total_pcu": aadt_pcu_result.total_pcu,
        }
        self._apply_traffic_summary(
            traffic_state.get("traffic_count_rows", []),
            summary_total_row,
            aadt_pcu_result,
        )

    def _apply_traffic_summary(
        self,
        rows: list[list],
        summary_total_row: list | None,
        aadt_pcu_result: AadtPcuResult | None = None,
    ) -> None:
        self._ensure_page(1)
        detail_page = self._page_widgets[1]
        if detail_page is not None and hasattr(detail_page, "set_traffic_count_rows"):
            detail_page.set_traffic_count_rows(rows, summary_total_row=summary_total_row)
        if detail_page is not None and hasattr(detail_page, "set_aadt_pcu_result"):
            if aadt_pcu_result is None and summary_total_row:
                aadt_pcu_result = compute_aadt_pcu(summary_total_row=summary_total_row)
            detail_page.set_aadt_pcu_result(aadt_pcu_result)

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
        self._apply_traffic_summary([], None, AadtPcuResult((), 0, 0))
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
            QMessageBox.information(self, "Export PDF", f"Saved: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Export failed", str(e))
        finally:
            if image_path and Path(image_path).exists():
                try:
                    Path(image_path).unlink()
                except Exception:
                    pass
