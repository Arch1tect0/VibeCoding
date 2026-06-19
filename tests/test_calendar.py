"""
tests/test_calendar.py
Unit tests for the calendar_parser module.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.calendar_parser import (
    load_calendar,
    _validate_event,
    filter_events_by_date,
    filter_events_by_range,
)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "calendar.json")


def write_tmp_calendar(data: list) -> str:
    """Write a list of events to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return f.name


class TestLoadCalendar(unittest.TestCase):

    def test_loads_fixture_successfully(self):
        events = load_calendar(FIXTURE_PATH)
        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)

    def test_all_events_have_required_fields(self):
        events = load_calendar(FIXTURE_PATH)
        for e in events:
            for field in ("title", "date", "start_time", "end_time"):
                self.assertIn(field, e, f"Missing '{field}' in {e}")

    def test_events_sorted_by_date_then_time(self):
        events = load_calendar(FIXTURE_PATH)
        keys = [(e["date"], e["start_time"]) for e in events]
        self.assertEqual(keys, sorted(keys))

    def test_missing_file_returns_empty_list(self):
        events = load_calendar("/tmp/no_such_file_xyz.json")
        self.assertEqual(events, [])

    def test_invalid_json_returns_empty_list(self):
        path = write_tmp_calendar([])
        with open(path, "w") as f:
            f.write("{not json}")
        events = load_calendar(path)
        self.assertEqual(events, [])
        os.unlink(path)

    def test_non_array_json_returns_empty_list(self):
        path = write_tmp_calendar([])
        with open(path, "w") as f:
            json.dump({"events": []}, f)
        events = load_calendar(path)
        self.assertEqual(events, [])
        os.unlink(path)

    def test_skips_invalid_entries_keeps_valid(self):
        data = [
            {"title": "Good Event", "date": "2025-06-20", "start_time": "09:00", "end_time": "10:00"},
            {"title": "Bad — no date", "start_time": "10:00", "end_time": "11:00"},
        ]
        path = write_tmp_calendar(data)
        events = load_calendar(path)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Good Event")
        os.unlink(path)


class TestValidateEvent(unittest.TestCase):

    def _valid(self, **overrides):
        base = {
            "title": "Test", "date": "2025-06-20",
            "start_time": "09:00", "end_time": "10:00",
        }
        base.update(overrides)
        return base

    def test_valid_event_passes(self):
        result = _validate_event(self._valid(), index=0)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Test")

    def test_missing_title_fails(self):
        e = self._valid()
        del e["title"]
        self.assertIsNone(_validate_event(e, 0))

    def test_missing_date_fails(self):
        e = self._valid()
        del e["date"]
        self.assertIsNone(_validate_event(e, 0))

    def test_invalid_date_format_fails(self):
        self.assertIsNone(_validate_event(self._valid(date="20-06-2025"), 0))

    def test_invalid_start_time_fails(self):
        self.assertIsNone(_validate_event(self._valid(start_time="9am"), 0))

    def test_invalid_end_time_fails(self):
        self.assertIsNone(_validate_event(self._valid(end_time="25:00"), 0))

    def test_optional_location_defaults_to_empty(self):
        result = _validate_event(self._valid(), 0)
        self.assertEqual(result["location"], "")

    def test_location_preserved_when_present(self):
        result = _validate_event(self._valid(location="Office"), 0)
        self.assertEqual(result["location"], "Office")

    def test_non_dict_entry_returns_none(self):
        self.assertIsNone(_validate_event("not a dict", 0))


class TestFilterEventsByDate(unittest.TestCase):

    def setUp(self):
        self.events = [
            {"title": "A", "date": "2025-06-20", "start_time": "09:00", "end_time": "10:00", "location": ""},
            {"title": "B", "date": "2025-06-21", "start_time": "10:00", "end_time": "11:00", "location": ""},
            {"title": "C", "date": "2025-06-20", "start_time": "14:00", "end_time": "15:00", "location": ""},
        ]

    def test_returns_matching_date(self):
        result = filter_events_by_date(self.events, "2025-06-20")
        titles = [e["title"] for e in result]
        self.assertIn("A", titles)
        self.assertIn("C", titles)

    def test_excludes_other_dates(self):
        result = filter_events_by_date(self.events, "2025-06-20")
        titles = [e["title"] for e in result]
        self.assertNotIn("B", titles)

    def test_empty_when_no_match(self):
        result = filter_events_by_date(self.events, "2025-12-31")
        self.assertEqual(result, [])


class TestFilterEventsByRange(unittest.TestCase):

    def setUp(self):
        self.events = [
            {"title": "A", "date": "2025-06-18", "start_time": "09:00", "end_time": "10:00", "location": ""},
            {"title": "B", "date": "2025-06-20", "start_time": "10:00", "end_time": "11:00", "location": ""},
            {"title": "C", "date": "2025-06-22", "start_time": "14:00", "end_time": "15:00", "location": ""},
            {"title": "D", "date": "2025-06-25", "start_time": "14:00", "end_time": "15:00", "location": ""},
        ]

    def test_includes_boundary_dates(self):
        result = filter_events_by_range(
            self.events, date(2025, 6, 20), date(2025, 6, 22)
        )
        titles = [e["title"] for e in result]
        self.assertIn("B", titles)
        self.assertIn("C", titles)

    def test_excludes_outside_dates(self):
        result = filter_events_by_range(
            self.events, date(2025, 6, 20), date(2025, 6, 22)
        )
        titles = [e["title"] for e in result]
        self.assertNotIn("A", titles)
        self.assertNotIn("D", titles)


if __name__ == "__main__":
    unittest.main()
