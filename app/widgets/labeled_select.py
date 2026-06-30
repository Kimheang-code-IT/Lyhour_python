"""Reusable label + ComboBox row using native QComboBox (so dropdown arrow shows) and qfluentwidgets BodyLabel when available."""
from pathlib import Path

from PyQt6.QtWidgets import QComboBox, QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

# From app/widgets, icon assets are at app/assets/icon
_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "icon"
_ARROW_DOWN_ASSET = _ASSETS / "arrow-down.png"

try:
    from qfluentwidgets import BodyLabel  # type: ignore[import-untyped]
    _HAS_FLUENT = True
except ImportError:
    _HAS_FLUENT = False

DESIGN_YEAR_OPTIONS = [5, 10, 15, 20, 25, 30, 35, 40]


def _combo_dropdown_arrow_style() -> str:
    """Stylesheet to use app/assets/icon/arrow-down.png as ComboBox dropdown arrow."""
    if not _ARROW_DOWN_ASSET.exists():
        return ""
    try:
        url = _ARROW_DOWN_ASSET.resolve().as_uri()
    except Exception:
        url = _ARROW_DOWN_ASSET.as_uri()
    return f"""
        QComboBox::down-arrow {{
            image: url({url});
            width: 16px;
            height: 16px;
        }}
    """


def _make_label(text: str, row_height: int):
    if _HAS_FLUENT:
        lbl = BodyLabel(text)
    else:
        lbl = QLabel(text)
    lbl.setFixedHeight(row_height)
    lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return lbl


def add_labeled_select_row(grid, row: int, label_text: str, combo, row_height: int = 36) -> None:
    """Add a label (col 0) and combo (col 1) to grid. Uses arrow-down.png for dropdown arrow when available."""
    combo.setMinimumHeight(row_height)
    combo.setMaximumHeight(row_height)
    arrow_style = _combo_dropdown_arrow_style()
    if arrow_style:
        combo.setStyleSheet((combo.styleSheet() or "") + arrow_style)
    lbl = _make_label(label_text, row_height)
    grid.addWidget(lbl, row, 0)
    grid.addWidget(combo, row, 1)


def make_design_year_combo() -> QComboBox:
    """Create a reusable design-year select with 5-year interval options."""
    combo = QComboBox()
    combo.addItems([f"{year} year" for year in DESIGN_YEAR_OPTIONS])
    return combo


class LabeledSelect(QWidget):
    """Single row: label + native QComboBox (dropdown arrow from theme/assets). BodyLabel for label when Fluent available."""

    def __init__(self, label_text: str, combo=None, row_height: int = 36, parent=None):
        super().__init__(parent)
        if combo is None:
            combo = QComboBox()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        combo.setMinimumHeight(row_height)
        combo.setMaximumHeight(row_height)
        arrow_style = _combo_dropdown_arrow_style()
        if arrow_style:
            combo.setStyleSheet((combo.styleSheet() or "") + arrow_style)
        lbl = _make_label(label_text, row_height)
        layout.addWidget(lbl)
        layout.addWidget(combo, 1)
        self._combo = combo

    @property
    def combo(self):
        return self._combo
