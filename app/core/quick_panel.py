"""Quick panel: compact traffic analysis results for Input and Detail Result pages."""
from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

from app.core.theme import shell_stylesheet, theme_tokens

_QUICK_VALUE_STYLE = "color:#4da3ff; font-weight:700;"
_QUICK_EMPTY_STYLE = "color:#888888;"


class QuickPanel(QFrame):
    """Right-side quick results panel shown on Traffic Analysis pages."""

    _PANEL_MIN_WIDTH = 260
    _PANEL_MAX_WIDTH = 300

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

        title = QLabel("Quick Results")
        title.setObjectName("quickPanelTitle")
        layout.addWidget(title)

        self._result_labels: dict[str, QLabel] = {}
        self._result_names: dict[str, str] = {}
        self._empty_style = _QUICK_EMPTY_STYLE
        for key, label_text in self._TRAFFIC_FIELDS:
            row = QLabel()
            row.setObjectName("quickPanelRow")
            row.setTextFormat(Qt.TextFormat.RichText)
            row.setWordWrap(True)
            self._set_row_text(row, label_text, None)
            self._result_labels[key] = row
            self._result_names[key] = label_text
            layout.addWidget(row)

        layout.addStretch()
        self.apply_theme()

    def apply_theme(self) -> None:
        tokens = theme_tokens()
        self.setStyleSheet(shell_stylesheet(tokens))
        self._empty_style = f"color:{tokens.text_muted};"

    def _set_row_text(self, label: QLabel, prefix: str, value: str | None) -> None:
        safe_prefix = escape(prefix)
        if value is not None and str(value).strip():
            safe_value = escape(str(value).strip())
            label.setText(f'{safe_prefix} <span style="{_QUICK_VALUE_STYLE}">{safe_value}</span>')
        else:
            label.setText(f'{safe_prefix} <span style="{self._empty_style}">—</span>')

    def set_results(self, results: dict | None) -> None:
        for key, label in self._result_labels.items():
            prefix = self._result_names[key]
            value = (results or {}).get(key)
            self._set_row_text(label, prefix, str(value) if value is not None else None)
