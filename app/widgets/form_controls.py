"""Reusable form control factories with Fluent fallbacks."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QRadioButton, QSpinBox


class _NoWheelMixin:
    """Ignore mouse wheel so values change only by direct typing or selection."""

    def wheelEvent(self, event) -> None:  # noqa: N802
        event.ignore()

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


if _HAS_FLUENT and FluentDoubleSpinBox is not None:
    class _NoWheelDoubleSpinBox(_NoWheelMixin, FluentDoubleSpinBox):  # type: ignore[misc,valid-type]
        pass
else:
    class _NoWheelDoubleSpinBox(_NoWheelMixin, QDoubleSpinBox):
        pass


if _HAS_FLUENT and FluentComboBox is not None:
    class _NoWheelComboBox(_NoWheelMixin, FluentComboBox):  # type: ignore[misc,valid-type]
        pass
else:
    class _NoWheelComboBox(_NoWheelMixin, QComboBox):
        pass


if _HAS_FLUENT and FluentEditableComboBox is not None:
    class _NoWheelEditableComboBox(_NoWheelMixin, FluentEditableComboBox):  # type: ignore[misc,valid-type]
        pass
else:
    _NoWheelEditableComboBox = _NoWheelComboBox


if _HAS_FLUENT and FluentLineEdit is not None:
    class _NoWheelLineEdit(_NoWheelMixin, FluentLineEdit):  # type: ignore[misc,valid-type]
        pass
else:
    class _NoWheelLineEdit(_NoWheelMixin, QLineEdit):
        pass


def disable_wheel_on_input(widget):
    """Prevent mouse wheel from changing a control; wheel scrolls the parent instead."""
    widget.wheelEvent = _NoWheelMixin.wheelEvent.__get__(widget, type(widget))  # type: ignore[method-assign]
    return widget


def make_double_spin() -> QDoubleSpinBox:
    """Numeric input without increment/decrement icons."""
    widget = _NoWheelDoubleSpinBox()
    if _HAS_FLUENT and FluentDoubleSpinBox is not None and isinstance(widget, FluentDoubleSpinBox):
        widget.setSymbolVisible(False)
    else:
        widget.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    return widget


def make_spin_no_buttons(widget):
    """Hide increment/decrement icons on native spin controls."""
    if isinstance(widget, QSpinBox):
        widget.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
    else:
        widget.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    return disable_wheel_on_input(widget)


def make_combo(items, *, editable: bool = False):
    """Create a combo with Fluent style when available."""
    if _HAS_FLUENT:
        if editable and FluentEditableComboBox is not None:
            combo = _NoWheelEditableComboBox()
        else:
            combo = _NoWheelComboBox()
    else:
        combo = _NoWheelComboBox()

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
    return _NoWheelLineEdit()


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
