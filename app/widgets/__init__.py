# app.widgets – reusable UI components for app.pages

from app.widgets.button import primary_button, secondary_button
from app.widgets.form_controls import (
    make_combo,
    make_decimal_line_edit,
    make_double_spin,
    make_integer_line_edit,
    make_spin_no_buttons,
)
from app.widgets.labeled_input import LabeledInput, add_labeled_row
from app.widgets.labeled_select import LabeledSelect, add_labeled_select_row, make_design_year_combo
from app.widgets.dialog import info, open_file, save_file, warning
from app.widgets.page_shell import PageShell
from app.widgets.traffic_charts import TrafficTotalLineChart, TrafficVehicleGroupPieChart
from app.widgets.traffic_results import (
    BarChart,
    GroupedBarChart,
    description_page,
    empty_message_label,
    highlight_result_table_row,
    result_card,
    result_description_label,
    result_description_note,
    configure_result_description_note_layout,
    result_table,
    scrollable_result_table,
)
from app.widgets.traffic_summary_table import TrafficCountSummaryTable, traffic_count_summary_table

try:
    from qfluentwidgets import ComboBox, DoubleSpinBox, LineEdit, SpinBox

    FluentComboBox = ComboBox
    FluentSpinBox = SpinBox
    FluentDoubleSpinBox = DoubleSpinBox
    FluentLineEdit = LineEdit
except ImportError:
    from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox

    FluentComboBox = QComboBox
    FluentSpinBox = QSpinBox
    FluentDoubleSpinBox = QDoubleSpinBox
    FluentLineEdit = QLineEdit

__all__ = [
    "primary_button",
    "secondary_button",
    "make_combo",
    "make_decimal_line_edit",
    "make_double_spin",
    "make_integer_line_edit",
    "make_spin_no_buttons",
    "add_labeled_row",
    "LabeledInput",
    "add_labeled_select_row",
    "LabeledSelect",
    "make_design_year_combo",
    "info",
    "warning",
    "open_file",
    "save_file",
    "PageShell",
    "TrafficTotalLineChart",
    "TrafficVehicleGroupPieChart",
    "TrafficCountSummaryTable",
    "traffic_count_summary_table",
    "BarChart",
    "GroupedBarChart",
    "description_page",
    "empty_message_label",
    "highlight_result_table_row",
    "result_card",
    "result_description_label",
    "result_description_note",
    "configure_result_description_note_layout",
    "result_table",
    "scrollable_result_table",
    "FluentComboBox",
    "FluentSpinBox",
    "FluentDoubleSpinBox",
    "FluentLineEdit",
]
