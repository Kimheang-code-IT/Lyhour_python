"""Quick panel: compact results for Traffic Analysis and Road Geometry pages."""
from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

from app.core.theme import shell_stylesheet, theme_tokens

_QUICK_VALUE_STYLE = "color:#4da3ff; font-weight:700;"
_QUICK_EMPTY_STYLE = "color:#888888;"


class QuickPanel(QFrame):
    """Right-side quick results panel (no preview image)."""

    _PANEL_MIN_WIDTH = 260
    _PANEL_MAX_WIDTH = 300
    _WIDE_PANEL_MIN_WIDTH = 380
    _WIDE_PANEL_MAX_WIDTH = 430

    _TRAFFIC_FIELDS: tuple[tuple[str, str], ...] = (
        ("AADT", "AADT ="),
        ("PCU", "PCU ="),
        ("Road classification", "Road classification ="),
        ("Number of lane", "Number of lane ="),
        ("Capacity ratio", "Capacity ratio ="),
        ("ESAL", "ESAL ="),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quickPanel")
        self.setMinimumWidth(self._PANEL_MIN_WIDTH)
        self.setMaximumWidth(self._PANEL_MAX_WIDTH)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._card_layout = layout
        self._title = QLabel("Quick Results")
        self._title.setObjectName("quickPanelTitle")
        layout.addWidget(self._title)

        self._result_labels: dict[str, QLabel] = {}
        self._result_names: dict[str, str] = {}
        self._result_suffix_m: set[str] = set()
        self._empty_style = _QUICK_EMPTY_STYLE

        layout.addStretch()
        self.set_traffic_schema()
        self.apply_theme()

    def apply_theme(self) -> None:
        tokens = theme_tokens()
        self.setStyleSheet(shell_stylesheet(tokens))
        self._empty_style = f"color:{tokens.text_muted};"

    def set_compact_width(self) -> None:
        self.setMinimumWidth(self._PANEL_MIN_WIDTH)
        self.setMaximumWidth(self._PANEL_MAX_WIDTH)

    def set_wide_width(self) -> None:
        self.setMinimumWidth(self._WIDE_PANEL_MIN_WIDTH)
        self.setMaximumWidth(self._WIDE_PANEL_MAX_WIDTH)

    def _set_row_text(self, label: QLabel, prefix: str, value: str | None) -> None:
        safe_prefix = escape(prefix)
        if value is not None and str(value).strip():
            safe_value = escape(str(value).strip())
            label.setText(f'{safe_prefix} <span style="{_QUICK_VALUE_STYLE}">{safe_value}</span>')
        else:
            label.setText(f'{safe_prefix} <span style="{self._empty_style}">—</span>')

    def _set_schema(self, fields: list[tuple[str, str]], *, suffix_m_keys: set[str] | None = None) -> None:
        for label in self._result_labels.values():
            self._card_layout.removeWidget(label)
            label.deleteLater()
        self._result_labels.clear()
        self._result_names.clear()
        self._result_suffix_m = suffix_m_keys or set()

        insert_index = max(self._card_layout.count() - 1, 1)
        for key, name in fields:
            row = QLabel()
            row.setObjectName("quickPanelRow")
            row.setTextFormat(Qt.TextFormat.RichText)
            row.setWordWrap(True)
            self._set_row_text(row, name, None)
            self._result_labels[key] = row
            self._result_names[key] = name
            self._card_layout.insertWidget(insert_index, row)
            insert_index += 1

    def set_traffic_schema(self) -> None:
        """Schema for Traffic Analysis Input / Detail Result pages."""
        self.set_compact_width()
        self._set_schema(list(self._TRAFFIC_FIELDS))

    def set_horizontal_curvature_schema(self) -> None:
        """Schema for Horizontal Curvature page."""
        self.set_wide_width()
        fields = [
            ("Minimum Radius", "Minimum radius R_min    ="),
            ("Minimum Radius from table", "Minimum radius from table ="),
            ("Minimum radius on grade R_min_ongrade", "Minimum radius on grade R_min_ongrade ="),
            ("Verification", "Verification ="),
        ]
        suffix_m = {
            "Minimum Radius",
            "Minimum Radius from table",
            "Minimum radius on grade R_min_ongrade",
        }
        self._set_schema(fields, suffix_m_keys=suffix_m)

    def set_superelevation_schema(self) -> None:
        """Schema for Superelevation Design page."""
        self.set_wide_width()
        fields = [
            ("Transition Length Le", "Transition Length Le ="),
            ("Tro", "Tro ="),
            ("Sro", "Sro ="),
            ("Curve length", "Curve length ="),
        ]
        suffix_m = {"Transition Length Le", "Tro", "Sro", "Curve length"}
        self._set_schema(fields, suffix_m_keys=suffix_m)

    def set_subgrade_schema(self) -> None:
        """Schema for Subgrade Design (DCP) page."""
        self.set_wide_width()
        fields = [
            ("Number of layers", "Number of layers ="),
            ("Maximum depth", "Maximum depth ="),
            ("Total blow number", "Total blow number ="),
            ("CBR at max depth", "CBR at max depth ="),
            ("Minimum CBR", "Minimum CBR ="),
            ("Average CBR", "Average CBR ="),
        ]
        self._set_schema(fields)

    def set_subgrade_cbr_equivalent_schema(self) -> None:
        """Schema for Subgrade Design CBR Equivalent tab."""
        self.set_wide_width()
        fields = [
            ("CBR Equivalent", "CBR Equivalent ="),
            ("Design depth", "Design depth ="),
            ("Minimum CBR in zone", "Minimum CBR in zone ="),
            ("Layers used", "Layers used ="),
        ]
        self._set_schema(fields)

    def set_flexible_pavement_schema(self) -> None:
        """Schema for Flexible Pavement AASHTO tab."""
        self.set_wide_width()
        fields = [
            ("ESAL", "Total traffic, ESAL (80kN) ="),
            ("Initial serviceability P0", "Initial serviceability P0 ="),
            ("Terminal serviceability Pt", "Terminal serviceability Pt ="),
            ("Reliability R0", "Reliability design R0 ="),
            ("Effective MR", "Effective roadbed MR ="),
            ("Average uf", "Average relative damage uf ="),
        ]
        self._set_schema(fields)

    def set_results(self, results: dict | None) -> None:
        for key, label in self._result_labels.items():
            prefix = self._result_names[key]
            value = (results or {}).get(key)
            if value is not None and value != "":
                if isinstance(value, float):
                    suffix = " m" if key in self._result_suffix_m else ""
                    display = f"{value:,.2f}{suffix}"
                else:
                    display = str(value)
                self._set_row_text(label, prefix, display)
            else:
                self._set_row_text(label, prefix, None)
