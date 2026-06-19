#!/usr/bin/env python3
"""
assistant.py — Weather-Aware Personal Assistant
Entry point. Run: python assistant.py [--days N] [--date YYYY-MM-DD]
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta

# Allow running from the project root without installing
sys.path.insert(0, os.path.dirname(__file__))

from src.weather import fetch_weather
from src.calendar_parser import load_calendar, filter_events_by_range, filter_events_by_date
from src.advice import build_day_report
from src.formatter import (
    print_header,
    print_day_section,
    print_event_advice,
    print_no_events,
    print_footer,
)

DEFAULT_CONFIG = {
    "latitude": 29.7604,
    "longitude": -95.3698,
    "location_name": "Houston, TX",
    "units": "imperial",
    "cache_ttl_minutes": 60,
    "thresholds": {
        "rain_pct": 50,
        "temp_high_f": 95,
        "temp_low_f": 32,
        "wind_mph": 30,
    },
}


def load_config(path: str = "config.json") -> dict:
    """Load config.json, falling back to defaults for missing keys."""
    if not os.path.exists(path):
        return DEFAULT_CONFIG.copy()
    try:
        with open(path, "r") as f:
            user_cfg = json.load(f)
        merged = {**DEFAULT_CONFIG, **user_cfg}
        merged["thresholds"] = {
            **DEFAULT_CONFIG["thresholds"],
            **user_cfg.get("thresholds", {}),
        }
        return merged
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  Could not read config.json ({e}). Using defaults.")
        return DEFAULT_CONFIG.copy()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Weather-Aware Personal Assistant — combines weather + your calendar.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python assistant.py                  # Today + tomorrow
  python assistant.py --days 7         # Full week
  python assistant.py --date 2025-06-22  # Specific day
  python assistant.py --no-cache       # Force fresh weather fetch
        """,
    )
    parser.add_argument(
        "--days", type=int, default=2,
        help="Number of days to show (default: 2)"
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Show a specific date (YYYY-MM-DD); overrides --days"
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Force a fresh weather fetch, ignoring the cache"
    )
    parser.add_argument(
        "--calendar", type=str, default="calendar.json",
        help="Path to calendar JSON file (default: calendar.json)"
    )
    parser.add_argument(
        "--config", type=str, default="config.json",
        help="Path to config JSON file (default: config.json)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)

    # Determine date range
    today = date.today()
    if args.date:
        try:
            target = date.fromisoformat(args.date)
            date_range = [target]
        except ValueError:
            print(f"❌  Invalid date format '{args.date}'. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        date_range = [today + timedelta(days=i) for i in range(args.days)]

    # Fetch weather
    cache_path = "weather_cache.json"
    if args.no_cache and os.path.exists(cache_path):
        os.remove(cache_path)

    weather_data = fetch_weather(
        lat=cfg["latitude"],
        lon=cfg["longitude"],
        units=cfg["units"],
        cache_path=cache_path,
        cache_ttl_minutes=cfg["cache_ttl_minutes"],
    )

    # Load calendar
    events = load_calendar(args.calendar)

    # Print output
    print_header(cfg["location_name"])

    for target_date in date_range:
        date_str = target_date.isoformat()
        day_events = filter_events_by_date(events, date_str)
        print_day_section(date_str)

        if not day_events:
            print_no_events(date_str)
            continue

        advices = build_day_report(
            date_str,
            day_events,
            weather_data,
            units=cfg["units"],
            thresholds=cfg["thresholds"],
        )
        for adv in advices:
            print_event_advice(adv)

    print_footer(days_shown=len(date_range))


if __name__ == "__main__":
    main()
