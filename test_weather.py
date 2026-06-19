"""
tests/test_weather.py
Unit tests for the weather module. No real HTTP calls — uses local fixtures.
"""

import json
import os
import sys
import time
import unittest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.weather import (
    _build_url,
    _parse_response,
    get_weather_for_window,
    worst_conditions,
    _load_cache,
    _save_cache,
    WMO_DESCRIPTIONS,
)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "weather.json")


def load_fixture() -> dict:
    with open(FIXTURE_PATH) as f:
        return json.load(f)


class TestBuildUrl(unittest.TestCase):

    def test_url_contains_latitude(self):
        url = _build_url(29.76, -95.37, "imperial")
        self.assertIn("latitude=29.76", url)

    def test_url_contains_longitude(self):
        url = _build_url(29.76, -95.37, "imperial")
        self.assertIn("longitude=-95.37", url)

    def test_imperial_units(self):
        url = _build_url(29.76, -95.37, "imperial")
        self.assertIn("fahrenheit", url)
        self.assertIn("mph", url)

    def test_metric_units(self):
        url = _build_url(48.85, 2.35, "metric")
        self.assertIn("celsius", url)
        self.assertIn("kmh", url)

    def test_url_starts_with_base(self):
        url = _build_url(0, 0, "imperial")
        self.assertTrue(url.startswith("https://api.open-meteo.com"))


class TestParseResponse(unittest.TestCase):

    def setUp(self):
        """Build a minimal raw Open-Meteo-style response."""
        self.raw = {
            "hourly": {
                "time": ["2025-06-20T14:00", "2025-06-20T15:00"],
                "temperature_2m": [90.5, 88.0],
                "precipitation_probability": [75, 80],
                "weathercode": [63, 63],
                "windspeed_10m": [15.0, 18.0],
            }
        }

    def test_returns_dict_keyed_by_time(self):
        result = _parse_response(self.raw)
        self.assertIn("2025-06-20T14:00", result)
        self.assertIn("2025-06-20T15:00", result)

    def test_slot_has_expected_keys(self):
        result = _parse_response(self.raw)
        slot = result["2025-06-20T14:00"]
        for key in ("temp", "precip_pct", "wind", "code", "description"):
            self.assertIn(key, slot)

    def test_temperature_parsed_correctly(self):
        result = _parse_response(self.raw)
        self.assertAlmostEqual(result["2025-06-20T14:00"]["temp"], 90.5)

    def test_precip_probability_parsed(self):
        result = _parse_response(self.raw)
        self.assertEqual(result["2025-06-20T14:00"]["precip_pct"], 75)

    def test_wmo_description_resolved(self):
        result = _parse_response(self.raw)
        self.assertEqual(result["2025-06-20T14:00"]["description"], "Moderate rain")

    def test_empty_hourly_returns_empty_dict(self):
        result = _parse_response({"hourly": {}})
        self.assertEqual(result, {})


class TestGetWeatherForWindow(unittest.TestCase):

    def setUp(self):
        self.weather = load_fixture()

    def test_returns_slots_in_window(self):
        slots = get_weather_for_window(self.weather, "2025-06-20", "14:00", "15:30")
        times = [s["time"] for s in slots]
        self.assertIn("2025-06-20T14:00", times)
        self.assertIn("2025-06-20T15:00", times)

    def test_excludes_slots_outside_window(self):
        slots = get_weather_for_window(self.weather, "2025-06-20", "14:00", "15:30")
        times = [s["time"] for s in slots]
        self.assertNotIn("2025-06-20T09:00", times)
        self.assertNotIn("2025-06-20T17:00", times)

    def test_returns_empty_for_no_data(self):
        slots = get_weather_for_window({}, "2025-06-20", "14:00", "15:00")
        self.assertEqual(slots, [])

    def test_returns_empty_for_none(self):
        slots = get_weather_for_window(None, "2025-06-20", "14:00", "15:00")
        self.assertEqual(slots, [])

    def test_single_hour_event(self):
        slots = get_weather_for_window(self.weather, "2025-06-20", "07:00", "08:00")
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]["time"], "2025-06-20T07:00")


class TestWorstConditions(unittest.TestCase):

    def test_picks_highest_precip(self):
        slots = [
            {"precip_pct": 20, "wind": 5, "time": "T1"},
            {"precip_pct": 80, "wind": 5, "time": "T2"},
            {"precip_pct": 40, "wind": 5, "time": "T3"},
        ]
        worst = worst_conditions(slots)
        self.assertEqual(worst["time"], "T2")

    def test_breaks_tie_by_wind(self):
        slots = [
            {"precip_pct": 70, "wind": 10, "time": "T1"},
            {"precip_pct": 70, "wind": 35, "time": "T2"},
        ]
        worst = worst_conditions(slots)
        self.assertEqual(worst["time"], "T2")

    def test_returns_none_for_empty(self):
        self.assertIsNone(worst_conditions([]))

    def test_returns_single_item(self):
        slots = [{"precip_pct": 50, "wind": 10, "time": "T1"}]
        self.assertEqual(worst_conditions(slots)["time"], "T1")


class TestCache(unittest.TestCase):

    def setUp(self):
        self.cache_path = "/tmp/test_weather_cache.json"
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)

    def tearDown(self):
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)

    def test_save_then_load_returns_data(self):
        data = {"2025-06-20T14:00": {"temp": 90}}
        _save_cache(self.cache_path, data)
        loaded = _load_cache(self.cache_path, ttl_minutes=60)
        self.assertEqual(loaded, data)

    def test_expired_cache_returns_none(self):
        data = {"key": "val"}
        _save_cache(self.cache_path, data)
        # Manually age the cache
        with open(self.cache_path) as f:
            cache = json.load(f)
        cache["_saved_at"] = time.time() - 7200  # 2 hours ago
        with open(self.cache_path, "w") as f:
            json.dump(cache, f)
        result = _load_cache(self.cache_path, ttl_minutes=60)
        self.assertIsNone(result)

    def test_missing_cache_returns_none(self):
        result = _load_cache("/tmp/nonexistent_cache.json", 60)
        self.assertIsNone(result)

    def test_corrupt_cache_returns_none(self):
        with open(self.cache_path, "w") as f:
            f.write("not valid json{{{{")
        result = _load_cache(self.cache_path, 60)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
