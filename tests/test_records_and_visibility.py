"""Regressions for record rounding and graphs.conf series visibility.

Run with WeeWX 5 and pytest installed: python -m pytest -q tests
"""
import io
import json
import sqlite3
import sys
from pathlib import Path

import configobj
import pytest
import weewx.units

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))
from user import belchertown


class SummaryDatabase:
    """Execute the production query against actual daily-summary rows."""

    def __init__(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(
            "CREATE TABLE archive_day_outTemp "
            "(dateTime INTEGER PRIMARY KEY, min REAL, max REAL, count INTEGER)"
        )

    def add(self, *rows):
        self.connection.executemany(
            "INSERT INTO archive_day_outTemp VALUES (?, ?, ?, ?)", rows
        )

    def getSql(self, sql, parameters):
        # WeeWX uses question-mark placeholders and adapts them for MySQL.
        return self.connection.execute(sql, parameters).fetchone()


@pytest.fixture
def summaries():
    database = SummaryDatabase()
    yield database
    database.connection.close()


@pytest.mark.parametrize("maximum, expected", [(False, 300), (True, 100)])
def test_rank_unrounded_ranges_when_display_values_tie(summaries, maximum, expected):
    summaries.add(
        (100, 3.72222222222222, 4.33333333333333, 288),
        (300, 1.888888888888888, 2.4444444444444438, 288),
    )
    record = belchertown._get_daily_temperature_range(
        summaries, None, 400, 144, maximum=maximum
    )
    assert record[0] == expected
    assert record[1] == pytest.approx(record[3] - record[2])
    assert record[2] != round(record[2], 1)


@pytest.mark.parametrize("maximum", [False, True])
def test_year_and_all_time_agree_when_year_has_the_record(summaries, maximum):
    current_high = 10.555555555555556 if maximum else 0.5555555555555556
    old_high = 10.51111111111111 if maximum else 0.6111111111111112
    summaries.add((100, 0, old_high, 288), (300, 0, current_high, 288))
    year = belchertown._get_daily_temperature_range(
        summaries, 200, 400, 144, maximum=maximum
    )
    all_time = belchertown._get_daily_temperature_range(
        summaries, None, 400, 144, maximum=maximum
    )
    assert year == all_time
    assert year[0] == 300


@pytest.mark.parametrize("maximum", [False, True])
def test_complete_day_and_time_filters_are_preserved(summaries, maximum):
    misleading = 1000 if maximum else 0
    summaries.add(
        (100, 0, misleading, 288),  # Before the requested year.
        (200, 0, 3, 144),          # At the start and completeness boundaries.
        (250, 0, misleading, 143), # Incomplete day.
        (270, None, 5, 288),
        (280, 0, None, 288),
        (400, 0, misleading, 288), # Current day must be excluded.
    )
    result = belchertown._get_daily_temperature_range(
        summaries, 200, 400, 144, maximum=maximum
    )
    assert result == (200, 3, 0, 3)


@pytest.mark.parametrize("maximum", [False, True])
def test_true_ties_choose_the_earliest_day(summaries, maximum):
    summaries.add((300, 1, 2, 288), (100, 3, 4, 288))
    assert belchertown._get_daily_temperature_range(
        summaries, None, 400, 144, maximum=maximum
    )[0] == 100


@pytest.mark.parametrize("maximum", [False, True])
def test_tenths_based_ranges_ignore_floating_point_noise(summaries, maximum):
    # Real Fahrenheit readings: both days have a 2.9-degree range.
    older, newer = 1577750400, 1758672000  # 2019-12-31 and 2025-09-24 UTC.
    summaries.add((newer, 63.6, 66.5, 288), (older, 30.7, 33.6, 288))
    assert 33.6 - 30.7 != 66.5 - 63.6
    result = belchertown._get_daily_temperature_range(
        summaries, None, newer + 86400, 144, maximum=maximum
    )
    assert result[0] == older
    assert result[1] == pytest.approx(2.9)


def test_no_eligible_record(summaries):
    assert belchertown._get_daily_temperature_range(
        summaries, None, 400, 144
    ) is None


@pytest.mark.parametrize("source_unit", ["degree_C", "degree_F"])
@pytest.mark.parametrize("target_unit, expected", [("degree_C", "0.6"), ("degree_F", "1.0")])
def test_range_is_converted_and_subtracted_before_display_rounding(
    source_unit, target_unit, expected
):
    low, high = 1.888888888888888, 2.4444444444444438
    if source_unit == "degree_F":
        low, high = low * 1.8 + 32, high * 1.8 + 32
    converter = weewx.units.Converter({"group_temperature": target_unit})
    result = belchertown._temperature_range_total(
        (high, source_unit, "group_temperature"),
        (low, source_unit, "group_temperature"), converter, "%.1f"
    )
    assert result == expected


def test_range_uses_the_configured_precision():
    converter = weewx.units.Converter({"group_temperature": "degree_C"})
    assert belchertown._temperature_range_total(
        (2.4444444444444438, "degree_C", "group_temperature"),
        (1.888888888888888, "degree_C", "group_temperature"), converter, "%.2f"
    ) == "0.56"


@pytest.mark.parametrize("value, expected", [
    ("false", False), ("False", False), ("FALSE", False),
    ("true", True), ("True", True), ("TRUE", True),
    ("0", False), ("1", True), (False, False), (True, True),
    (0, False), (1, True),
])
def test_series_visible_is_a_json_boolean(value, expected):
    generator = object.__new__(belchertown.HighchartsJsonGenerator)
    options = {"visible": value}
    converted = generator.highcharts_series_options_to_float(options)
    assert json.loads(json.dumps(converted))["visible"] is expected
    # A second normalization pass must not turn booleans into numbers.
    assert generator.highcharts_series_options_to_float(converted)["visible"] is expected


def test_series_visibility_from_graphs_conf_and_nested_options():
    config = configobj.ConfigObj(io.StringIO(
        "[day]\n[[chart1]]\n[[[windchill]]]\nvisible = false\n"
        "lineWidth = 2\nname = false\n[[[[custom]]]]\nvisible = true\n"
    ))
    options = config["day"]["chart1"]["windchill"]
    generator = object.__new__(belchertown.HighchartsJsonGenerator)
    result = json.loads(json.dumps(generator.highcharts_series_options_to_float(options)))
    assert result["visible"] is False
    assert result["custom"]["visible"] is True
    assert result["lineWidth"] == 2.0
    assert result["name"] == "false"


def test_series_without_visibility_keeps_the_library_default():
    generator = object.__new__(belchertown.HighchartsJsonGenerator)
    result = generator.highcharts_series_options_to_float({"name": "Temperature"})
    assert "visible" not in result
