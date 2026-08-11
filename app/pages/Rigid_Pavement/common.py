"""Shared UI helpers for Rigid Pavement pages."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from app.core.theme import theme_tokens
from app.core.ui_style import section_title_style

TAB_MPWT = 0
TAB_AASHTO = 1

ROW_HEIGHT = 36
BLOCK_SPACING = 24
SECTION_TITLE_STYLE = section_title_style(18)
VALUE_BOX_WIDTH = 140


def set_input_height(widget) -> None:
    widget.setMinimumHeight(ROW_HEIGHT)
    widget.setMaximumHeight(ROW_HEIGHT)


def section_frame(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("rigidPavementSectionFrame")
    frame.setStyleSheet(
        "#rigidPavementSectionFrame { background-color: transparent; "
        "border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 16)
    layout.setSpacing(12)
    title_label = QLabel(title)
    title_label.setStyleSheet(SECTION_TITLE_STYLE)
    layout.addWidget(title_label)
    frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return frame, layout


def value_box(text: str = "—") -> QLabel:
    """Bordered read-only value cell matching the Analysis & Result layout."""
    tokens = theme_tokens()
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setMinimumHeight(ROW_HEIGHT)
    label.setMinimumWidth(VALUE_BOX_WIDTH)
    label.setStyleSheet(
        f"color: {tokens.accent}; font-weight: 700; "
        "border: 1px solid #888888; border-radius: 2px; "
        "background-color: transparent; padding: 4px 10px;"
    )
    return label


def labeled_value_row(caption: str, value_label: QLabel) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(12)
    caption_label = QLabel(caption)
    caption_label.setStyleSheet("color: #dddddd; font-weight: 700;")
    caption_label.setMinimumWidth(280)
    row.addWidget(caption_label)
    row.addWidget(value_label)
    row.addStretch()
    return row


def result_card(title: str, value: str) -> QFrame:
    tokens = theme_tokens()
    card = QFrame()
    card.setObjectName("rigidResultCard")
    card.setStyleSheet(
        "#rigidResultCard { background-color: transparent; "
        "border: 1px solid #3e3e40; border-radius: 6px; }"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(6)
    caption = QLabel(title)
    caption.setStyleSheet("color: #aaaaaa; font-size: 12px;")
    caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
    value_label = QLabel(value)
    value_label.setObjectName("rigidResultValue")
    value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    value_label.setStyleSheet(
        f"color: {tokens.accent}; font-size: 18px; font-weight: 700;"
    )
    layout.addWidget(caption)
    layout.addWidget(value_label)
    card.setMinimumWidth(160)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    card._value_label = value_label  # type: ignore[attr-defined]
    return card


def set_result_card_value(card: QFrame, value: str) -> None:
    label = getattr(card, "_value_label", None)
    if label is not None:
        label.setText(value)
