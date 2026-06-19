"""
tests/test_advice.py
Unit tests for the advice engine.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.advice import generate_advice, _check_warnings, _build_summary, build_day_report

WEATHER_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "weather.json")
CALENDAR_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "calendar.json")


def load_weather() -> dict:
    with open(WEATHER_FIXTURE) as f:
        return json.load(f)


def load_calendar() -> list:
    with open(CALENDAR_FIXTURE) as f:
        return json.load(f)


def make_event(
    title="Test", date="2025-06-20", start="14:00", end="15:30", location=""
) -> dict:
    return {
        "title": title, "date": date,
        "start_time": start, "end_time": end, "location": location,
    }


DEFAULT_THRESHOLDS = {
    "rain_pct": 50, "temp_high_f": 95, "temp_low_f": 32, "wind_mph": 30,
}


class TestCheckWarnings(unittest.TestCase):

    def test_rain_warning_above_threshold(self):
        slot = {"code": 61, "precip_pct": 75, "temp": 80, "wind": 10}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertTrue(any("rain" in w.lower() or "☔" in w for w in warnings))

    def test_no_rain_warning_below_threshold(self):
        slot = {"code": 1, "precip_pct": 30, "temp": 80, "wind": 10}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertFalse(any("rain" in w.lower() or "☔" in w for w in warnings))

    def test_thunderstorm_warning(self):
        slot = {"code": 95, "precip_pct": 60, "temp": 80, "wind": 20}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertTrue(any("⛈️" in w or "thunder" in w.lower() for w in warnings))

    def test_snow_warning(self):
        slot = {"code": 73, "precip_pct": 80, "temp": 28, "wind": 10}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertTrue(any("🌨️" in w or "snow" in w.lower() for w in warnings))

    def test_high_temp_warning(self):
        slot = {"code": 0, "precip_pct": 5, "temp": 98.0, "wind": 5}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertTrue(any("🥵" in w for w in warnings))

    def test_low_temp_warning(self):
        slot = {"code": 0, "precip_pct": 5, "temp": 28.0, "wind": 5}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertTrue(any("🥶" in w for w in warnings))

    def test_wind_warning(self):
        slot = {"code": 0, "precip_pct": 5, "temp": 70, "wind": 40}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertTrue(any("💨" in w for w in warnings))

    def test_no_warnings_for_pleasant_weather(self):
        slot = {"code": 1, "precip_pct": 10, "temp": 75, "wind": 8}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertEqual(warnings, [])

    def test_multiple_warnings_possible(self):
        # Thunderstorm + extreme heat
        slot = {"code": 95, "precip_pct": 70, "temp": 100, "wind": 50}
        warnings = _check_warnings(slot, DEFAULT_THRESHOLDS, "°F", "mph")
        self.assertGreater(len(warnings), 1)


class TestGenerateAdvice(unittest.TestCase):

    def setUp(self):
        self.weather = load_weather()

    def test_rainy_event_has_warning(self):
        event = make_event(start="14:00", end="15:30")
        result = generate_advice(event, self.weather)
        self.assertTrue(len(result["warnings"]) > 0)
        self.assertIn("rain", result["summary"].lower() + " ".join(result["warnings"]).lower())

    def test_clear_morning_no_warning(self):
        event = make_event(start="07:00", end="08:00")
        result = generate_advice(event, self.weather)
        self.assertEqual(result["warnings"], [])
        self.assertIn("✅", result["summary"])

    def test_thunderstorm_event_warning(self):
        event = make_event(start="17:00", end="18:00")
        result = generate_advice(event, self.weather)
        combined = result["summary"] + " ".join(result["warnings"])
        self.assertTrue("⛈️" in combined or "thunder" in combined.lower())

    def test_high_temp_warning(self):
        event = make_event(start="18:00", end="19:00")
        result = generate_advice(event, self.weather)
        combined = " ".join(result["warnings"])
        self.assertTrue("🥵" in combined)

    def test_freezing_temp_warning(self):
        event = make_event(date="2025-06-22", start="09:00", end="10:00")
        result = generate_advice(event, self.weather)
        combined = " ".join(result["warnings"])
        self.assertTrue("🥶" in combined)

    def test_no_weather_data_returns_gracefully(self):
        event = make_event()
        result = generate_advice(event, None)
        self.assertIsNone(result["conditions"])
        self.assertEqual(result["warnings"], [])
        self.assertIn("No weather data", result["summary"])

    def test_event_out_of_weather_range_returns_gracefully(self):
        event = make_event(date="2030-01-01", start="09:00", end="10:00")
        result = generate_advice(event, self.weather)
        self.assertIsNone(result["conditions"])

    def test_result_contains_event(self):
        event = make_event(title="My Meeting")
        result = generate_advice(event, self.weather)
        self.assertEqual(result["event"]["title"], "My Meeting")


class TestBuildDayReport(unittest.TestCase):

    def setUp(self):
        self.weather = load_weather()

    def test_returns_one_advice_per_event(self):
        events = [
            make_event(title="A", start="07:00", end="08:00"),
            make_event(title="B", start="14:00", end="15:30"),
        ]
        results = build_day_report("2025-06-20", events, self.weather)
        self.assertEqual(len(results), 2)

    def test_empty_events_returns_empty_list(self):
        results = build_day_report("2025-06-20", [], self.weather)
        self.assertEqual(results, [])

    def test_no_weather_still_returns_results(self):
        events = [make_event()]
        results = build_day_report("2025-06-20", events, None)
        self.assertEqual(len(results), 1)
        self.assertIn("No weather data", results[0]["summary"])

    def test_custom_threshold_changes_warnings(self):
        # Lower the rain threshold to 5% — even "mostly clear" events should warn
        events = [make_event(start="07:00", end="08:00")]
        strict_thresholds = {**DEFAULT_THRESHOLDS, "rain_pct": 5}
        results = build_day_report("2025-06-20", events, self.weather, thresholds=strict_thresholds)
        # Morning run has 10% precip, which exceeds threshold of 5%
        combined = " ".join(results[0]["warnings"])
        self.assertTrue("☔" in combined or "rain" in combined.lower())


if __name__ == "__main__":
    unittest.main()
