"""Road Classification subpage."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.utils.result_html import result_title_style
from app.data.road_classification import build_road_classification_text
from app.widgets.traffic_results import (
    configure_result_description_note_layout,
    result_card,
    result_description_label,
    result_description_note,
    refresh_theme_widgets,
)


class RoadClassificationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._design_year: str | None = None
        self._total_aadt: int | None = None
        self._total_pcu: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = result_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._title = result_description_label()
        card_layout.addWidget(self._title, 0, Qt.AlignmentFlag.AlignTop)

        note = result_description_note(dark_background=False)
        note_layout = QVBoxLayout(note)
        note_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._description = result_description_label()
        configure_result_description_note_layout(note_layout, self._description)

        card_layout.addWidget(note, 1, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(card, 1, Qt.AlignmentFlag.AlignTop)
        self.refresh_ui_scale()
        self.set_road_classification(None, None, None)

    def set_road_classification(
        self,
        design_year: str | None,
        total_aadt: int | None,
        total_pcu: int | None,
    ) -> None:
        self._design_year = design_year
        self._total_aadt = total_aadt
        self._total_pcu = total_pcu
        self._apply_description()

    def refresh_theme(self) -> None:
        refresh_theme_widgets(self)
        self.refresh_ui_scale()

    def _apply_description(self) -> None:
        self._description.setText(
            build_road_classification_text(
                self._design_year or "",
                self._total_aadt,
                self._total_pcu,
            )
        )

    def refresh_ui_scale(self) -> None:
        self._title.setText(
            f'<span style="{result_title_style()}">Road Classification</span>'
        )
        self._apply_description()
