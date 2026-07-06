"""Reusable form control factories with Fluent fallbacks."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QRadioButton, QSpinBox

try:
    from qfluentwidgets import (
        ComboBox as FluentComboBox,
        DoubleSpinBox as FluentDoubleSpinBox,
        EditableComboBox as FluentEditableComboBox,
        LineEdit as FluentLineEdit,
        RadioButton as FluentRadioButton,
        SwitchButton as FluentSwitchButton,
    )
    _HAS_FLUENT = True
except Exception:
    FluentComboBox = None  # type: ignore[assignment]
    FluentDoubleSpinBox = None  # type: ignore[assignment]
    FluentEditableComboBox = None  # type: ignore[assignment]
    FluentLineEdit = None  # type: ignore[assignment]
    FluentRadioButton = None  # type: ignore[assignment]
    FluentSwitchButton = None  # type: ignore[assignment]
    _HAS_FLUENT = False


def make_double_spin() -> QDoubleSpinBox:
    """Numeric input without increment/decrement icons."""
    if _HAS_FLUENT and FluentDoubleSpinBox is not None:
        widget = FluentDoubleSpinBox()
        widget.setSymbolVisible(False)
    else:
        widget = QDoubleSpinBox()
        widget.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    return widget


def make_spin_no_buttons(widget):
    """Hide increment/decrement icons on native spin controls."""
    if isinstance(widget, QSpinBox):
        widget.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
    else:
        widget.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    return widget


def make_combo(items, *, editable: bool = False):
    """Create a combo with Fluent style when available."""
    if _HAS_FLUENT:
        if editable and FluentEditableComboBox is not None:
            combo = FluentEditableComboBox()
        else:
            combo = FluentComboBox() if FluentComboBox is not None else QComboBox()
    else:
        combo = QComboBox()

    try:
        combo.setEditable(bool(editable) if isinstance(combo, QComboBox) else False)
    except Exception:
        pass

    combo.addItems(list(items))
    return combo


def make_data_combo(options: list[tuple[str, object]]):
    """Fluent combo with ``(label, value)`` pairs — same style as Traffic Input selects."""
    combo = make_combo([label for label, _ in options])
    for index, (_, value) in enumerate(options):
        combo.setItemData(index, value)
    return combo


def combo_current_data(combo) -> object:
    index = combo.currentIndex()
    if index < 0:
        return None
    data = combo.itemData(index)
    return data if data is not None else combo.currentText()


def set_combo_data(combo, value) -> None:
    for index in range(combo.count()):
        if combo.itemData(index) == value:
            combo.setCurrentIndex(index)
            return


def make_switch(*, checked: bool = False):
    """On/off toggle using Fluent ``SwitchButton`` when available."""
    if _HAS_FLUENT and FluentSwitchButton is not None:
        widget = FluentSwitchButton()
    else:
        from PyQt6.QtWidgets import QCheckBox

        widget = QCheckBox()
    widget.setChecked(checked)
    return widget


def make_radio(text: str = "", *, checked: bool = False) -> QRadioButton:
    """Radio control using Fluent ``RadioButton`` when available."""
    if _HAS_FLUENT and FluentRadioButton is not None:
        widget = FluentRadioButton(text)
    else:
        widget = QRadioButton(text)
    widget.setChecked(checked)
    return widget


def _make_line_edit() -> QLineEdit:
    if _HAS_FLUENT and FluentLineEdit is not None:
        return FluentLineEdit()
    return QLineEdit()


def make_integer_line_edit(*, minimum: int = 0, maximum: int = 9_999_999) -> QLineEdit:
    """Text input that accepts whole numbers only."""
    widget = _make_line_edit()
    widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    widget.setValidator(QIntValidator(minimum, maximum, widget))
    return widget


def make_decimal_line_edit(
    *,
    minimum: float = 0.0,
    maximum: float = 9_999_999.99,
    decimals: int = 2,
) -> QLineEdit:
    """Text input that accepts decimal numbers only."""
    widget = _make_line_edit()
    widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    validator = QDoubleValidator(minimum, maximum, decimals, widget)
    validator.setNotation(QDoubleValidator.Notation.StandardNotation)
    widget.setValidator(validator)
    return widget
