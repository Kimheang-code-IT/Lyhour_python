"""Application settings dialog — Fluent controls matching Traffic Input / Analysis pages."""
from __future__ import annotations

from copy import deepcopy

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.shortcuts import APP_SHORTCUTS, TOGGLEABLE_SHORTCUT_IDS
from app.core.i18n import tr
from app.core.theme import card_stylesheet, theme_tokens
from app.services.app_settings import FONT_SCALE_OPTIONS, AppSettings, AppSettingsData
from app.widgets.button import primary_button, secondary_button
from app.widgets.loading_overlay import LoadingOverlay
from app.widgets.form_controls import (
    combo_current_data,
    make_data_combo,
    make_double_spin,
    make_switch,
    set_combo_data,
)
from app.widgets.labeled_input import add_labeled_row

try:
    from qfluentwidgets import (
        BodyLabel,
        ColorDialog,
        FluentIcon,
        MaskDialogBase,
        PushButton,
        PrimaryPushButton,
        SegmentedWidget,
        SubtitleLabel,
        TransparentToolButton,
    )
    from qfluentwidgets.common.style_sheet import FluentStyleSheet

    _HAS_FLUENT = True
except Exception:
    MaskDialogBase = None  # type: ignore[assignment,misc]
    ColorDialog = None  # type: ignore[assignment,misc]
    SegmentedWidget = None  # type: ignore[assignment,misc]
    SubtitleLabel = None  # type: ignore[assignment,misc]
    BodyLabel = None  # type: ignore[assignment,misc]
    PushButton = None  # type: ignore[assignment,misc]
    PrimaryPushButton = None  # type: ignore[assignment,misc]
    FluentStyleSheet = None  # type: ignore[assignment,misc]
    FluentIcon = None  # type: ignore[assignment,misc]
    TransparentToolButton = None  # type: ignore[assignment,misc]
    _HAS_FLUENT = False

_ROW_HEIGHT = 36


def _section_style() -> str:
    return card_stylesheet(theme_tokens())


class _AccentColorPicker(QWidget):
    """Color swatch + hex label + choose button (opens Fluent ColorDialog)."""

    def __init__(self, color: str = "#0078D4", parent=None) -> None:
        super().__init__(parent)
        self._color = QColor(color or "#0078D4")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self._swatch = QFrame()
        self._swatch.setFixedSize(_ROW_HEIGHT, _ROW_HEIGHT)
        self._swatch.setObjectName("accentSwatch")

        if _HAS_FLUENT and BodyLabel is not None:
            self._hex_label = BodyLabel(self._color.name())
        else:
            self._hex_label = QLabel(self._color.name())

        self._choose_btn = secondary_button(tr("settings.choose_color"), min_height=_ROW_HEIGHT)
        self._choose_btn.setFixedWidth(96)
        self._choose_btn.setToolTip(tr("settings.accent"))
        self._choose_btn.clicked.connect(self._pick_color)

        row.addWidget(self._swatch)
        row.addWidget(self._hex_label, 1)
        row.addWidget(self._choose_btn)
        self._apply_swatch_style()

    def _apply_swatch_style(self) -> None:
        name = self._color.name()
        self._swatch.setStyleSheet(
            f"#accentSwatch {{ background-color: {name}; border: 1px solid #888888; border-radius: 6px; }}"
        )
        self._hex_label.setText(name)

    def _pick_color(self) -> None:
        parent = self.window()
        if _HAS_FLUENT and ColorDialog is not None:
            dialog = ColorDialog(self._color, tr("settings.accent"), parent)
            if dialog.exec():
                self._color = QColor(dialog.color)
                self._apply_swatch_style()
            return

        from PyQt6.QtWidgets import QColorDialog

        picked = QColorDialog.getColor(self._color, parent, tr("settings.accent"))
        if picked.isValid():
            self._color = picked
            self._apply_swatch_style()

    def color_hex(self) -> str:
        return self._color.name()

    def set_color_hex(self, value: str) -> None:
        self._color = QColor(value or "#0078D4")
        self._apply_swatch_style()


def _section_frame(parent: QWidget | None = None) -> tuple[QFrame, QGridLayout]:
    frame = QFrame(parent)
    frame.setObjectName("settingsSectionFrame")
    frame.setStyleSheet(_section_style())
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(16, 12, 16, 16)
    outer.setSpacing(10)
    grid = QGridLayout()
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(12)
    grid.setContentsMargins(0, 0, 0, 0)
    outer.addLayout(grid)
    return frame, grid


class _SettingsPanel:
    """Shared panel builder used by Fluent and fallback dialogs."""

    def __init__(self, parent=None) -> None:
        self.parent = parent
        self._draft = AppSettings.instance().data
        self._language_combo = None
        self._theme_combo = None
        self._font_combo = None
        self._accent_picker = None
        self._tooltips_sw = None
        self._confirm_exit_sw = None
        self._sidebar_sw = None
        self._preview_sw = None
        self._remember_sw = None
        self._compact_sw = None
        self._auto_refresh_sw = None
        self._growth_spin = None
        self._shortcut_hints_sw = None
        self._shortcut_switches: dict[str, object] = {}

    def build(self, root: QVBoxLayout, *, header_right: QWidget | None = None) -> None:
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)
        if _HAS_FLUENT and SubtitleLabel is not None:
            title = SubtitleLabel(tr("settings.title"))
        else:
            title = QLabel(tr("settings.title"))
            title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch(1)
        if header_right is not None:
            header_row.addWidget(header_right)
        root.addLayout(header_row)

        if _HAS_FLUENT and SegmentedWidget is not None:
            segmented = SegmentedWidget()
            stack = QStackedWidget()
            tabs = [
                ("general", tr("settings.tab.general"), self._build_general_tab()),
                ("appearance", tr("settings.tab.appearance"), self._build_appearance_tab()),
                ("workspace", tr("settings.tab.workspace"), self._build_workspace_tab()),
                ("shortcuts", tr("settings.tab.shortcuts"), self._build_shortcuts_tab()),
                ("advanced", tr("settings.tab.advanced"), self._build_advanced_tab()),
            ]
            for index, (route_key, text, page) in enumerate(tabs):
                segmented.addItem(
                    route_key,
                    text,
                    onClick=lambda *_args, i=index: stack.setCurrentIndex(i),
                )
                stack.addWidget(page)
            segmented.setCurrentItem("general")
            root.addWidget(segmented)
            root.addWidget(stack, 1)
        else:
            root.addWidget(self._build_general_tab())
            root.addWidget(self._build_appearance_tab())
            root.addWidget(self._build_workspace_tab())
            root.addWidget(self._build_shortcuts_tab())
            root.addWidget(self._build_advanced_tab(), 1)

        if _HAS_FLUENT and BodyLabel is not None:
            note = BodyLabel(tr("settings.restart_note"))
        else:
            note = QLabel(tr("settings.restart_note"))
            note.setStyleSheet("color: #888888; font-size: 12px;")
        note.setWordWrap(True)
        root.addWidget(note)

        self._load_draft_into_controls()

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        frame, grid = _section_frame(tab)
        row = 0

        self._language_combo = make_data_combo(
            [
                (tr("settings.language.en"), "en"),
                (tr("settings.language.km"), "km"),
            ]
        )
        add_labeled_row(grid, row, tr("settings.language"), self._language_combo, _ROW_HEIGHT)
        row += 1

        self._tooltips_sw = make_switch(checked=self._draft.show_tooltips)
        add_labeled_row(grid, row, tr("settings.tooltips"), self._tooltips_sw, _ROW_HEIGHT)
        row += 1

        self._confirm_exit_sw = make_switch(checked=self._draft.confirm_exit)
        add_labeled_row(grid, row, tr("settings.confirm_exit"), self._confirm_exit_sw, _ROW_HEIGHT)

        layout.addWidget(frame)
        layout.addStretch()
        return tab

    def _build_appearance_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        frame, grid = _section_frame(tab)
        row = 0

        self._theme_combo = make_data_combo(
            [
                (tr("settings.theme.dark"), "dark"),
                (tr("settings.theme.light"), "light"),
            ]
        )
        add_labeled_row(grid, row, tr("settings.theme"), self._theme_combo, _ROW_HEIGHT)
        row += 1

        self._font_combo = make_data_combo(
            [(tr(label_key), value) for label_key, value in FONT_SCALE_OPTIONS]
        )
        add_labeled_row(grid, row, tr("settings.font_size"), self._font_combo, _ROW_HEIGHT)
        row += 1

        self._accent_picker = _AccentColorPicker(self._draft.accent_color)
        add_labeled_row(grid, row, tr("settings.accent"), self._accent_picker, _ROW_HEIGHT)

        layout.addWidget(frame)
        layout.addStretch()
        return tab

    def _build_workspace_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        frame, grid = _section_frame(tab)
        row = 0

        self._sidebar_sw = make_switch(checked=self._draft.sidebar_visible)
        add_labeled_row(grid, row, tr("settings.sidebar_visible"), self._sidebar_sw, _ROW_HEIGHT)
        row += 1

        self._preview_sw = make_switch(checked=self._draft.preview_visible)
        add_labeled_row(grid, row, tr("settings.preview_visible"), self._preview_sw, _ROW_HEIGHT)
        row += 1

        self._remember_sw = make_switch(checked=self._draft.remember_panel_layout)
        add_labeled_row(grid, row, tr("settings.remember_layout"), self._remember_sw, _ROW_HEIGHT)
        row += 1

        self._compact_sw = make_switch(checked=self._draft.compact_mode)
        add_labeled_row(grid, row, tr("settings.compact_mode"), self._compact_sw, _ROW_HEIGHT)

        layout.addWidget(frame)
        layout.addStretch()
        return tab

    def _build_shortcuts_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        frame, grid = _section_frame(tab)
        row = 0

        self._shortcut_hints_sw = make_switch(checked=self._draft.show_shortcut_hints)
        add_labeled_row(grid, row, tr("settings.shortcuts.hints"), self._shortcut_hints_sw, _ROW_HEIGHT)
        row += 1

        if _HAS_FLUENT and BodyLabel is not None:
            action_hdr = BodyLabel(tr("settings.shortcuts.action"))
            keys_hdr = BodyLabel(tr("settings.shortcuts.keys"))
            enabled_hdr = BodyLabel(tr("settings.shortcuts.enabled"))
        else:
            action_hdr = QLabel(tr("settings.shortcuts.action"))
            keys_hdr = QLabel(tr("settings.shortcuts.keys"))
            enabled_hdr = QLabel(tr("settings.shortcuts.enabled"))
            header_style = "font-weight: 600; color: #b5bac8;"
            action_hdr.setStyleSheet(header_style)
            keys_hdr.setStyleSheet(header_style)
            enabled_hdr.setStyleSheet(header_style)

        grid.addWidget(action_hdr, row, 0)
        grid.addWidget(keys_hdr, row, 1)
        grid.addWidget(enabled_hdr, row, 2, alignment=Qt.AlignmentFlag.AlignRight)
        row += 1

        last_category = ""
        self._shortcut_switches.clear()
        for spec in APP_SHORTCUTS:
            if spec.category_key != last_category:
                if _HAS_FLUENT and BodyLabel is not None:
                    category = BodyLabel(tr(spec.category_key))
                else:
                    category = QLabel(tr(spec.category_key))
                    category.setStyleSheet("color: #9aa0a6; font-size: 12px; font-weight: 600;")
                grid.addWidget(category, row, 0, 1, 3)
                row += 1
                last_category = spec.category_key

            if _HAS_FLUENT and BodyLabel is not None:
                action_lbl = BodyLabel(tr(spec.label_key))
                keys_lbl = BodyLabel(spec.sequence)
            else:
                action_lbl = QLabel(tr(spec.label_key))
                keys_lbl = QLabel(spec.sequence)
                keys_lbl.setStyleSheet("color: #cccccc; font-family: Consolas, monospace;")

            grid.addWidget(action_lbl, row, 0)
            grid.addWidget(keys_lbl, row, 1)

            if spec.toggleable:
                switch = make_switch(checked=spec.id not in self._draft.disabled_shortcuts)
                self._shortcut_switches[spec.id] = switch
                grid.addWidget(switch, row, 2, alignment=Qt.AlignmentFlag.AlignRight)
            else:
                spacer = QWidget()
                spacer.setFixedHeight(_ROW_HEIGHT)
                grid.addWidget(spacer, row, 2)
            row += 1

        layout.addWidget(frame)
        layout.addStretch()
        return tab

    def _build_advanced_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        frame, grid = _section_frame(tab)
        row = 0

        self._auto_refresh_sw = make_switch(checked=self._draft.auto_refresh_results)
        add_labeled_row(grid, row, tr("settings.auto_refresh"), self._auto_refresh_sw, _ROW_HEIGHT)
        row += 1

        self._growth_spin = make_double_spin()
        self._growth_spin.setRange(0.0, 25.0)
        self._growth_spin.setDecimals(1)
        self._growth_spin.setSuffix(" %")
        self._growth_spin.setMinimumHeight(_ROW_HEIGHT)
        self._growth_spin.setMaximumHeight(_ROW_HEIGHT)
        add_labeled_row(grid, row, tr("settings.growth_rate"), self._growth_spin, _ROW_HEIGHT)

        layout.addWidget(frame)
        layout.addStretch()
        return tab

    def _load_draft_into_controls(self) -> None:
        d = self._draft
        if self._language_combo is not None:
            set_combo_data(self._language_combo, d.language)
        if self._theme_combo is not None:
            set_combo_data(self._theme_combo, d.theme)
        if self._font_combo is not None:
            set_combo_data(self._font_combo, d.font_scale)
        if self._accent_picker is not None:
            self._accent_picker.set_color_hex(d.accent_color)
        if self._tooltips_sw is not None:
            self._tooltips_sw.setChecked(d.show_tooltips)
        if self._confirm_exit_sw is not None:
            self._confirm_exit_sw.setChecked(d.confirm_exit)
        if self._sidebar_sw is not None:
            self._sidebar_sw.setChecked(d.sidebar_visible)
        if self._preview_sw is not None:
            self._preview_sw.setChecked(d.preview_visible)
        if self._remember_sw is not None:
            self._remember_sw.setChecked(d.remember_panel_layout)
        if self._compact_sw is not None:
            self._compact_sw.setChecked(d.compact_mode)
        if self._auto_refresh_sw is not None:
            self._auto_refresh_sw.setChecked(d.auto_refresh_results)
        if self._growth_spin is not None:
            self._growth_spin.setValue(d.default_growth_rate)
        if self._shortcut_hints_sw is not None:
            self._shortcut_hints_sw.setChecked(d.show_shortcut_hints)
        for shortcut_id, switch in self._shortcut_switches.items():
            switch.setChecked(shortcut_id not in d.disabled_shortcuts)

    def collect_draft(self) -> AppSettingsData:
        d = deepcopy(self._draft)
        if self._language_combo is not None:
            d.language = combo_current_data(self._language_combo) or "en"
        if self._theme_combo is not None:
            d.theme = combo_current_data(self._theme_combo) or "dark"
        if self._font_combo is not None:
            d.font_scale = float(combo_current_data(self._font_combo) or 1.0)
        if self._accent_picker is not None:
            d.accent_color = self._accent_picker.color_hex()
        if self._tooltips_sw is not None:
            d.show_tooltips = self._tooltips_sw.isChecked()
        if self._confirm_exit_sw is not None:
            d.confirm_exit = self._confirm_exit_sw.isChecked()
        if self._sidebar_sw is not None:
            d.sidebar_visible = self._sidebar_sw.isChecked()
        if self._preview_sw is not None:
            d.preview_visible = self._preview_sw.isChecked()
        if self._remember_sw is not None:
            d.remember_panel_layout = self._remember_sw.isChecked()
        if self._compact_sw is not None:
            d.compact_mode = self._compact_sw.isChecked()
        if self._auto_refresh_sw is not None:
            d.auto_refresh_results = self._auto_refresh_sw.isChecked()
        if self._growth_spin is not None:
            d.default_growth_rate = float(self._growth_spin.value())
        if self._shortcut_hints_sw is not None:
            d.show_shortcut_hints = self._shortcut_hints_sw.isChecked()
        disabled: list[str] = []
        for shortcut_id, switch in self._shortcut_switches.items():
            if shortcut_id in TOGGLEABLE_SHORTCUT_IDS and not switch.isChecked():
                disabled.append(shortcut_id)
        d.disabled_shortcuts = disabled
        return d.normalized()

    def apply(self) -> None:
        self._draft = self.collect_draft()
        AppSettings.instance().save(self._draft)


class _SettingsApplyController:
    """Show loading UI while settings save and the main window refreshes."""

    def __init__(self, dialog, panel: _SettingsPanel, overlay_parent: QWidget) -> None:
        self._dialog = dialog
        self._panel = panel
        self._overlay = LoadingOverlay(overlay_parent)
        self._applying = False
        self._close_after = False
        self._action_buttons: list[QWidget] = []

    def register_action_buttons(self, *buttons: QWidget) -> None:
        self._action_buttons = list(buttons)

    def apply_only(self) -> None:
        self._run_apply(close=False)

    def apply_and_close(self) -> None:
        self._run_apply(close=True)

    def _main_window(self):
        candidate = self._dialog.parent()
        while candidate is not None:
            if hasattr(candidate, "settingsApplyFinished"):
                return candidate
            candidate = candidate.parent()
        return None

    def _run_apply(self, *, close: bool) -> None:
        if self._applying:
            return
        self._applying = True
        self._close_after = close
        self._set_actions_enabled(False)
        self._overlay.show_busy(tr("settings.applying"))
        QApplication.processEvents()

        main_window = self._main_window()
        if main_window is not None:
            main_window.settingsApplyFinished.connect(
                self._on_main_apply_finished,
                Qt.ConnectionType.SingleShotConnection,
            )
            QTimer.singleShot(0, self._panel.apply)
        else:
            QTimer.singleShot(0, self._apply_without_main_window)

    def _apply_without_main_window(self) -> None:
        self._panel.apply()
        self._on_main_apply_finished()

    def _on_main_apply_finished(self) -> None:
        if not self._applying:
            return
        self._overlay.hide_busy()
        self._set_actions_enabled(True)
        self._applying = False
        if self._close_after:
            self._dialog.accept()

    def _set_actions_enabled(self, enabled: bool) -> None:
        for button in self._action_buttons:
            button.setEnabled(enabled)


if _HAS_FLUENT and MaskDialogBase is not None:

    def _make_close_button(parent: QWidget | None) -> QWidget:
        btn = TransparentToolButton(FluentIcon.CLOSE, parent)
        btn.setFixedSize(32, 32)
        btn.setToolTip(tr("settings.cancel"))
        return btn

    class FluentSettingsDialog(MaskDialogBase):
        """Fluent mask dialog with segmented tabs (like Analysis page)."""

        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self._panel = _SettingsPanel(parent)

            self.widget.setObjectName("settingsDialog")
            self.widget.setFixedSize(600, 580)
            self.setMaskColor(QColor(0, 0, 0, 120))

            shell = QVBoxLayout(self.widget)
            shell.setContentsMargins(24, 20, 24, 16)
            shell.setSpacing(12)

            close_btn = _make_close_button(self.widget)
            close_btn.clicked.connect(self.reject)
            self._panel.build(shell, header_right=close_btn)

            button_row = QHBoxLayout()
            button_row.setSpacing(10)
            self._cancel_btn = PushButton(tr("settings.cancel"))
            self._apply_btn = PushButton(tr("settings.apply"))
            self._ok_btn = PrimaryPushButton(tr("settings.ok"))
            button_row.addStretch(1)
            button_row.addWidget(self._cancel_btn)
            button_row.addWidget(self._apply_btn)
            button_row.addWidget(self._ok_btn)
            shell.addLayout(button_row)

            if FluentStyleSheet is not None:
                FluentStyleSheet.DIALOG.apply(self.widget)

            self._cancel_btn.clicked.connect(self.reject)
            self._apply_btn.clicked.connect(self._apply_only)
            self._ok_btn.clicked.connect(self._accept)

            self._apply_controller = _SettingsApplyController(self, self._panel, self.widget)
            self._apply_controller.register_action_buttons(
                self._cancel_btn,
                self._apply_btn,
                self._ok_btn,
            )

        def _apply_only(self) -> None:
            self._apply_controller.apply_only()

        def _accept(self) -> None:
            self._apply_controller.apply_and_close()

    SettingsDialog = FluentSettingsDialog  # type: ignore[misc,assignment]

else:
    from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QToolButton

    def _make_fallback_close_button(parent: QWidget | None) -> QWidget:
        btn = QToolButton(parent)
        btn.setText("\u2715")
        btn.setFixedSize(32, 32)
        btn.setToolTip(tr("settings.cancel"))
        btn.setStyleSheet(
            "QToolButton { border: none; border-radius: 4px; font-size: 16px; color: #cccccc; }"
            "QToolButton:hover { background-color: #3e3e40; }"
        )
        return btn

    class _FallbackSettingsDialog(QDialog):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setWindowTitle(tr("settings.title"))
            self.setModal(True)
            self.resize(580, 540)
            self._panel = _SettingsPanel(parent)

            root = QVBoxLayout(self)
            root.setContentsMargins(16, 16, 16, 16)
            close_btn = _make_fallback_close_button(self)
            close_btn.clicked.connect(self.reject)
            self._panel.build(root, header_right=close_btn)

            buttons = QDialogButtonBox()
            cancel = secondary_button(tr("settings.cancel"))
            apply_btn = secondary_button(tr("settings.apply"))
            ok_btn = primary_button(tr("settings.ok"))
            buttons.addButton(cancel, QDialogButtonBox.ButtonRole.RejectRole)
            buttons.addButton(apply_btn, QDialogButtonBox.ButtonRole.ApplyRole)
            buttons.addButton(ok_btn, QDialogButtonBox.ButtonRole.AcceptRole)
            root.addWidget(buttons)
            cancel.clicked.connect(self.reject)
            apply_btn.clicked.connect(self._apply_only)
            ok_btn.clicked.connect(self._accept)

            self._apply_controller = _SettingsApplyController(self, self._panel, self)
            self._apply_controller.register_action_buttons(cancel, apply_btn, ok_btn)

        def _apply_only(self) -> None:
            self._apply_controller.apply_only()

        def _accept(self) -> None:
            self._apply_controller.apply_and_close()

    SettingsDialog = _FallbackSettingsDialog  # type: ignore[misc,assignment]
