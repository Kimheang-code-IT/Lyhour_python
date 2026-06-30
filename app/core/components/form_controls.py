"""Reusable form control factories with Fluent fallbacks."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox

try:
    from qfluentwidgets import (
        ComboBox as FluentComboBox,
        DoubleSpinBox as FluentDoubleSpinBox,
        EditableComboBox as FluentEditableComboBox,
        LineEdit as FluentLineEdit,
    )
    _HAS_FLUENT = True
except Exception:
    FluentComboBox = None  # type: ignore[assignment]
    FluentDoubleSpinBox = None  # type: ignore[assignment]
    FluentEditableComboBox = None  # type: ignore[assignment]
    FluentLineEdit = None  # type: ignore[assignment]
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
