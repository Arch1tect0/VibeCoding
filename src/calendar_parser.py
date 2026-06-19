"""
src/calendar_parser.py
Loads and validates events from calendar.json.
"""

import json
import os
from datetime import date, datetime
from typing import Optional


REQUIRED_FIELDS = {"title", "date", "start_time", "end_time"}


def load_calendar(path: str = "calendar.json") -> list[dict]:
    """
    Load and validate calendar events from a JSON file.

    Skips malformed entries with a warning rather than crashing.
    Returns a list of valid event dicts sorted by date + start_time.
    """
    if not os.path.exists(path):
        print(f"⚠️  Calendar file not found: {path}")
        print("    Create a calendar.json file to get event-based advice.")
        return []

    try:
        with open(path, "r") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌  calendar.json is not valid JSON: {e}")
        return []

    if not isinstance(raw, list):
        print("❌  calendar.json must be a JSON array of event objects.")
        return []

    valid_events = []
    for i, entry in enumerate(raw):
        event = _validate_event(entry, index=i)
        if event:
            valid_events.append(event)

    valid_events.sort(key=lambda e: (e["date"], e["start_time"]))
    return valid_events


def _validate_event(entry: dict, index: int) -> Optional[dict]:
    """
    Validate a single calendar entry.
    Returns the cleaned event dict, or None if invalid.
    """
    if not isinstance(entry, dict):
        print(f"⚠️  Entry #{index} is not an object — skipping.")
        return None

    missing = REQUIRED_FIELDS - entry.keys()
    if missing:
        title = entry.get("title", f"entry #{index}")
        print(f"⚠️  Event '{title}' missing fields {missing} — skipping.")
        return None

    # Validate date format
    try:
        datetime.strptime(entry["date"], "%Y-%m-%d")
    except ValueError:
        print(f"⚠️  Event '{entry.get('title')}' has invalid date '{entry['date']}' — skipping.")
        return None

    # Validate time formats
    for field in ("start_time", "end_time"):
        try:
            datetime.strptime(entry[field], "%H:%M")
        except ValueError:
            print(f"⚠️  Event '{entry.get('title')}' has invalid {field} '{entry[field]}' — skipping.")
            return None

    return {
        "title": str(entry["title"]).strip(),
        "date": entry["date"],
        "start_time": entry["start_time"],
        "end_time": entry["end_time"],
        "location": str(entry.get("location", "")).strip(),
    }


def filter_events_by_date(events: list[dict], target_date: str) -> list[dict]:
    """Return only events matching the given 'YYYY-MM-DD' date string."""
    return [e for e in events if e["date"] == target_date]


def filter_events_by_range(events: list[dict], start: date, end: date) -> list[dict]:
    """Return events whose date falls within [start, end] inclusive."""
    result = []
    for e in events:
        try:
            event_date = date.fromisoformat(e["date"])
        except ValueError:
            continue
        if start <= event_date <= end:
            result.append(e)
    return result
