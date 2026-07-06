"""ESAL calculations from temporary D1/D2 traffic session data."""
from __future__ import annotations

from dataclasses import dataclass

from app.services.esal_calculator import (
    AxleEsalRow,
    DESIGN_PERIODS_YEARS,
    TLD_UPLOAD_MESSAGE,
    build_axle_esal_rows,
    build_design_period_results,
    calculate_total_esal_per_day,
    classify_traffic,
    esal_chart_years,
    esal_table_years,
    has_tld_distribution,
)
from app.services.traffic_excel import VEHICLE_TYPE_COUNT, average_vehicle_totals

DESIGN_PERIODS = DESIGN_PERIODS_YEARS

# Axle summary table groups -> column indices in vehicle totals.
AXLE_TABLE_GROUPS: tuple[tuple[str, list[int]], ...] = (
    ("steering_sast", [0, 1, 2, 3, 4]),
    ("sadt", [5, 6]),
    ("tast", [8]),
    ("tadt", [9, 10]),
    ("trdt", list(range(11, VEHICLE_TYPE_COUNT))),
)

CHART_COLORS = ("#156082", "#e97132", "#196b24")


@dataclass(frozen=True)
class EsalDesignPeriodResult:
    years: int
    total_esal: int
    traffic_class: str


@dataclass(frozen=True)
class EsalResult:
    axle_numbers: dict[str, int]
    design_periods: tuple[EsalDesignPeriodResult, ...]
    chart_periods: tuple[EsalDesignPeriodResult, ...] = ()
    table_periods: tuple[EsalDesignPeriodResult, ...] = ()
    pavement_design_years: int = 0
    total_esal_per_day: float = 0.0
    axle_rows: tuple[AxleEsalRow, ...] = ()
    use_tld: bool = False
    tld_loads_ready: bool = False
    tld_message: str | None = None

    @property
    def has_data(self) -> bool:
        if any(count > 0 for count in self.axle_numbers.values()):
            return True
        if self.use_tld and self.tld_loads_ready:
            return True
        periods = self.chart_periods or self.design_periods
        return any(period.total_esal > 0 for period in periods)

    @property
    def axle_detail_rows(self) -> list[list[str]]:
        rows: list[list[str]] = []
        for row in self.axle_rows:
            count_text = f"{row.count:,}" if row.count > 0 else "-"
            factor_text = (
                "-"
                if self.use_tld and row.esal_factor is None
                else f"{row.esal_factor:,.6f}".rstrip("0").rstrip(".")
            )
            esal_day_text = f"{int(round(row.esal_per_day)):,}" if row.esal_per_day > 0 else "-"
            if self.use_tld:
                rows.append(
                    [
                        row.axle_type,
                        count_text,
                        f"{row.standard_load_kn:,.0f}",
                        factor_text,
                        f"{row.ldf:.1f}",
                        esal_day_text,
                    ]
                )
            else:
                actual_text = f"{row.actual_load_kn:,.2f}".rstrip("0").rstrip(".") if row.actual_load_kn else "-"
                rows.append(
                    [
                        row.axle_type,
                        f"{row.standard_load_kn:,.0f}",
                        actual_text,
                        count_text,
                        factor_text,
                        f"{row.ldf:.1f}",
                        esal_day_text,
                    ]
                )
        return rows

    @property
    def has_calculated_esal(self) -> bool:
        if self.use_tld and not self.tld_loads_ready:
            return False
        return self.total_esal_per_day > 0 or any(
            period.total_esal > 0 for period in (self.chart_periods or self.design_periods)
        )

    @property
    def esal_table_rows(self) -> list[list[str]]:
        rows: list[list[str]] = []
        for period in self.table_periods:
            if self.use_tld and not self.tld_loads_ready:
                rows.append([f"Year {period.years}", "—", "—"])
                continue
            rows.append(
                [
                    f"Year {period.years}",
                    f"{period.total_esal:,}",
                    period.traffic_class,
                ]
            )
        return rows

    @property
    def esal_table_highlight_row(self) -> int | None:
        if self.pavement_design_years <= 0 or not self.table_periods:
            return None
        years = [period.years for period in self.table_periods]
        if self.pavement_design_years in years:
            return years.index(self.pavement_design_years)
        return None


def get_traffic_class(esal_million: float) -> str:
    """Backward-compatible traffic class from ESAL in millions."""
    return classify_traffic(esal_million * 1_000_000)


def sum_vehicle_totals(
    daily_totals: dict[str, list[int]] | None = None,
    *,
    daily_totals_12h: dict[str, list[int]] | None = None,
    daily_totals_24h: dict[str, list[int]] | None = None,
    survey_hours: int = 12,
    count_hour: str = "12h",
) -> list[int]:
    """Average D1 and D2 daily totals for the selected count period and apply power."""
    return average_vehicle_totals(
        daily_totals_12h=daily_totals_12h,
        daily_totals_24h=daily_totals_24h,
        daily_totals=daily_totals,
        survey_hours=survey_hours,
        count_hour=count_hour,
    )


def vehicle_totals_from_summary_row(summary_total_row: list) -> list[int]:
    if not summary_total_row or len(summary_total_row) < 1 + VEHICLE_TYPE_COUNT:
        return []
    return [int(summary_total_row[index]) for index in range(1, 1 + VEHICLE_TYPE_COUNT)]


def build_axle_counts(vehicle_totals: list[int]) -> dict[str, int]:
    """Daily axle counts per axle group from averaged vehicle totals."""
    counts: dict[str, int] = {}
    for key, indices in AXLE_TABLE_GROUPS:
        total = 0
        for index in indices:
            if index < len(vehicle_totals):
                total += max(0, int(vehicle_totals[index] or 0))
        counts[key] = total
    return counts


def build_axle_numbers(vehicle_totals: list[int]) -> dict[str, int]:
    """Alias for daily axle counts shown in the ESAL axle table."""
    return build_axle_counts(vehicle_totals)


def _growth_rate_to_percent(growth_rate: float) -> float:
    rate = float(growth_rate or 0)
    if rate <= 0:
        return 0.0
    if rate <= 1.0:
        return rate * 100.0
    return rate


def _empty_period_results(
    years_list: tuple[int, ...],
) -> tuple[EsalDesignPeriodResult, ...]:
    return tuple(
        EsalDesignPeriodResult(years=years, total_esal=0, traffic_class="—")
        for years in years_list
    )


def _period_results_from_design_rows(
    rows: list[tuple[int, int, str]],
) -> tuple[EsalDesignPeriodResult, ...]:
    return tuple(
        EsalDesignPeriodResult(
            years=years,
            total_esal=total_esal,
            traffic_class=traffic_class,
        )
        for years, total_esal, traffic_class in rows
    )


def build_design_period_description(periods: tuple[EsalDesignPeriodResult, ...]) -> str:
    """Plain-text design period lines (backward compatible)."""
    lines = [
        f"- Design period in {period.years} year is {period.traffic_class}"
        for period in periods
    ]
    return "\n\n".join(lines)


def build_design_period_description_html(
    periods: tuple[EsalDesignPeriodResult, ...],
    *,
    panel_width: int | None = None,
) -> str:
    """HTML description for the ESAL tab."""
    from app.utils.result_html import result_highlight_style, wrap_result_description_lines

    highlight = result_highlight_style()
    lines: list[str] = []
    for period in periods:
        value = period.traffic_class if period.traffic_class and period.traffic_class != "—" else "____"
        lines.append(
            f'- Design period in {period.years} year is <span style="{highlight}">{value}</span>'
        )

    return wrap_result_description_lines(lines, panel_width=panel_width)


def _empty_description_periods() -> tuple[EsalDesignPeriodResult, ...]:
    """Placeholder 15/20/25 year lines before ESAL is calculated."""
    return tuple(
        EsalDesignPeriodResult(years=years, total_esal=0, traffic_class="—")
        for years in DESIGN_PERIODS
    )


def _description_periods(
    table_results: tuple[EsalDesignPeriodResult, ...],
) -> tuple[EsalDesignPeriodResult, ...]:
    """Always show 15, 20, and 25 year classifications in the description panel."""
    by_year = {period.years: period for period in table_results}
    return tuple(
        by_year.get(
            years,
            EsalDesignPeriodResult(years=years, total_esal=0, traffic_class="—"),
        )
        for years in DESIGN_PERIODS
    )


def _build_esal_result(
    axle_counts: dict[str, int],
    *,
    tld_distribution: list[dict[str, float]] | None = None,
    use_tld: bool = False,
    tld_loads_ready: bool = False,
    lane_count: int = 1,
    growth_rate: float = 0.05,
    pavement_design_years: int = 0,
) -> EsalResult:
    rate_percent = _growth_rate_to_percent(growth_rate)
    lane = max(1, min(3, int(lane_count or 1)))
    normalized_counts = {key: max(0, int(axle_counts.get(key, 0) or 0)) for key, _ in AXLE_TABLE_GROUPS}
    distribution = list(tld_distribution or [])
    distribution_ready = tld_loads_ready and has_tld_distribution(distribution)
    tld_message = None
    if use_tld and not distribution_ready:
        tld_message = TLD_UPLOAD_MESSAGE

    table_year_list = esal_table_years(pavement_design_years)
    chart_year_list = esal_chart_years(pavement_design_years)

    if not any(normalized_counts.values()):
        empty_table = _empty_period_results(table_year_list)
        empty_chart = _empty_period_results(chart_year_list)
        return EsalResult(
            axle_numbers=normalized_counts,
            design_periods=_empty_description_periods(),
            chart_periods=empty_chart,
            table_periods=empty_table,
            pavement_design_years=pavement_design_years,
            total_esal_per_day=0.0,
            axle_rows=(),
            use_tld=use_tld,
            tld_loads_ready=distribution_ready,
            tld_message=tld_message,
        )

    axle_rows = build_axle_esal_rows(
        normalized_counts,
        tld_distribution=distribution,
        use_tld=use_tld,
        tld_loads_ready=distribution_ready,
        lane_each_direction=lane,
    )
    total_per_day = calculate_total_esal_per_day(list(axle_rows))
    description_rows = build_design_period_results(
        total_per_day,
        rate_percent=rate_percent,
        periods=DESIGN_PERIODS,
    )
    description_periods = _period_results_from_design_rows(description_rows)
    table_rows = build_design_period_results(
        total_per_day,
        rate_percent=rate_percent,
        periods=table_year_list,
    )
    table_results = _period_results_from_design_rows(table_rows)
    chart_rows = build_design_period_results(
        total_per_day,
        rate_percent=rate_percent,
        periods=chart_year_list,
    )
    chart_results = _period_results_from_design_rows(chart_rows)

    return EsalResult(
        axle_numbers=normalized_counts,
        design_periods=description_periods,
        chart_periods=chart_results,
        table_periods=table_results,
        pavement_design_years=pavement_design_years,
        total_esal_per_day=total_per_day,
        axle_rows=axle_rows,
        use_tld=use_tld,
        tld_loads_ready=distribution_ready,
        tld_message=tld_message,
    )


def compute_esal(
    daily_totals: dict[str, list[int]] | None = None,
    *,
    daily_totals_12h: dict[str, list[int]] | None = None,
    daily_totals_24h: dict[str, list[int]] | None = None,
    survey_hours: int = 12,
    count_hour: str = "12h",
    summary_total_row: list | None = None,
    growth_rate: float = 0.05,
    lane_count: int = 1,
    use_tld: bool = False,
    tld_distribution: list[dict[str, float]] | None = None,
    pavement_design_years: int = 0,
    vehicle_totals_override: list[int] | None = None,
) -> EsalResult:
    if vehicle_totals_override is not None:
        vehicle_totals = list(vehicle_totals_override)
    elif summary_total_row:
        vehicle_totals = vehicle_totals_from_summary_row(summary_total_row)
    elif daily_totals or daily_totals_12h or daily_totals_24h:
        vehicle_totals = sum_vehicle_totals(
            daily_totals,
            daily_totals_12h=daily_totals_12h,
            daily_totals_24h=daily_totals_24h,
            survey_hours=survey_hours,
            count_hour=count_hour,
        )
    else:
        vehicle_totals = []

    axle_counts = build_axle_counts(vehicle_totals)
    distribution_ready = has_tld_distribution(tld_distribution) if use_tld else False
    return _build_esal_result(
        axle_counts,
        tld_distribution=tld_distribution,
        use_tld=use_tld,
        tld_loads_ready=distribution_ready,
        lane_count=lane_count,
        growth_rate=growth_rate,
        pavement_design_years=pavement_design_years,
    )


def compute_esal_from_workbook_data(
    workbook_data: dict,
    *,
    growth_rate: float = 0.05,
    lane_count: int = 1,
    pavement_design_years: int = 0,
    use_tld: bool = False,
    tld_data: dict | None = None,
) -> EsalResult:
    vehicle_totals = _vehicle_totals_from_workbook(workbook_data)
    axle_counts = build_axle_counts(vehicle_totals)
    tld_distribution: list[dict[str, float]] | None = None
    distribution_ready = False

    if use_tld and tld_data:
        tld_distribution = list(tld_data.get("distribution_rows") or [])
        distribution_ready = (
            bool(tld_data.get("has_parsed_distribution"))
            or bool(tld_data.get("has_parsed_loads"))
            or has_tld_distribution(tld_distribution)
        )

    return _build_esal_result(
        axle_counts,
        tld_distribution=tld_distribution,
        use_tld=use_tld,
        tld_loads_ready=distribution_ready,
        lane_count=lane_count,
        growth_rate=growth_rate,
        pavement_design_years=pavement_design_years,
    )


def _vehicle_totals_from_workbook(workbook_data: dict) -> list[int]:
    summary_total_row = workbook_data.get("summary_total_row")
    if summary_total_row:
        return vehicle_totals_from_summary_row(summary_total_row)
    daily_totals = workbook_data.get("daily_totals")
    daily_totals_12h = workbook_data.get("daily_totals_12h")
    daily_totals_24h = workbook_data.get("daily_totals_24h")
    if daily_totals or daily_totals_12h or daily_totals_24h:
        return sum_vehicle_totals(
            daily_totals,
            daily_totals_12h=daily_totals_12h,
            daily_totals_24h=daily_totals_24h,
            survey_hours=int(workbook_data.get("survey_hours") or 12),
            count_hour=workbook_data.get("traffic_count_hour", "12h"),
        )
    return []


def chart_bars_from_esal(result: EsalResult) -> list[tuple[str, float, str]]:
    bars: list[tuple[str, float, str]] = []
    periods = result.chart_periods or result.design_periods
    for index, period in enumerate(periods):
        color = CHART_COLORS[index % len(CHART_COLORS)]
        bars.append((f"Year {period.years}", float(period.total_esal), color))
    return bars
