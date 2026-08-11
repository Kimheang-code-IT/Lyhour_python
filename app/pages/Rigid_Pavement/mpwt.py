"""Rigid Pavement > MPWT design page content."""
from __future__ import annotations

import math

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.theme import theme_tokens
from app.data.mpwt_rigid import (
    PAVEMENT_TYPE_OPTIONS,
    RELIABILITY_OPTIONS,
    SHOULDER_OPTIONS,
    SUBBASE_MATERIAL_OPTIONS,
    compute_mpwt_rigid,
    effective_subgrade_strength,
)
from app.pages.Rigid_Pavement.common import (
    BLOCK_SPACING,
    ROW_HEIGHT,
    labeled_value_row,
    section_frame,
    set_input_height,
    value_box,
)
from app.widgets.form_controls import make_combo, make_double_spin
from app.widgets.labeled_input import add_labeled_row
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content


class MpwtRigidPanel(QWidget):
    """MPWT: Input Parameter → Analysis & Result → Reinforcement Design."""

    inputs_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._updating_effective = False
        self._ready = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        fit_scroll_content(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)
        layout.addWidget(self._build_input_block())
        layout.addWidget(self._build_analysis_block())
        layout.addWidget(self._build_reinforcement_block())
        layout.addStretch(0)

        scroll.setWidget(content)
        configure_page_scroll(scroll)
        outer.addWidget(scroll, 1)
        self._ready = True
        self._auto_effective()
        self._refresh()

    def connect_inputs_changed(self, callback) -> None:
        self.inputs_changed.connect(callback)

    def quick_results(self) -> dict[str, str]:
        r = self._current_result()
        return {
            "Trial thickness": f"{r.trial_thickness_mm:,.0f} mm",
            "Minimum thickness": f"{r.minimum_thickness_mm:,.0f} mm",
            "Fatigue damage": f"{r.fatigue_damage_percent:,.2f} %",
            "Erosion damage": f"{r.erosion_damage_percent:,.2f} %",
            "Design status": r.status_text,
        }

    def _make_spin(self, *, value: float, decimals: int = 2, minimum: float = 0.0, maximum: float = 1e6, suffix: str = ""):
        spin = make_double_spin()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setValue(value)
        if suffix:
            spin.setSuffix(suffix)
        set_input_height(spin)
        spin.valueChanged.connect(self._on_changed)
        return spin

    def _make_combo(self, items: tuple[str, ...], current: str):
        combo = make_combo(list(items))
        set_input_height(combo)
        idx = combo.findText(current)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentTextChanged.connect(self._on_changed)
        return combo

    def _build_input_block(self) -> QFrame:
        frame, layout = section_frame("1. Input Parameter")
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        self.reliability_combo = self._make_combo(RELIABILITY_OPTIONS, "90%")
        self.subgrade_spin = self._make_spin(value=4.0, decimals=2, minimum=0.01, maximum=100.0)
        self.subbase_thickness_spin = self._make_spin(
            value=150.0, decimals=0, minimum=0.0, maximum=1000.0, suffix=" mm"
        )
        self.subbase_material_combo = self._make_combo(SUBBASE_MATERIAL_OPTIONS, "Granular")
        self.effective_spin = self._make_spin(value=4.0, decimals=2, minimum=0.01, maximum=200.0)
        self.shoulder_combo = self._make_combo(SHOULDER_OPTIONS, "Yes")
        self.pavement_type_combo = self._make_combo(PAVEMENT_TYPE_OPTIONS, "CRCP")
        self.concrete_strength_spin = self._make_spin(
            value=4.5, decimals=2, minimum=0.1, maximum=20.0, suffix=" MPa"
        )
        self.trial_thickness_spin = self._make_spin(
            value=200.0, decimals=0, minimum=50.0, maximum=800.0, suffix=" mm"
        )

        row = 0
        add_labeled_row(grid, row, "Project Design Reliability =", self.reliability_combo, ROW_HEIGHT)
        row += 1
        add_labeled_row(grid, row, "Design Subgrade Strength =", self.subgrade_spin, ROW_HEIGHT)
        row += 1

        subbase_row = QWidget()
        subbase_layout = QHBoxLayout(subbase_row)
        subbase_layout.setContentsMargins(0, 0, 0, 0)
        subbase_layout.setSpacing(16)
        left = QWidget()
        left_grid = QGridLayout(left)
        left_grid.setContentsMargins(0, 0, 0, 0)
        add_labeled_row(left_grid, 0, "Subbase Thickness =", self.subbase_thickness_spin, ROW_HEIGHT)
        right = QWidget()
        right_grid = QGridLayout(right)
        right_grid.setContentsMargins(0, 0, 0, 0)
        add_labeled_row(right_grid, 0, "Subbase Material =", self.subbase_material_combo, ROW_HEIGHT)
        subbase_layout.addWidget(left, 1)
        subbase_layout.addWidget(right, 1)
        grid.addWidget(subbase_row, row, 0, 1, 2)
        row += 1

        add_labeled_row(grid, row, "Effective Subgrade Strength =", self.effective_spin, ROW_HEIGHT)
        row += 1
        add_labeled_row(grid, row, "Use Shoulder =", self.shoulder_combo, ROW_HEIGHT)
        row += 1
        add_labeled_row(grid, row, "Concrete Pavement Type =", self.pavement_type_combo, ROW_HEIGHT)
        row += 1
        add_labeled_row(grid, row, "Concrete Strength =", self.concrete_strength_spin, ROW_HEIGHT)
        row += 1
        add_labeled_row(
            grid, row, "Trial Concrete Pavement Thickness =", self.trial_thickness_spin, ROW_HEIGHT
        )
        grid.setColumnStretch(1, 1)

        # Auto-fill effective strength when upstream inputs change.
        self.subgrade_spin.valueChanged.connect(self._auto_effective)
        self.subbase_thickness_spin.valueChanged.connect(self._auto_effective)
        self.subbase_material_combo.currentTextChanged.connect(self._auto_effective)

        layout.addWidget(grid_host)
        return frame

    def _build_analysis_block(self) -> QFrame:
        frame, layout = section_frame("2. Analysis & Result")
        layout.setSpacing(18)

        self.trial_value = value_box()
        self.min_value = value_box()
        self.fatigue_value = value_box()
        self.erosion_value = value_box()

        layout.addLayout(labeled_value_row("Base thickness (mm):", self.trial_value))
        layout.addLayout(
            labeled_value_row("Minimum Design Base thickness (mm):", self.min_value)
        )

        damage_row = QHBoxLayout()
        damage_row.setSpacing(40)
        fatigue_col = QHBoxLayout()
        fatigue_col.setSpacing(12)
        fatigue_caption = QLabel("Total fatigue:")
        fatigue_caption.setStyleSheet("color: #dddddd; font-weight: 700;")
        fatigue_col.addWidget(fatigue_caption)
        fatigue_col.addWidget(self.fatigue_value)
        fatigue_col.addStretch()

        erosion_col = QHBoxLayout()
        erosion_col.setSpacing(12)
        erosion_caption = QLabel("Total erosion damage:")
        erosion_caption.setStyleSheet("color: #dddddd; font-weight: 700;")
        erosion_col.addWidget(erosion_caption)
        erosion_col.addWidget(self.erosion_value)
        erosion_col.addStretch()

        damage_row.addLayout(fatigue_col, 1)
        damage_row.addLayout(erosion_col, 1)
        layout.addLayout(damage_row)
        return frame

    def _build_reinforcement_block(self) -> QFrame:
        frame, layout = section_frame("3. Reinforcement Design")
        note = QLabel(
            "Prepare reinforcement inputs for later calculation: reinforcement type, "
            "steel area, bar diameter / spacing, longitudinal & transverse reinforcement, "
            "reinforcement ratio, and joint information."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #999999;")
        layout.addWidget(note)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        self.reinf_type_combo = self._make_combo(
            ("Deformed bar", "Wire mesh", "CRCP steel"), "Deformed bar"
        )
        self.bar_diameter_spin = self._make_spin(
            value=16.0, decimals=1, minimum=6.0, maximum=40.0, suffix=" mm"
        )
        self.bar_spacing_spin = self._make_spin(
            value=200.0, decimals=0, minimum=50.0, maximum=500.0, suffix=" mm"
        )
        self.long_ratio_spin = self._make_spin(
            value=0.60, decimals=2, minimum=0.0, maximum=5.0, suffix=" %"
        )
        self.trans_ratio_spin = self._make_spin(
            value=0.20, decimals=2, minimum=0.0, maximum=5.0, suffix=" %"
        )
        self.steel_area_label = QLabel("—")
        self.steel_area_label.setStyleSheet(
            f"color: {theme_tokens().accent}; font-weight: 700;"
        )

        add_labeled_row(grid, 0, "Reinforcement type =", self.reinf_type_combo, ROW_HEIGHT)
        add_labeled_row(grid, 1, "Bar diameter =", self.bar_diameter_spin, ROW_HEIGHT)
        add_labeled_row(grid, 2, "Bar spacing =", self.bar_spacing_spin, ROW_HEIGHT)
        add_labeled_row(grid, 3, "Longitudinal reinforcement ratio =", self.long_ratio_spin, ROW_HEIGHT)
        add_labeled_row(grid, 4, "Transverse reinforcement ratio =", self.trans_ratio_spin, ROW_HEIGHT)
        add_labeled_row(grid, 5, "Steel reinforcement area =", self.steel_area_label, ROW_HEIGHT)
        grid.setColumnStretch(1, 1)
        layout.addWidget(grid_host)
        return frame

    def _auto_effective(self, *_args) -> None:
        if self._updating_effective:
            return
        value = effective_subgrade_strength(
            design_subgrade_strength=float(self.subgrade_spin.value()),
            subbase_thickness_mm=float(self.subbase_thickness_spin.value()),
            subbase_material=self.subbase_material_combo.currentText(),
        )
        self._updating_effective = True
        try:
            self.effective_spin.setValue(value)
        finally:
            self._updating_effective = False

    def _on_changed(self, *_args) -> None:
        if not self._ready:
            return
        self._refresh()
        self.inputs_changed.emit()

    def _current_result(self):
        return compute_mpwt_rigid(
            reliability=self.reliability_combo.currentText(),
            design_subgrade_strength=float(self.subgrade_spin.value()),
            subbase_thickness_mm=float(self.subbase_thickness_spin.value()),
            subbase_material=self.subbase_material_combo.currentText(),
            effective_subgrade_strength_override=float(self.effective_spin.value()),
            use_shoulder=self.shoulder_combo.currentText(),
            pavement_type=self.pavement_type_combo.currentText(),
            concrete_strength=float(self.concrete_strength_spin.value()),
            trial_thickness_mm=float(self.trial_thickness_spin.value()),
        )

    def _refresh(self) -> None:
        if not self._ready:
            return
        r = self._current_result()
        self.trial_value.setText(f"{r.trial_thickness_mm:,.0f}")
        self.min_value.setText(f"{r.minimum_thickness_mm:,.0f}")
        self.fatigue_value.setText(f"{r.fatigue_damage_percent:,.2f}%")
        self.erosion_value.setText(f"{r.erosion_damage_percent:,.2f}%")

        # Approximate steel area from diameter & spacing (mm²/m).
        dia = float(self.bar_diameter_spin.value())
        spacing = max(float(self.bar_spacing_spin.value()), 1.0)
        area = (math.pi * (dia / 2.0) ** 2) * (1000.0 / spacing)
        self.steel_area_label.setText(f"{area:,.1f} mm²/m")
