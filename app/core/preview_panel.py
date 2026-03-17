"""Right panel: preview image and Quick Results card."""
from pathlib import Path

from PyQt6.QtWidgets import QVBoxLayout, QLabel, QFrame, QSplitter, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QColor

# From app/core, assets are at app/assets
_ASSETS = Path(__file__).resolve().parent.parent / "assets"


class PreviewPanel(QFrame):
    """Right column: preview area and Quick Results card."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("previewPanel")
        self.setStyleSheet("""
            #previewPanel { background-color: #252526; border: none; outline: none; outline-color: transparent; }
            #quickResultsCard { background-color: #2d2d30; border: none; padding: 0; outline: none; outline-color: transparent; }
            #quickResultsCard #cardTitle { font-weight: bold; font-size: 15px; color: #ffffff; padding: 14px 16px; background-color: #333333; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            #quickResultsCard QLabel { padding: 10px 16px; color: #cccccc; font-size: 16px; border: none; }
        """)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(8)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #3e3e40; height: 8px; }")

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(120)
        self.preview_label.setStyleSheet("background-color: #1e1e1e; ")
        self.preview_label.setScaledContents(False)
        self._set_default_preview_image()
        self.splitter.addWidget(self.preview_label)

        card = QFrame()
        card.setObjectName("quickResultsCard")
        card.setMinimumHeight(120)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        title = QLabel("Quick Results")
        title.setObjectName("cardTitle")
        card_layout.addWidget(title)
        card_layout.addStretch()
        self.splitter.addWidget(card)

        layout.addWidget(self.splitter, 1)
        self._splitter_initialized = False

        # Quick results schema state
        self._card_layout = card_layout
        self.result_labels: dict[str, QLabel] = {}
        self._result_names: dict[str, str] = {}
        # Keys whose numeric values are displayed with " m" suffix (radius in meters)
        self._result_suffix_m: set[str] = set()
        self.set_horizontal_curvature_schema()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._splitter_initialized and self.splitter.height() > 0:
            self._splitter_initialized = True
            h = self.splitter.height()
            self.splitter.setSizes([h // 2, h - h // 2])
        if hasattr(self, "_default_pixmap") and self._default_pixmap and not self._default_pixmap.isNull():
            self._update_preview_pixmap(self._default_pixmap)

    def _default_image_path(self) -> Path:
        return _ASSETS / "road.jpg"

    def _set_default_preview_image(self):
        path = self._default_image_path()
        if path.is_file():
            pm = QPixmap(str(path))
            if not pm.isNull():
                self._default_pixmap = pm
                self._update_preview_pixmap(pm)
                return
        self._default_pixmap = None
        self._set_placeholder_image()

    def _set_placeholder_image(self):
        self._default_pixmap = None
        pm = QPixmap(320, 200)
        pm.fill(QColor(30, 30, 30))
        painter = QPainter(pm)
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "Preview")
        painter.end()
        self.preview_label.setPixmap(pm)

    def _update_preview_pixmap(self, pm: QPixmap):
        w = self.preview_label.width() or 320
        h = self.preview_label.height() or 200
        if w < 10:
            w = 320
        if h < 10:
            h = 200
        self.preview_label.setPixmap(
            pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

    def set_preview_image(self, pixmap: QPixmap | None):
        if pixmap is None or pixmap.isNull():
            self._set_default_preview_image()
        else:
            self._update_preview_pixmap(pixmap)

    def set_preview_from_asset(self, filename: str):
        """Set preview image from an asset file in app/assets."""
        try:
            path = _ASSETS / filename
            pm = QPixmap(str(path)) if path.is_file() else None
        except Exception:
            pm = None
        self.set_preview_image(pm)

    def _set_schema(self, fields: list[tuple[str, str]], suffix_m_keys: set[str] | None = None):
        """Configure which quick result rows are shown."""
        # Remove existing labels
        for lbl in self.result_labels.values():
            self._card_layout.removeWidget(lbl)
            lbl.deleteLater()
        self.result_labels.clear()
        self._result_names.clear()
        self._result_suffix_m = suffix_m_keys or set()

        # Insert new labels before the stretch item (last item in layout)
        insert_index = max(self._card_layout.count() - 1, 1)
        for key, name in fields:
            row = QLabel(f"{name} —")
            row.setObjectName(f"result_{key}")
            self.result_labels[key] = row
            self._result_names[key] = name
            self._card_layout.insertWidget(insert_index, row)
            insert_index += 1

    def set_horizontal_curvature_schema(self):
        """Default schema: horizontal curvature quick results."""
        fields = [
            ("Minimum Radius", "Minimum radius R_min    ="),
            ("Minimum Radius from table", "Minimum radius from table ="),
            ("Minimum radius on grade R_min_ongrade", "Minimum radius on grade R_min_ongrade ="),
            ("Verification", "Verification ="),
        ]
        suffix_m = {"Minimum Radius", "Minimum Radius from table", "Minimum radius on grade R_min_ongrade"}
        self._set_schema(fields, suffix_m_keys=suffix_m)

    def set_traffic_input_schema(self):
        """Schema used by Traffic Analysis Input page."""
        fields = [
            ("AADT", "AADT ="),
            ("PCU", "PCU ="),
            ("Road classification", "Road classification ="),
            ("Number of lane", "Number of lane ="),
        ]
        self._set_schema(fields, suffix_m_keys=set())

    def set_superelevation_schema(self):
        """Schema used by Superelevation Design page."""
        fields = [
            ("Transition Length Le", "Transition Length Le ="),
            ("Tro", "Tro ="),
            ("Sro", "Sro ="),
            ("Curve length", "Curve length ="),
        ]
        suffix_m = {"Transition Length Le", "Curve length"}
        self._set_schema(fields, suffix_m_keys=suffix_m)

    def set_results(self, results: dict | None):
        for key, label in self.result_labels.items():
            name = self._result_names[key]
            value = (results or {}).get(key)
            if value is not None and value != "":
                if isinstance(value, float):
                    suffix = " m" if key in self._result_suffix_m else ""
                    label.setText(f"{name} {value:,.2f}{suffix}")
                else:
                    label.setText(f"{name} {value}")
            else:
                label.setText(f"{name} —")
