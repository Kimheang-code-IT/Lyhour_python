"""Unit tests for ESAL calculator helpers."""
from __future__ import annotations

import unittest

from app.services.esal_calculator import (
    build_axle_esal_rows,
    calculate_axle_esal_per_day,
    calculate_cgf,
    calculate_design_period_esal,
    calculate_esal_factor,
    calculate_total_esal_per_day,
    classify_traffic,
    esal_chart_years,
    esal_table_years,
    get_ldf_by_lane,
)
from app.services.traffic_esal import chart_bars_from_esal, compute_esal_from_workbook_data

_EXAMPLE_COUNTS = [297, 0, 0, 0, 0, 0, 0, 0, 562, 5950, 0, 8687, 0, 0, 0, 0, 0, 0]
_EXAMPLE_WORKBOOK = {"summary_total_row": [""] + _EXAMPLE_COUNTS}


class EsalCalculatorTests(unittest.TestCase):
    def test_get_ldf_by_lane(self) -> None:
        self.assertEqual(get_ldf_by_lane(1), 1.0)
        self.assertEqual(get_ldf_by_lane(2), 0.9)
        self.assertEqual(get_ldf_by_lane(3), 0.7)

    def test_calculate_cgf_zero_rate(self) -> None:
        self.assertEqual(calculate_cgf(0, 15), 15.0)

    def test_calculate_esal_factor_standard_load(self) -> None:
        self.assertEqual(calculate_esal_factor("SAST", 0, False), 1.0)

    def test_calculate_axle_esal_per_day(self) -> None:
        self.assertEqual(calculate_axle_esal_per_day(100, 1.0, 0.9), 90.0)

    def test_example_standard_load_case_lane_1(self) -> None:
        counts = {
            "steering_sast": 297,
            "tast": 562,
            "sadt": 0,
            "tadt": 5950,
            "trdt": 8687,
        }
        rows = build_axle_esal_rows(counts, use_tld=False, tld_loads_ready=True, lane_each_direction=1)
        total_per_day = calculate_total_esal_per_day(list(rows))
        self.assertEqual(total_per_day, 15496.0)

    def test_lane_2_applies_ldf_to_esal_per_day(self) -> None:
        result = compute_esal_from_workbook_data(
            _EXAMPLE_WORKBOOK,
            growth_rate=0.03,
            lane_count=2,
        )
        self.assertAlmostEqual(result.total_esal_per_day, 15496.0 * 0.9)

    def test_design_period_esal_multiplies_by_365(self) -> None:
        esal_per_day = 13946.4
        year_one = calculate_design_period_esal(esal_per_day, 3, 1)
        self.assertEqual(year_one, 5_090_436)

    def test_chart_and_table_use_design_period_esal(self) -> None:
        result = compute_esal_from_workbook_data(
            _EXAMPLE_WORKBOOK,
            growth_rate=0.03,
            lane_count=2,
            pavement_design_years=25,
        )
        chart_by_year = {period.years: period.total_esal for period in result.chart_periods}
        table_by_year = {period.years: period.total_esal for period in result.table_periods}

        for years in (15, 20, 25):
            self.assertEqual(chart_by_year[years], table_by_year[years])

        expected = {
            1: 5_090_436,
            5: 27_025_816,
            10: 58_356_144,
            15: 94_676_581,
            20: 136_781_922,
            25: 185_593_552,
        }
        for years, total_esal in expected.items():
            self.assertEqual(chart_by_year[years], total_esal, msg=f"Year {years}")

        self.assertEqual(len(table_by_year), 25)
        bars = chart_bars_from_esal(result)
        self.assertEqual(bars[0][0], "Year 1")
        self.assertEqual(int(bars[0][1]), expected[1])

    def test_esal_table_and_chart_years_follow_pavement_design_year(self) -> None:
        self.assertEqual(esal_table_years(25), tuple(range(1, 26)))
        self.assertEqual(esal_chart_years(25), (1, 5, 10, 15, 20, 25))
        self.assertEqual(esal_table_years(15), tuple(range(1, 16)))
        self.assertEqual(esal_chart_years(15), (1, 5, 10, 15))

    def test_description_periods_always_use_15_20_25(self) -> None:
        result = compute_esal_from_workbook_data(
            _EXAMPLE_WORKBOOK,
            growth_rate=0.03,
            lane_count=2,
            pavement_design_years=5,
        )
        description_years = [period.years for period in result.design_periods]
        self.assertEqual(description_years, [15, 20, 25])
        for period in result.design_periods:
            self.assertNotEqual(period.traffic_class, "—")
            self.assertGreater(period.total_esal, 0)


if __name__ == "__main__":
    unittest.main()
