"""Flexible Pavement thickness / SN panel (shown on the AASHTO tab)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.theme import theme_tokens
from app.core.ui_scale import UiScale
from app.data.mpwt_thickness import compute_mpwt_thickness
from app.pages.Flexible_Pavement.common import (
    BLOCK_SPACING,
    ROW_HEIGHT,
    section_frame,
    set_input_height,
)
from app.widgets.form_controls import make_double_spin
from app.widgets.labeled_input import add_labeled_row

try:
    from qfluentwidgets import BodyLabel
except ImportError:
    BodyLabel = QLabel  # type: ignore[misc,assignment]

# Matches spreadsheet example defaults.
_DEFAULT_REQUIRED_SN = 4.73
_DEFAULT_A1 = 0.3056
_DEFAULT_A2 = 0.1947
_DEFAULT_A3 = 0.174
_DEFAULT_M2 = 0.8
_DEFAULT_M3 = 0.8
_DEFAULT_H1 = 9.0
_DEFAULT_H2 = 35.0
_DEFAULT_H3 = 30.0
_DEFAULT_AASHTO_HMA_MIN_CM = 8.9
_DEFAULT_AASHTO_BASE_MIN_CM = 15.0
_DEFAULT_JAPAN_HMA_MIN_CM = 8.9
_DEFAULT_JAPAN_BASE_MIN_CM = 20.0

_EQ_HTML = (
    "<div style='color:#cccccc; font-size:12pt; line-height:1.45;'>"
    "<b>Principle equation (AASHTO 1993)</b><br/>"
    "log W<sub>18</sub> = Z<sub>R</sub>·S<sub>0</sub> "
    "+ 9.36·log(SN+1) − 0.20 "
    "+ log{(p<sub>0</sub>−p<sub>t</sub>)/(4.2−1.5)} "
    "/ [0.4 + 1094/(SN+1)<sup>5.19</sup>] "
    "+ 2.32·log M<sub>R</sub> − 8.07"
    "</div>"
)


class ThicknessSnPanel(QWidget):
    """Sections 3.1–3.3: structural/drainage coeffs, min thickness, layer SN check."""

    inputs_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._ready = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(BLOCK_SPACING)
        layout.addWidget(self._build_section_31())
        layout.addWidget(self._build_section_32())
        layout.addWidget(self._build_section_33())

        self._ready = True
        self._refresh()

    def connect_inputs_changed(self, callback) -> None:
        self.inputs_changed.connect(callback)

    def quick_results(self) -> dict[str, str]:
        r = self._current_result()
        results = {
            "Required SN": f"{r.required_sn:.2f}" if r.required_sn is not None else "—",
            "Total SN": f"{r.total_sn:.2f}",
            "HMA h1": f"{self.h1_spin.value():.2f} cm",
            "Base h2": f"{self.h2_spin.value():.2f} cm",
            "Subbase h3": f"{self.h3_spin.value():.2f} cm",
        }
        if r.design_ok is True:
            results["Design check"] = "OK"
        elif r.design_ok is False:
            results["Design check"] = "NG"
        else:
            results["Design check"] = "—"
        return results

    def get_inputs(self) -> dict[str, float]:
        return {
            "required_sn": float(self.required_sn_spin.value()),
            "a1": float(self.a1_spin.value()),
            "a2": float(self.a2_spin.value()),
            "a3": float(self.a3_spin.value()),
            "m2": float(self.m2_spin.value()),
            "m3": float(self.m3_spin.value()),
            "h1_cm": float(self.h1_spin.value()),
            "h2_cm": float(self.h2_spin.value()),
            "h3_cm": float(self.h3_spin.value()),
            "aashto_hma_min_cm": float(self.aashto_hma_min_spin.value()),
            "aashto_base_min_cm": float(self.aashto_base_min_spin.value()),
            "japan_hma_min_cm": float(self.japan_hma_min_spin.value()),
            "japan_base_min_cm": float(self.japan_base_min_spin.value()),
        }

    def _current_result(self):
        inputs = self.get_inputs()
        return compute_mpwt_thickness(
            a1=inputs["a1"],
            a2=inputs["a2"],
            a3=inputs["a3"],
            m2=inputs["m2"],
            m3=inputs["m3"],
            h1_cm=inputs["h1_cm"],
            h2_cm=inputs["h2_cm"],
            h3_cm=inputs["h3_cm"],
            required_sn=inputs["required_sn"],
        )

    def _notify(self, *_args) -> None:
        if not self._ready:
            return
        self._refresh()
        self.inputs_changed.emit()

    def _make_spin(
        self,
        *,
        value: float,
        decimals: int = 2,
        minimum: float = 0.0,
        maximum: float = 1e6,
        suffix: str = "",
    ):
        spin = make_double_spin()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setValue(value)
        if suffix:
            spin.setSuffix(suffix)
        set_input_height(spin)
        spin.valueChanged.connect(self._notify)
        return spin

    def _value_label(self) -> QLabel:
        label = BodyLabel("—")
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        accent = theme_tokens().accent
        label.setStyleSheet(f"color: {accent}; font-weight: 700;")
        return label

    def _body_label(self, text: str, *, bold: bool = False) -> QLabel:
        """Same label style as section 3.1 (`add_labeled_row` / BodyLabel)."""
        label = BodyLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if bold:
            label.setStyleSheet("font-weight: 600;")
        return label

    def _build_section_31(self) -> QFrame:
        frame, layout = section_frame("3.1 Structural and Drainage Coefficients")

        sides = QHBoxLayout()
        sides.setSpacing(BLOCK_SPACING)
        sides.addWidget(self._build_structural_coeff_side(), 1)
        sides.addWidget(self._build_drainage_coeff_side(), 1)
        layout.addLayout(sides)
        return frame

    def _side_panel(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        panel = QFrame()
        panel.setObjectName("mpwtCoeffSide")
        panel.setStyleSheet(
            "#mpwtCoeffSide { background-color: transparent; "
            "border: 1px solid #3e3e40; border-radius: 6px; }"
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 10, 12, 12)
        panel_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #e0e0e0; font-weight: 700; font-size: 14px;")
        panel_layout.addWidget(title_label)
        return panel, panel_layout

    def _build_structural_coeff_side(self) -> QFrame:
        panel, panel_layout = self._side_panel("Structural Coefficients")

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        self.a1_spin = self._make_spin(
            value=_DEFAULT_A1, decimals=4, minimum=0.0, maximum=2.0
        )
        self.a2_spin = self._make_spin(
            value=_DEFAULT_A2, decimals=4, minimum=0.0, maximum=2.0
        )
        self.a3_spin = self._make_spin(
            value=_DEFAULT_A3, decimals=4, minimum=0.0, maximum=2.0
        )
        add_labeled_row(grid, 0, "a₁ =", self.a1_spin, ROW_HEIGHT)
        add_labeled_row(grid, 1, "a₂ =", self.a2_spin, ROW_HEIGHT)
        add_labeled_row(grid, 2, "a₃ =", self.a3_spin, ROW_HEIGHT)
        grid.setColumnStretch(1, 1)

        panel_layout.addWidget(grid_host)
        panel_layout.addStretch()
        return panel

    def _build_drainage_coeff_side(self) -> QFrame:
        panel, panel_layout = self._side_panel("Drainage Coefficients")

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        self.m2_spin = self._make_spin(
            value=_DEFAULT_M2, decimals=2, minimum=0.0, maximum=2.0
        )
        self.m3_spin = self._make_spin(
            value=_DEFAULT_M3, decimals=2, minimum=0.0, maximum=2.0
        )
        add_labeled_row(grid, 0, "m₂ =", self.m2_spin, ROW_HEIGHT)
        add_labeled_row(grid, 1, "m₃ =", self.m3_spin, ROW_HEIGHT)
        grid.setColumnStretch(1, 1)

        panel_layout.addWidget(grid_host)
        panel_layout.addStretch()
        return panel

    def _build_section_32(self) -> QFrame:
        frame, layout = section_frame("3.2 Determination of Minimum Thickness")

        sides = QHBoxLayout()
        sides.setSpacing(BLOCK_SPACING)
        sides.addWidget(
            self._build_min_thickness_side(
                title="AASHTO 1993",
                hma_attr="aashto_hma_min_spin",
                base_attr="aashto_base_min_spin",
                hma_default=_DEFAULT_AASHTO_HMA_MIN_CM,
                base_default=_DEFAULT_AASHTO_BASE_MIN_CM,
            ),
            1,
        )
        sides.addWidget(
            self._build_min_thickness_side(
                title="Japan Standard / Practical Application",
                hma_attr="japan_hma_min_spin",
                base_attr="japan_base_min_spin",
                hma_default=_DEFAULT_JAPAN_HMA_MIN_CM,
                base_default=_DEFAULT_JAPAN_BASE_MIN_CM,
            ),
            1,
        )

        eq = QLabel(_EQ_HTML)
        eq.setTextFormat(Qt.TextFormat.RichText)
        eq.setWordWrap(True)

        layout.addLayout(sides)
        layout.addWidget(eq)
        return frame

    def _build_min_thickness_side(
        self,
        *,
        title: str,
        hma_attr: str,
        base_attr: str,
        hma_default: float,
        base_default: float,
    ) -> QFrame:
        panel = QFrame()
        panel.setObjectName("mpwtMinThicknessSide")
        panel.setStyleSheet(
            "#mpwtMinThicknessSide { background-color: transparent; "
            "border: 1px solid #3e3e40; border-radius: 6px; }"
        )
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 10, 12, 12)
        panel_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #e0e0e0; font-weight: 700; font-size: 14px;")
        panel_layout.addWidget(title_label)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        hma_spin = self._make_spin(
            value=hma_default, decimals=1, minimum=0.0, maximum=200.0, suffix=" cm"
        )
        base_spin = self._make_spin(
            value=base_default, decimals=1, minimum=0.0, maximum=200.0, suffix=" cm"
        )
        setattr(self, hma_attr, hma_spin)
        setattr(self, base_attr, base_spin)

        add_labeled_row(grid, 0, "Minimum thickness of HMA =", hma_spin, ROW_HEIGHT)
        add_labeled_row(
            grid, 1, "Minimum thickness of granular base =", base_spin, ROW_HEIGHT
        )
        grid.setColumnStretch(1, 1)

        panel_layout.addWidget(grid_host)
        panel_layout.addStretch()
        return panel

    def _build_section_33(self) -> QFrame:
        frame, layout = section_frame("3.3 Determination of Required Thickness for Each Layer")

        req_host = QWidget()
        req_grid = QGridLayout(req_host)
        req_grid.setHorizontalSpacing(12)
        req_grid.setVerticalSpacing(14)
        req_grid.setContentsMargins(0, 0, 0, 0)
        self.required_sn_spin = self._make_spin(
            value=_DEFAULT_REQUIRED_SN, decimals=2, minimum=0.0, maximum=40.0
        )
        add_labeled_row(
            req_grid,
            0,
            "Calculate the required total Structural Number based on Eq. (1):",
            self.required_sn_spin,
            ROW_HEIGHT,
        )
        req_grid.setColumnStretch(1, 1)

        # Selected thicknesses → SN₁ / SN₂ / SN₃
        thick_host = QWidget()
        thick = QGridLayout(thick_host)
        thick.setHorizontalSpacing(10)
        thick.setVerticalSpacing(14)
        thick.setContentsMargins(0, 0, 0, 0)

        self.h1_spin = self._make_spin(
            value=_DEFAULT_H1, decimals=2, minimum=0.0, maximum=200.0, suffix=" cm"
        )
        self.h2_spin = self._make_spin(
            value=_DEFAULT_H2, decimals=2, minimum=0.0, maximum=200.0, suffix=" cm"
        )
        self.h3_spin = self._make_spin(
            value=_DEFAULT_H3, decimals=2, minimum=0.0, maximum=200.0, suffix=" cm"
        )
        self.sn1_label = self._value_label()
        self.sn2_label = self._value_label()
        self.sn3_label = self._value_label()

        layer_rows = (
            ("Selected HMA Thickness =", self.h1_spin, "Then  SN₁ =", self.sn1_label),
            ("Selected Base Thickness =", self.h2_spin, "Then  SN₂ =", self.sn2_label),
            ("Selected Subbase Thickness =", self.h3_spin, "Then  SN₃ =", self.sn3_label),
        )
        for r, (left_text, spin, then_text, sn_label) in enumerate(layer_rows):
            set_input_height(spin)
            thick.addWidget(self._body_label(left_text), r, 0)
            thick.addWidget(spin, r, 1)
            thick.addWidget(self._body_label(then_text), r, 2)
            thick.addWidget(sn_label, r, 3)
        thick.setColumnStretch(1, 1)
        thick.setColumnStretch(3, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3e3e40; background: #3e3e40; max-height: 1px;")

        total_row = QHBoxLayout()
        total_row.addWidget(
            self._body_label("Total SN from selected layer thickness =", bold=True)
        )
        self.total_sn_label = self._value_label()
        total_row.addWidget(self.total_sn_label)
        total_row.addStretch()

        # Verification subsection
        verify_panel, verify_layout = self._side_panel("Verification")
        verify_row = QHBoxLayout()
        self.check_caption = self._body_label("—", bold=True)
        self.check_caption.setWordWrap(True)
        self.status_label = BodyLabel("—")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumWidth(UiScale.px(64))
        self.status_label.setMinimumHeight(UiScale.px(32))
        self._apply_status_style(None)
        verify_row.addWidget(self.check_caption, 1)
        verify_row.addWidget(self.status_label, 0)
        verify_layout.addLayout(verify_row)

        layout.addWidget(req_host)
        layout.addWidget(thick_host)
        layout.addWidget(sep)
        layout.addLayout(total_row)
        layout.addWidget(verify_panel)
        return frame

    def _apply_status_style(self, ok: bool | None) -> None:
        if ok is True:
            self.status_label.setText("OK")
            self.status_label.setStyleSheet(
                "background-color: #2d6a9f; color: #ffffff; font-weight: 700; "
                "border-radius: 4px; padding: 4px 12px;"
            )
        elif ok is False:
            self.status_label.setText("NG")
            self.status_label.setStyleSheet(
                "background-color: #8b3a3a; color: #ffffff; font-weight: 700; "
                "border-radius: 4px; padding: 4px 12px;"
            )
        else:
            self.status_label.setText("—")
            self.status_label.setStyleSheet(
                "background-color: #3e3e40; color: #cccccc; font-weight: 700; "
                "border-radius: 4px; padding: 4px 12px;"
            )

    def _refresh(self) -> None:
        r = self._current_result()

        self.sn1_label.setText(f"{r.sn1:.2f}")
        self.sn2_label.setText(f"{r.sn2:.2f}")
        self.sn3_label.setText(f"{r.sn3:.2f}")
        self.total_sn_label.setText(f"{r.total_sn:.2f}")

        required = r.required_sn if r.required_sn is not None else 0.0
        if r.design_ok:
            compare_op = ">" if r.total_sn > required else "≥"
            self.check_caption.setText(
                f"Total SN from selected layer thickness = {r.total_sn:.2f} "
                f"{compare_op} {required:.2f} (the required total SN)  →  OK"
            )
        else:
            self.check_caption.setText(
                f"Total SN from selected layer thickness = {r.total_sn:.2f} "
                f"< {required:.2f} (the required total SN)  →  NG"
            )
        self._apply_status_style(r.design_ok)


class MpwtPage(QWidget):
    """MPWT tab placeholder — thickness design now lives on the AASHTO tab."""

    inputs_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        note = QLabel(
            "Thickness design (sections 3.1–3.3) is on the AASHTO tab.\n"
            "MPWT-specific catalog methods can be added here later."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #aaaaaa; font-size: 14px;")
        layout.addWidget(note)
        layout.addStretch()

    def connect_inputs_changed(self, callback) -> None:
        self.inputs_changed.connect(callback)

    def quick_results(self) -> dict[str, str]:
        return {}
