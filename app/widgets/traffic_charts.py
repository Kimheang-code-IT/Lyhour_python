"""Traffic summary line/pie charts."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from app.core.ui_scale import UiScale
from app.core.theme import theme_tokens
from app.services.traffic_excel import chart_time_display_label

Y_AXIS_STEP = 500
_EMPTY_MESSAGE = "No data yet. Upload Excel from Traffic Analysis Input."

class TrafficTotalLineChart(QWidget):
    """Line chart using time on X and total traffic on Y."""

    def __init__(self, rows: list[list], parent=None):
        super().__init__(parent)
        self._labels = [str(row[0]) for row in rows]
        self._values = [int(row[-1]) for row in rows]
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(self._auto_chart_height())

    def sizeHint(self) -> QSize:
        return QSize(640, self._auto_chart_height())

    def _auto_chart_height(self) -> int:
        return max(UiScale.px(420), UiScale.px(340) + max(0, len(self._values) - 12) * UiScale.px(10))

    def _layout_metrics(self, point_count: int, plot_width: int) -> dict[str, float | int | bool]:
        compact = point_count > 12
        if point_count > 20:
            x_font_pt = 7
            value_font_pt = 7
            bottom_margin = 64
            x_label_height = 28
        elif point_count > 12:
            x_font_pt = 8
            value_font_pt = 8
            bottom_margin = 68
            x_label_height = 32
        else:
            x_font_pt = 10
            value_font_pt = 10
            bottom_margin = 76
            x_label_height = 40

        step_x = plot_width / max(point_count - 1, 1)
        label_box = max(UiScale.px(30), int(step_x))
        return {
            "compact": compact,
            "x_font_pt": x_font_pt,
            "value_font_pt": value_font_pt,
            "bottom_margin": bottom_margin,
            "x_label_height": x_label_height,
            "label_box": label_box,
        }

    def paintEvent(self, event):
        super().paintEvent(event)
        tokens = theme_tokens()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        point_count = len(self._values)
        metrics = self._layout_metrics(point_count, max(self.width() - UiScale.px(80), UiScale.px(200)))
        bottom_margin = int(metrics["bottom_margin"])
        top_margin = UiScale.px(40)
        rect = self.rect().adjusted(
            UiScale.px(64),
            top_margin,
            -UiScale.px(16),
            -bottom_margin,
        )

        if not self._values:
            label_font = painter.font()
            label_font.setPointSizeF(UiScale.pt(9))
            painter.setFont(label_font)
            painter.setPen(QColor(tokens.text_muted))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _EMPTY_MESSAGE)
            return

        legend_font = painter.font()
        legend_font.setPointSizeF(UiScale.pt(12))
        legend_font.setBold(True)
        painter.setFont(legend_font)
        painter.setPen(QColor(tokens.chart_label))
        painter.drawText(
            UiScale.px(64),
            UiScale.px(10),
            UiScale.px(120),
            UiScale.px(24),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Total",
        )

        min_value = 0
        max_value = max(self._values)
        axis_max = max(Y_AXIS_STEP, ((max_value + Y_AXIS_STEP - 1) // Y_AXIS_STEP) * Y_AXIS_STEP)
        span = max(axis_max - min_value, 1)
        step_x = rect.width() / max(point_count - 1, 1)
        label_box = max(int(metrics["label_box"]), int(step_x))

        painter.setPen(QPen(QColor(tokens.chart_axis), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())

        axis_font = painter.font()
        axis_font.setPointSizeF(UiScale.pt(12))
        axis_font.setBold(False)
        painter.setFont(axis_font)

        for value in range(0, axis_max + Y_AXIS_STEP, Y_AXIS_STEP):
            y = int(rect.bottom() - ((value - min_value) / span) * rect.height())
            painter.setPen(QPen(QColor(tokens.chart_grid), 1))
            painter.drawLine(rect.left(), y, rect.right(), y)
            painter.setPen(QColor(tokens.chart_value))
            painter.drawText(
                4,
                y - UiScale.px(10),
                UiScale.px(56),
                UiScale.px(24),
                Qt.AlignmentFlag.AlignRight,
                str(value),
            )

        points: list[QPointF] = []
        for index, value in enumerate(self._values):
            x = rect.left() + step_x * index
            y = rect.bottom() - ((value - min_value) / span) * rect.height()
            points.append(QPointF(x, y))

        painter.setPen(QPen(QColor("#4da3ff"), 2))
        for start, end in zip(points, points[1:]):
            painter.drawLine(start, end)

        painter.setBrush(QColor("#4da3ff"))
        painter.setPen(Qt.PenStyle.NoPen)
        marker_radius = 2 if point_count > 20 else 3
        for point in points:
            painter.drawEllipse(point, marker_radius, marker_radius)

        painter.setPen(QColor(tokens.chart_value))
        time_font = painter.font()
        time_font.setPointSizeF(UiScale.pt(10))
        time_font.setBold(False)
        painter.setFont(time_font)
        painter.drawText(rect.right() - UiScale.px(28), self.height() - UiScale.px(14), "Time")

        x_font_pt = float(metrics["x_font_pt"])
        value_font_pt = float(metrics["value_font_pt"])
        x_label_height = int(metrics["x_label_height"])
        compact = bool(metrics["compact"])

        label_font = painter.font()
        label_font.setPointSizeF(UiScale.pt(x_font_pt))
        painter.setFont(label_font)
        for index, (label, value, point) in enumerate(zip(self._labels, self._values, points)):
            x = int(rect.left() + step_x * index - label_box / 2)
            display_label = chart_time_display_label(label, compact=compact)
            painter.drawText(
                x,
                rect.bottom() + UiScale.px(6),
                label_box,
                x_label_height,
                Qt.AlignmentFlag.AlignCenter,
                display_label,
            )

        value_font = painter.font()
        value_font.setPointSizeF(UiScale.pt(value_font_pt))
        painter.setFont(value_font)
        value_box = label_box
        for index, (value, point) in enumerate(zip(self._values, points)):
            x = int(rect.left() + step_x * index - value_box / 2)
            value_y = max(rect.top() - UiScale.px(18), int(point.y()) - UiScale.px(18))
            painter.drawText(x, value_y, value_box, UiScale.px(18), Qt.AlignmentFlag.AlignCenter, str(value))


class TrafficVehicleGroupPieChart(QWidget):
    """Pie chart for three vehicle groups (D1 + D2 summed)."""

    def __init__(self, groups: list[tuple[str, int, str]] | None = None, parent=None):
        super().__init__(parent)
        self._groups = groups or []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(UiScale.px(260))

    def sizeHint(self) -> QSize:
        return QSize(640, UiScale.px(260))

    def paintEvent(self, event):
        super().paintEvent(event)
        tokens = theme_tokens()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._groups or not any(value for _label, value, _color in self._groups):
            label_font = painter.font()
            label_font.setPointSizeF(UiScale.pt(9))
            painter.setFont(label_font)
            painter.setPen(QColor(tokens.text_muted))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _EMPTY_MESSAGE)
            return

        total = sum(value for _label, value, _color in self._groups)
        if total <= 0:
            label_font = painter.font()
            label_font.setPointSizeF(UiScale.pt(9))
            painter.setFont(label_font)
            painter.setPen(QColor(tokens.text_muted))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, _EMPTY_MESSAGE)
            return

        side = min(self.width() - UiScale.px(24), self.height() - UiScale.px(72), UiScale.px(220))
        pie_rect = QRectF(
            (self.width() - side) / 2,
            UiScale.px(28),
            side,
            side,
        )

        start_angle = 90 * 16
        for _label, value, color in self._groups:
            if value <= 0:
                continue
            span_angle = -int(round((value / total) * 360 * 16))
            painter.setBrush(QColor(color))
            painter.setPen(QPen(QColor(tokens.bg_window), 2))
            painter.drawPie(pie_rect, start_angle, span_angle)
            start_angle += span_angle

        legend_y = int(pie_rect.bottom()) + UiScale.px(18)
        row_height = UiScale.px(24)
        legend_font = painter.font()
        legend_font.setPointSizeF(UiScale.pt(9))
        painter.setFont(legend_font)
        metrics = QFontMetrics(legend_font)
        swatch_size = UiScale.px(12)
        swatch_gap = UiScale.px(8)
        item_gap = UiScale.px(28)
        legend_entries: list[tuple[str, int, str, str]] = []
        for label, value, color in self._groups:
            percent = (value / total) * 100
            legend_entries.append((label, value, color, f"{label}: {value:,} ({percent:.1f}%)"))

        total_legend_width = 0
        for index, (_label, _value, _color, text) in enumerate(legend_entries):
            total_legend_width += swatch_size + swatch_gap + metrics.horizontalAdvance(text)
            if index < len(legend_entries) - 1:
                total_legend_width += item_gap

        x = int((self.width() - total_legend_width) / 2)
        for label, value, color, text in legend_entries:
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, legend_y + UiScale.px(5), swatch_size, swatch_size, 2, 2)
            painter.setPen(QColor(tokens.chart_label))
            painter.drawText(
                x + swatch_size + swatch_gap,
                legend_y,
                metrics.horizontalAdvance(text) + UiScale.px(4),
                row_height,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )
            x += swatch_size + swatch_gap + metrics.horizontalAdvance(text) + item_gap

