"""
Left nav tree; icons + expand/collapse arrows (down/right)
- Arrow priority: app/assets -> FluentIcon -> QApplication style -> drawn fallback
- Main parent folders ALWAYS show expand/collapse arrow
- Windows-safe URI for QSS url()
"""

import tempfile
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QSizePolicy,
    QStyle,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPolygonF

# From app/widgets, assets are at app/assets
_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_ARROW_DOWN_ASSET = _ASSETS / "arrow-down.png"
_ARROW_RIGHT_ASSET = _ASSETS / "arrow-right.png"

try:
    import qtawesome as qta  # type: ignore[import-untyped]
    _HAS_QTAWESOME = True
except Exception:
    qta = None  # type: ignore[assignment]
    _HAS_QTAWESOME = False

try:
    from qfluentwidgets import FluentIcon, Theme  # type: ignore[import-untyped]
    _HAS_FLUENT = True
except Exception:
    FluentIcon = None  # type: ignore[assignment]
    Theme = None  # type: ignore[assignment]
    _HAS_FLUENT = False

_CACHE_DIR = Path(tempfile.gettempdir()) / "Win_UI_sidebar_cache"
_ARROW_SIZE = 14


def _draw_arrow_pixmap(down: bool) -> QPixmap:
    """Draw a simple white arrow (down or right) onto a transparent pixmap."""
    pm = QPixmap(_ARROW_SIZE, _ARROW_SIZE)
    pm.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(255, 255, 255), 2))
    painter.setBrush(QBrush(QColor(255, 255, 255)))

    s = _ARROW_SIZE
    if down:
        poly = QPolygonF([QPointF(s / 2, s - 4), QPointF(4, 6), QPointF(s - 4, 6)])
    else:
        poly = QPolygonF([QPointF(s - 4, s / 2), QPointF(6, 4), QPointF(6, s - 4)])

    painter.drawPolygon(poly)
    painter.end()
    return pm


def _safe_asset_uri(path: Path) -> str:
    """Windows-safe URI for stylesheet url()."""
    if not path.exists():
        return ""
    try:
        return path.resolve().as_uri()
    except Exception:
        return ""


def _ensure_branch_icons() -> tuple[Path, Path]:
    """
    Return local file paths (down_path, right_path) for tree branch icons.
    Creates PNGs if needed in temp cache.
    """
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    down_path = (_CACHE_DIR / "branch_down.png").resolve()
    right_path = (_CACHE_DIR / "branch_right.png").resolve()

    def _save_icon(icon: QIcon, path: Path) -> bool:
        pm = icon.pixmap(_ARROW_SIZE, _ARROW_SIZE)
        if not pm.isNull() and not pm.size().isEmpty():
            return pm.save(str(path))
        return False

    # 1) FluentIcon CHEVRON_DOWN / CHEVRON_RIGHT
    if _HAS_FLUENT:
        try:
            icon_down = FluentIcon.CHEVRON_DOWN.icon(theme=Theme.DARK)
            icon_right = FluentIcon.CHEVRON_RIGHT.icon(theme=Theme.DARK)
            _save_icon(icon_down, down_path)
            _save_icon(icon_right, right_path)
        except Exception:
            pass

    # 2) QApplication style fallback (no QStyle() standalone)
    if not down_path.exists() or not right_path.exists():
        app = QApplication.instance()
        style = app.style() if app else None
        if style is not None:
            try:
                _save_icon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowDown), down_path)
                _save_icon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight), right_path)
            except Exception:
                pass

    # 3) Draw arrow pixmap fallback
    if not down_path.exists():
        _draw_arrow_pixmap(True).save(str(down_path))
    if not right_path.exists():
        _draw_arrow_pixmap(False).save(str(right_path))

    return down_path, right_path


class SidebarLeft(QFrame):
    """Left nav tree; emits pageChanged(int) and toggleRequested."""

    pageChanged = pyqtSignal(int)
    toggleRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navPanel")

        # Arrow priority:
        # 1) app/assets arrows
        # 2) FluentIcon / Qt style / drawn fallback (cached in temp)
        arrow_down_url = _safe_asset_uri(_ARROW_DOWN_ASSET)
        arrow_right_url = _safe_asset_uri(_ARROW_RIGHT_ASSET)

        if not arrow_down_url or not arrow_right_url:
            down_path, right_path = _ensure_branch_icons()
            if not arrow_down_url:
                arrow_down_url = _safe_asset_uri(down_path)
            if not arrow_right_url:
                arrow_right_url = _safe_asset_uri(right_path)

        branch_closed_css = f"image: url({arrow_right_url});" if arrow_right_url else "image: none;"
        branch_open_css = f"image: url({arrow_down_url});" if arrow_down_url else "image: none;"

        # Background like Topbar_nav
        self.setStyleSheet(f"""
            #navPanel {{
                background-color: #252526;
                border: none;
                border-right: 1px solid #3e3e40;
            }}
            QTreeWidget {{
                background: transparent;
                color: #ffffff;
                border: none;
                outline: none;
                padding: 2px 0;
                font-size: 15px;
            }}
            QTreeWidget::item {{
                padding: 4px 12px;
                height: 28px;
                border: none;
                color: #ffffff;
            }}
            QTreeWidget::item:hover {{
                background-color: #3e3e40;
                color: #ffffff;
            }}
            QTreeWidget::item:selected {{
                background-color: #3e3e40;
                color: #ffffff;
            }}

            /* Branch arrows (parents) */
            QTreeWidget::branch:closed:has-children {{
                border-image: none;
                {branch_closed_css}
                margin-left: 4px;
                width: {_ARROW_SIZE}px;
                height: {_ARROW_SIZE}px;
            }}
            QTreeWidget::branch:open:has-children {{
                border-image: none;
                {branch_open_css}
                margin-left: 4px;
                width: {_ARROW_SIZE}px;
                height: {_ARROW_SIZE}px;
            }}
            QTreeWidget::branch:!has-children {{
                image: none;
                width: 0;
                min-width: 0;
            }}
        """)

        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)

        # IMPORTANT: force arrows on parent folders
        self.tree.setItemsExpandable(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setExpandsOnDoubleClick(True)

        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setIconSize(QSize(18, 18))

        # Icons: Fluent -> qtawesome -> QStyle fallback
        app = QApplication.instance()
        style = app.style() if app else None

        icon_folder = QIcon()
        icon_file = QIcon()

        if _HAS_FLUENT:
            try:
                icon_folder = FluentIcon.FOLDER.icon(theme=Theme.DARK)
                icon_file = FluentIcon.DOCUMENT.icon(theme=Theme.DARK)
            except Exception:
                icon_folder = QIcon()
                icon_file = QIcon()

        if (icon_folder.isNull() or icon_file.isNull()) and _HAS_QTAWESOME:
            try:
                icon_folder = qta.icon("fa5s.folder", color="#ffffff")
                icon_file = qta.icon("fa5s.file-alt", color="#ffffff")
            except Exception:
                pass

        if (icon_folder.isNull() or icon_file.isNull()) and style is not None:
            if icon_folder.isNull():
                icon_folder = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            if icon_file.isNull():
                icon_file = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)

        # ----- Tree Items -----
        # Chevron icon for parent nodes (always white, real icon)
        chevron_icon = QIcon()
        if _HAS_FLUENT:
            try:
                chevron_icon = FluentIcon.CHEVRON_DOWN.icon(color="#ffffff", theme=Theme.DARK)
            except Exception:
                chevron_icon = QIcon()
        if chevron_icon.isNull() and _HAS_QTAWESOME:
            try:
                chevron_icon = qta.icon("fa5s.chevron-down", color="#ffffff")
            except Exception:
                chevron_icon = QIcon()
        if chevron_icon.isNull():
            pm = _draw_arrow_pixmap(True)
            chevron_icon = QIcon(pm)

        traffic_parent = QTreeWidgetItem(self.tree, ["Traffic Analysis"])
        traffic_parent.setIcon(0, icon_folder)
        traffic_parent.setIcon(1, chevron_icon)
        traffic_parent.setExpanded(True)
        traffic_parent.setData(0, Qt.ItemDataRole.UserRole, -1)
        traffic_parent.setChildIndicatorPolicy(
            QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
        )

        sub = QTreeWidgetItem(traffic_parent, ["Input"])
        sub.setIcon(0, icon_file)
        sub.setData(0, Qt.ItemDataRole.UserRole, 0)

        sub = QTreeWidgetItem(traffic_parent, ["Detail Result"])
        sub.setIcon(0, icon_file)
        sub.setData(0, Qt.ItemDataRole.UserRole, 1)

        rgd_parent = QTreeWidgetItem(self.tree, ["Road Geometry Design"])
        rgd_parent.setIcon(0, icon_folder)
        rgd_parent.setIcon(1, chevron_icon)
        rgd_parent.setExpanded(True)
        rgd_parent.setData(0, Qt.ItemDataRole.UserRole, -1)
        rgd_parent.setChildIndicatorPolicy(
            QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
        )

        sub = QTreeWidgetItem(rgd_parent, ["Horizontal Curvature"])
        sub.setIcon(0, icon_file)
        sub.setData(0, Qt.ItemDataRole.UserRole, 2)

        sub = QTreeWidgetItem(rgd_parent, ["Superelevation Design"])
        sub.setIcon(0, icon_file)
        sub.setData(0, Qt.ItemDataRole.UserRole, 3)

        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree, 1)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        page_index = item.data(0, Qt.ItemDataRole.UserRole)
        if page_index is not None and int(page_index) >= 0:
            self.pageChanged.emit(int(page_index))

    def set_current_index(self, index: int):
        def find_leaf(parent_item: QTreeWidgetItem, idx: int):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if child.data(0, Qt.ItemDataRole.UserRole) == idx:
                    return child
                found = find_leaf(child, idx)
                if found:
                    return found
            return None

        for i in range(self.tree.topLevelItemCount()):
            item = find_leaf(self.tree.topLevelItem(i), index)
            if item:
                self.tree.setCurrentItem(item)
                break