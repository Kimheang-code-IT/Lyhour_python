"""Rigid Pavement > AASHTO 1993 design page content (Excel ASSHTO93 layout)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.theme import theme_tokens
from app.core.ui_scale import UiScale
from app.data.aashto_resilient_modulus import MONTH_LABELS
from app.data.aashto_rigid import compute_aashto_rigid
from app.pages.Flexible_Pavement.common import (
    MODULUS_LABEL_COLUMN_WIDTH,
    configure_modulus_table,
    fit_modulus_table_height,
    layer_band,
    modulus_row_label,
    modulus_table_item,
    set_modulus_spin_height,
    thickness_marker,
)
from app.pages.Rigid_Pavement.common import (
    BLOCK_SPACING,
    ROW_HEIGHT,
    section_frame,
    set_input_height,
    value_box,
)
from app.widgets.form_controls import make_double_spin
from app.widgets.labeled_input import add_labeled_row
from app.widgets.scroll_utils import configure_page_scroll, fit_scroll_content

# Editable-field tint (Excel yellow cells, adapted for dark UI).
_INPUT_TINT = (
    "background-color: #3d3a28; border: 1px solid #c9a227; border-radius: 3px;"
)

_EQUATION_HTML = (
    "<div style='color:#cccccc; font-size:12px; line-height:1.45;'>"
    "<b>Eq. (1) — AASHTO 1993 rigid pavement:</b><br/>"
    "Log<sub>10</sub>W<sub>18</sub> = Z<sub>R</sub>·S<sub>0</sub> + 7.35·Log<sub>10</sub>(D+1) − 0.06 "
    "+ Log<sub>10</sub>[ΔPSI/(4.5−1.5)] / [1 + 1.624×10<sup>7</sup>/(D+1)<sup>8.46</sup>] "
    "+ (4.22 − 0.32·P<sub>t</sub>)·Log<sub>10</sub>"
    "{ [S′<sub>c</sub>·C<sub>d</sub>·(D<sup>0.75</sup>−1.132)] "
    "/ [215.63·J·(D<sup>0.75</sup> − 18.42/(E<sub>c</sub>/k)<sup>0.25</sup>)] }"
    "</div>"
)


class AashtoRigidPanel(QWidget):
    """AASHTO 1993 rigid pavement thickness design (Excel ASSHTO93 logic)."""

    inputs_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        layout.addWidget(self._build_given_block())
        layout.addWidget(self._build_modulus_block())
        layout.addWidget(self._build_thickness_block())
        layout.addStretch(0)

        scroll.setWidget(content)
        configure_page_scroll(scroll)
        outer.addWidget(scroll, 1)
        self._ready = True
        self._refresh()

    def connect_inputs_changed(self, callback) -> None:
        self.inputs_changed.connect(callback)

    def quick_results(self) -> dict[str, str]:
        r = self._current_result()
        out: dict[str, str] = {}
        if r.effective_k_pci is not None:
            out["Effective k"] = f"{r.effective_k_pci:,.2f} pci"
        if r.corrected_k_pci is not None:
            out["Corrected k"] = f"{r.corrected_k_pci:,.2f} pci"
        if r.dcal_cm is not None:
            out["Required thickness"] = f"{r.dcal_cm:,.2f} cm"
        if r.final_thickness_cm is not None:
            out["Final thickness"] = f"{r.final_thickness_cm} cm"
        if r.verification_ok is True:
            out["Verification"] = "OK"
        elif r.verification_ok is False:
            out["Verification"] = "NO"
        return out

    def _style_input(self, spin) -> None:
        existing = spin.styleSheet() or ""
        spin.setStyleSheet(f"{existing}; {_INPUT_TINT}" if existing else _INPUT_TINT)

    def _make_spin(
        self,
        *,
        value: float,
        decimals: int = 2,
        minimum: float = 0.0,
        maximum: float = 1e9,
        suffix: str = "",
        tint: bool = True,
    ):
        spin = make_double_spin()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setValue(value)
        if suffix:
            spin.setSuffix(suffix)
        set_input_height(spin)
        if tint:
            self._style_input(spin)
        spin.valueChanged.connect(self._on_changed)
        return spin

    def _param_pair(self, symbol: str, spin, unit: str = "") -> QWidget:
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        label = QLabel(symbol)
        label.setStyleSheet("color: #cccccc; font-weight: 600;")
        row.addWidget(label)
        row.addWidget(spin, 1)
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #cccccc; font-size: 13px;")
            row.addWidget(unit_label)
        return wrap

    def _layer_row(
        self,
        layer_name: str,
        band_color: str,
        left_widget: QWidget,
        right_widget: QWidget | None,
        thickness_label: str,
    ) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        row_layout.addWidget(layer_band(layer_name, band_color, min_height=48), 2)
        params = QHBoxLayout()
        params.setSpacing(10)
        params.addWidget(left_widget, 1)
        if right_widget is not None:
            params.addWidget(right_widget, 1)
        row_layout.addLayout(params, 3)
        row_layout.addWidget(thickness_marker(thickness_label), 0)
        return row_widget

    def _build_given_block(self) -> QFrame:
        frame, layout = section_frame("1. Given Parameters")
        body = QHBoxLayout()
        body.setSpacing(BLOCK_SPACING)
        body.addWidget(self._build_left_params(), 1)
        body.addWidget(self._build_layer_panel(), 1)
        layout.addLayout(body)
        return frame

    def _build_left_params(self) -> QFrame:
        panel = QFrame()
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        self.esal_spin = self._make_spin(
            value=5.0, decimals=4, maximum=999.9999, suffix=" million"
        )
        self.pt_spin = self._make_spin(value=2.0, decimals=2, maximum=5.0)
        self.p0_spin = self._make_spin(value=4.5, decimals=2, maximum=5.0)
        self.s0_spin = self._make_spin(value=0.29, decimals=2, maximum=2.0)
        self.r0_spin = self._make_spin(value=80.0, decimals=0, maximum=99.9)
        self.sc_spin = self._make_spin(
            value=4.5, decimals=2, minimum=0.1, maximum=20.0, suffix=" MPa"
        )
        self.j_spin = self._make_spin(value=3.2, decimals=2, minimum=0.1, maximum=10.0)
        self.cd_spin = self._make_spin(value=1.0, decimals=2, minimum=0.1, maximum=2.0)
        self.ls_spin = self._make_spin(value=1.0, decimals=0, minimum=0.0, maximum=3.0)
        self.das_spin = self._make_spin(
            value=20.0, decimals=2, minimum=1.0, maximum=100.0, suffix=" cm"
        )

        rows = (
            ("Total traffic, ESAL =", self.esal_spin),
            ("Terminal serviceability Pt =", self.pt_spin),
            ("Initial serviceability P0 =", self.p0_spin),
            ("Standard deviation S0 =", self.s0_spin),
            ("Reliability design R0 =", self.r0_spin),
            ("Modulus of rupture of concrete Sc =", self.sc_spin),
            ("Load transfer coefficient J =", self.j_spin),
            ("Drainage coefficient Cd =", self.cd_spin),
            ("Loss of subgrade support LS =", self.ls_spin),
            ("Assumed concrete thickness Das =", self.das_spin),
        )
        for index, (caption, spin) in enumerate(rows):
            add_labeled_row(grid, index, caption, spin, ROW_HEIGHT)
        grid.setColumnStretch(1, 1)

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(grid_host)
        outer.addStretch()
        return panel

    def _build_layer_panel(self) -> QFrame:
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.ec_spin = self._make_spin(
            value=34500.0, decimals=0, minimum=1000.0, maximum=100_000.0
        )
        self.e2_spin = self._make_spin(
            value=335.0, decimals=2, minimum=1.0, maximum=100_000.0
        )
        self.h2_spin = self._make_spin(
            value=20.0, decimals=2, minimum=0.0, maximum=200.0
        )
        self.e3_spin = self._make_spin(
            value=209.66, decimals=2, minimum=1.0, maximum=100_000.0
        )
        self.h3_spin = self._make_spin(
            value=20.0, decimals=2, minimum=0.0, maximum=200.0
        )
        self.cbr_sel_spin = self._make_spin(
            value=2.0, decimals=2, minimum=0.0, maximum=100.0
        )
        self.h4_spin = self._make_spin(
            value=0.0, decimals=0, minimum=0.0, maximum=100.0
        )

        layout.addWidget(
            self._layer_row(
                "Concrete Slab",
                "#9bb7d4",
                self._param_pair("Ec =", self.ec_spin, "MPa"),
                None,
                "D",
            )
        )
        layout.addWidget(
            self._layer_row(
                "Granular base",
                "#7fbf7f",
                self._param_pair("E2 =", self.e2_spin, "MPa"),
                self._param_pair("h2 =", self.h2_spin, "cm"),
                "h₂",
            )
        )
        layout.addWidget(
            self._layer_row(
                "Subbase",
                "#c4a06a",
                self._param_pair("E3 =", self.e3_spin, "MPa"),
                self._param_pair("h3 =", self.h3_spin, "cm"),
                "h₃",
            )
        )
        layout.addWidget(
            self._layer_row(
                "Selected subgrade",
                "#d9c4a0",
                self._param_pair("CBR =", self.cbr_sel_spin, "%"),
                self._param_pair("h4 =", self.h4_spin, "cm"),
                "h₄",
            )
        )
        layout.addStretch()
        return panel

    def _build_modulus_block(self) -> QFrame:
        frame, layout = section_frame("2. Effective Roadbed Soil Resilient Modulus")

        self.modulus_table = QTableWidget(5, len(MONTH_LABELS) + 1)
        self.modulus_table.setHorizontalHeaderLabels(["Month", *MONTH_LABELS])
        self.modulus_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.modulus_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.modulus_table.setAlternatingRowColors(True)
        configure_modulus_table(self.modulus_table)

        row_labels = ["CBR (%)", "CBR_eff (%)", "MR (psi)", "k_eq", "ur"]
        self._monthly_cbr_spins = []
        for row_index, label in enumerate(row_labels):
            self.modulus_table.setCellWidget(row_index, 0, modulus_row_label(label))
            for col in range(len(MONTH_LABELS)):
                if row_index == 0:
                    spin = make_double_spin()
                    spin.setRange(0.0, 100.0)
                    spin.setDecimals(2)
                    spin.setValue(5.0)
                    set_modulus_spin_height(spin)
                    self._style_input(spin)
                    spin.valueChanged.connect(self._on_changed)
                    self._monthly_cbr_spins.append(spin)
                    self.modulus_table.setCellWidget(row_index, col + 1, spin)
                else:
                    self.modulus_table.setItem(row_index, col + 1, modulus_table_item("—"))

        self.modulus_table.setColumnWidth(0, UiScale.px(MODULUS_LABEL_COLUMN_WIDTH + 20))
        header = self.modulus_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        for col in range(1, self.modulus_table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        fit_modulus_table_height(self.modulus_table)
        layout.addWidget(self.modulus_table)

        summary = QLabel()
        summary.setWordWrap(True)
        summary.setTextFormat(Qt.TextFormat.RichText)
        self.modulus_summary = summary
        layout.addWidget(summary)
        return frame

    def _build_thickness_block(self) -> QFrame:
        frame, layout = section_frame("3. Determination of Concrete Thickness D")
        layout.setSpacing(16)

        eq = QLabel(_EQUATION_HTML)
        eq.setWordWrap(True)
        eq.setTextFormat(Qt.TextFormat.RichText)
        eq.setStyleSheet(
            "background-color: #2a2a2c; border: 1px solid #3e3e40; "
            "border-radius: 4px; padding: 10px 12px;"
        )
        layout.addWidget(eq)

        sub = QLabel("3.3 Determination of Required Thickness")
        sub.setStyleSheet("color: #dddddd; font-weight: 700; font-size: 14px;")
        layout.addWidget(sub)

        dcal_row = QHBoxLayout()
        dcal_row.setSpacing(12)
        dcal_caption = QLabel("Calculate the required thickness Dcal based on Eq. (1) =")
        dcal_caption.setStyleSheet("color: #cccccc; font-weight: 600;")
        self.dcal_inch_box = value_box()
        self.dcal_cm_box = value_box()
        dcal_row.addWidget(dcal_caption)
        dcal_row.addWidget(self.dcal_inch_box)
        dcal_row.addWidget(QLabel("inches   or"))
        dcal_row.addWidget(self.dcal_cm_box)
        dcal_row.addWidget(QLabel("cm"))
        dcal_row.addStretch()
        layout.addLayout(dcal_row)

        verify_title = QLabel("Verification")
        verify_title.setStyleSheet("color: #dddddd; font-weight: 700; font-size: 14px;")
        layout.addWidget(verify_title)

        verify_row = QHBoxLayout()
        verify_row.setSpacing(12)
        diff_caption = QLabel("% Difference between Das and Dcal =")
        diff_caption.setStyleSheet("color: #cccccc; font-weight: 600;")
        self.diff_box = value_box()
        self.verify_compare = QLabel("—")
        self.verify_compare.setStyleSheet("color: #cccccc; font-weight: 600;")
        self.verify_status = QLabel("—")
        self.verify_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verify_status.setMinimumWidth(72)
        self.verify_status.setMinimumHeight(32)
        verify_row.addWidget(diff_caption)
        verify_row.addWidget(self.diff_box)
        verify_row.addWidget(self.verify_compare)
        verify_row.addWidget(self.verify_status)
        verify_row.addStretch()
        layout.addLayout(verify_row)

        final_title = QLabel("Final Designed Thickness")
        final_title.setStyleSheet("color: #dddddd; font-weight: 700; font-size: 14px;")
        layout.addWidget(final_title)

        final_row = QHBoxLayout()
        final_row.setSpacing(12)
        final_caption = QLabel("The final designed thickness of D is =")
        final_caption.setStyleSheet("color: #cccccc; font-weight: 600;")
        self.final_calc_box = value_box()
        round_caption = QLabel("round-up to :")
        round_caption.setStyleSheet("color: #cccccc; font-weight: 600;")
        self.final_round_box = value_box()
        final_row.addWidget(final_caption)
        final_row.addWidget(self.final_calc_box)
        final_row.addWidget(QLabel("cm"))
        final_row.addSpacing(20)
        final_row.addWidget(round_caption)
        final_row.addWidget(self.final_round_box)
        final_row.addWidget(QLabel("cm"))
        final_row.addStretch()
        layout.addLayout(final_row)
        return frame

    def _on_changed(self, *_args) -> None:
        if not self._ready:
            return
        self._refresh()
        self.inputs_changed.emit()

    def _monthly_cbr_values(self) -> list[float]:
        return [float(spin.value()) for spin in self._monthly_cbr_spins]

    def _current_result(self):
        return compute_aashto_rigid(
            esal_million=float(self.esal_spin.value()),
            pt=float(self.pt_spin.value()),
            p0=float(self.p0_spin.value()),
            s0=float(self.s0_spin.value()),
            reliability_percent=float(self.r0_spin.value()),
            sc_mpa=float(self.sc_spin.value()),
            j=float(self.j_spin.value()),
            cd=float(self.cd_spin.value()),
            ls=int(self.ls_spin.value()),
            das_cm=float(self.das_spin.value()),
            ec_mpa=float(self.ec_spin.value()),
            e2_mpa=float(self.e2_spin.value()),
            h2_cm=float(self.h2_spin.value()),
            e3_mpa=float(self.e3_spin.value()),
            h3_cm=float(self.h3_spin.value()),
            cbr_selected=float(self.cbr_sel_spin.value()),
            h4_cm=float(self.h4_spin.value()),
            monthly_cbr_percent=self._monthly_cbr_values(),
        )

    def _refresh(self) -> None:
        if not self._ready:
            return
        r = self._current_result()
        accent = theme_tokens().accent

        for col, month in enumerate(r.months):
            values = [
                None,
                f"{month.cbr_effective_percent:.2f}",
                f"{month.mr_psi:.0f}",
                f"{month.k_eq_pci:.2f}",
                f"{month.relative_damage_ur:.3f}" if month.relative_damage_ur is not None else "—",
            ]
            for row_index, text in enumerate(values, start=1):
                if text is None:
                    continue
                item = self.modulus_table.item(row_index, col + 1)
                if item is None:
                    item = modulus_table_item()
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    self.modulus_table.setItem(row_index, col + 1, item)
                item.setText(text)
        fit_modulus_table_height(self.modulus_table)

        avg = f"{r.average_ur:.3f}" if r.average_ur is not None else "—"
        if r.effective_k_pci is not None:
            k_eff = (
                f"{r.effective_k_pci:,.2f} pci"
                f"&nbsp;&nbsp;({r.effective_k_mpa_per_m:,.2f} MPa/m)"
            )
        else:
            k_eff = "—"
        k_corr = f"{r.corrected_k_pci:,.2f} pci" if r.corrected_k_pci is not None else "—"
        value_style = f"color: {accent}; font-weight: 700;"
        self.modulus_summary.setText(
            "<ul style='margin: 4px 0 0 0; padding-left: 18px; color: #cccccc;'>"
            f"<li style='margin: 4px 0;'>Average relative damage ur = "
            f"<span style='{value_style}'>{avg}</span></li>"
            f"<li style='margin: 4px 0;'>Effective modulus of subgrade reaction k = "
            f"<span style='{value_style}'>{k_eff}</span></li>"
            f"<li style='margin: 4px 0;'>k value after corrected for loss of support = "
            f"<span style='{value_style}'>{k_corr}</span></li>"
            "</ul>"
        )

        if r.dcal_inch is not None and r.dcal_cm is not None:
            self.dcal_inch_box.setText(f"{r.dcal_inch:,.2f}")
            self.dcal_cm_box.setText(f"{r.dcal_cm:,.2f}")
            self.final_calc_box.setText(f"{r.dcal_cm:,.2f}")
        else:
            self.dcal_inch_box.setText("—")
            self.dcal_cm_box.setText("—")
            self.final_calc_box.setText("—")

        if r.final_thickness_cm is not None:
            self.final_round_box.setText(f"{r.final_thickness_cm:.2f}")
        else:
            self.final_round_box.setText("—")

        if r.difference_ratio is not None:
            pct = r.difference_ratio * 100.0
            self.diff_box.setText(f"{pct:,.2f}%")
            if r.verification_ok:
                self.verify_compare.setText(f"{pct:,.1f}% < 5%")
                self.verify_status.setText("OK")
                self.verify_status.setStyleSheet(
                    "background-color: #1f7a3f; color: #ffffff; font-weight: 700; "
                    "border-radius: 4px; padding: 4px 14px;"
                )
            else:
                self.verify_compare.setText(
                    f"{pct:,.1f}% ≥ 5% — Please change the assumed concrete thickness."
                )
                self.verify_status.setText("NO")
                self.verify_status.setStyleSheet(
                    "background-color: #8b3a3a; color: #ffffff; font-weight: 700; "
                    "border-radius: 4px; padding: 4px 14px;"
                )
        else:
            self.diff_box.setText("—")
            self.verify_compare.setText("—")
            self.verify_status.setText("—")
            self.verify_status.setStyleSheet(
                "background-color: #3e3e40; color: #cccccc; font-weight: 700; "
                "border-radius: 4px; padding: 4px 14px;"
            )
