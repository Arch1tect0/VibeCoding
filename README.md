# 🌤 Weather-Aware Personal Assistant

> A zero-dependency CLI that reads your calendar and live weather, then tells you what you actually need to know.

---

## Quick Start

```bash
# Clone or download the project
cd weather-assistant

# Run with defaults (today + tomorrow, Houston TX)
python assistant.py

# Show the next 7 days
python assistant.py --days 7

# Focus on one day
python assistant.py --date 2025-06-22

# Force a fresh weather fetch
python assistant.py --no-cache
```

**Requirements:** Python 3.10+ and an internet connection. No `pip install` needed.

---

## Setup

**1. Edit your calendar** (`calendar.json`):

```json
[
  {
    "title": "Team Standup",
    "date": "2025-06-20",
    "start_time": "09:00",
    "end_time": "09:30",
    "location": "Office"
  },
  {
    "title": "Rooftop Lunch",
    "date": "2025-06-20",
    "start_time": "12:30",
    "end_time": "13:30",
    "location": "The Capital Grille"
  }
]
```

**2. Edit your location** (`config.json`):

```json
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "location_name": "New York, NY",
  "units": "imperial"
}
```

**3. Run it.**

---

## Sample Output

```
╔══════════════════════════════════════════╗
  🌤  Weather-Aware Assistant — Houston, TX
  📅  Fri Jun 20, 2025 08:00 AM
╚══════════════════════════════════════════╝

  ── Friday, June 20 ──

    Morning Run  07:00–08:00  📍 Memorial Park
       ✅ Partly cloudy, 78°F — looks good!

    Team Standup  09:00–09:30  📍 Office
       ✅ Mainly clear, 82°F — looks good!

    Client Presentation  14:00–15:30  📍 Conference Room B
       ☔ 75% chance of rain (Moderate rain, 90°F)
       🥵 High of 90°F — stay hydrated, limit outdoor exposure.

  Showing 2 day(s). Run with --help for options.
```

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

All 66 tests should pass. Tests use local fixtures only — no network calls.

---

## Project Structure

```
weather-assistant/
├── assistant.py          # CLI entry point
├── config.json           # Your location + preferences
├── calendar.json         # Your events
├── src/
│   ├── weather.py        # Open-Meteo fetch + cache
│   ├── calendar_parser.py# Load + validate events
│   ├── advice.py         # Match events to weather
│   └── formatter.py      # Terminal output
├── tests/
│   ├── test_weather.py
│   ├── test_calendar.py
│   ├── test_advice.py
│   └── fixtures/         # Static JSON for tests
├── specs/PRD.md
└── docs/rules.md
```

---

## Configuration Reference

| Key | Default | Description |
|-----|---------|-------------|
| `latitude` | 29.7604 | Your latitude |
| `longitude` | -95.3698 | Your longitude |
| `location_name` | "Houston, TX" | Display name only |
| `units` | "imperial" | "imperial" or "metric" |
| `cache_ttl_minutes` | 60 | How long to cache weather |
| `thresholds.rain_pct` | 50 | % chance to trigger rain warning |
| `thresholds.temp_high_f` | 95 | °F above which to warn |
| `thresholds.temp_low_f` | 32 | °F below which to warn |
| `thresholds.wind_mph` | 30 | MPH above which to warn |

---

## Vibe Report — Reflection

### What I Was Going For

The core motivation was friction. Every morning I'd check my weather app, then my calendar, then mentally cross-reference them. "It rains at 3pm... do I have anything at 3pm?" That 10-second mental exercise is 10 seconds too many, and the right tool should just *tell* me.

### What Worked Well

The **modular design** paid off immediately. Splitting weather fetch, calendar parsing, and advice generation into three separate modules meant each was testable in isolation with zero mocking gymnastics. When I realized I wanted to support both imperial and metric units, I only had to change two places.

The **Open-Meteo API** was a great fit. Free, no API key, returns clean JSON with WMO weather codes. The WMO code system is a hidden gem — 100+ precisely defined weather states that map perfectly to user-readable advice.

**Caching** turned out more important than expected. Weather APIs have rate limits, and polling on every run would be antisocial. A 60-minute TTL is the right balance between freshness and courtesy.

### What Was Harder Than Expected

**Time window matching.** My first instinct was to find the exact slot matching an event's start time. But a 2-hour meeting might start in clear weather and end in a thunderstorm — users need the *worst* case across the entire window. The `worst_conditions()` function handles this but took iteration to get right.

**Terminal formatting without dependencies.** I wanted color output but didn't want to require `colorama` on Windows. The solution — checking `sys.stdout.isatty()` and falling back to plain text — works but feels slightly fragile. A v2 might accept `--no-color` explicitly.

### What I'd Do Differently

- **iCal support.** The `calendar.json` format is convenient but not realistic. Real users have Google Calendar or Outlook. An `--ical` flag would make this genuinely useful day-to-day.
- **Better event-to-weather interpolation.** Currently I only match whole-hour slots. An event from 2:15–3:45 might miss the 2:00 slot entirely if weather data lands on the hour.
- **Location per event.** "Dentist appointment (indoor)" shouldn't show a rain warning. Events could carry an `outdoor: true` flag to suppress indoor-irrelevant alerts.

### What I Learned

Writing a zero-dependency CLI forces discipline. Every convenience method you'd normally `pip install` has to be justified or hand-rolled. The result is a program that runs literally anywhere Python 3.10 exists, which is a real feature — not just a constraint.

The tests proved their worth when I refactored the threshold system. Having 66 tests meant I could restructure `_check_warnings()` and immediately know nothing broke.

---

*Built with Python 3.10 · Weather data from [Open-Meteo](https://open-meteo.com/) · Zero dependencies*
