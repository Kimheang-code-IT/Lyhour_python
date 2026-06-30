"""Quick panel: compact traffic analysis results for Input and Detail Result pages."""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel


class QuickPanel(QFrame):
    """Right-side quick results panel shown on Traffic Analysis pages."""

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
        self.setMinimumWidth(400)
        self.setMaximumWidth(430)
        self.setStyleSheet("""
            #quickPanel {
                background-color: #2d2d30;
                border: none;
                padding: 0;
            }
            #quickPanel QLabel {
                background-color: #2d2d30;
                color: #cccccc;
                font-size: 16px;
                border: none;
                padding: 10px 16px;
            }
            QLabel#quickPanelTitle {
                background-color: #333333;
                color: #ffffff;
                font-size: 15px;
                font-weight: bold;
                padding: 14px 16px;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QLabel#quickPanelRow {
                color: #cccccc;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Quick Results")
        title.setObjectName("quickPanelTitle")
        layout.addWidget(title)

        self._result_labels: dict[str, QLabel] = {}
        self._result_names: dict[str, str] = {}
        for key, label_text in self._TRAFFIC_FIELDS:
            row = QLabel(f"{label_text} —")
            row.setObjectName("quickPanelRow")
            self._result_labels[key] = row
            self._result_names[key] = label_text
            layout.addWidget(row)

        layout.addStretch()

    def set_results(self, results: dict | None) -> None:
        for key, label in self._result_labels.items():
            prefix = self._result_names[key]
            value = (results or {}).get(key)
            if value is not None and str(value).strip():
                label.setText(f"{prefix} {value}")
            else:
                label.setText(f"{prefix} —")
