# app.widgets – use qfluentwidgets when available (buttons, labels, combos, dialogs)

from app.widgets.button import primary_button, secondary_button
from app.widgets.labeled_input import add_labeled_row, LabeledInput
from app.widgets.labeled_select import add_labeled_select_row, LabeledSelect
from app.widgets.dialog import info, warning, open_file, save_file

# Optional Fluent inputs for pages that want Fluent ComboBox/SpinBox
try:
    from qfluentwidgets import ComboBox, SpinBox, DoubleSpinBox, LineEdit
    FluentComboBox = ComboBox
    FluentSpinBox = SpinBox
    FluentDoubleSpinBox = DoubleSpinBox
    FluentLineEdit = LineEdit
except ImportError:
    from PyQt6.QtWidgets import QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit
    FluentComboBox = QComboBox
    FluentSpinBox = QSpinBox
    FluentDoubleSpinBox = QDoubleSpinBox
    FluentLineEdit = QLineEdit

__all__ = [
    "primary_button",
    "secondary_button",
    "add_labeled_row",
    "LabeledInput",
    "add_labeled_select_row",
    "LabeledSelect",
    "info",
    "warning",
    "open_file",
    "save_file",
    "FluentComboBox",
    "FluentSpinBox",
    "FluentDoubleSpinBox",
    "FluentLineEdit",
]
