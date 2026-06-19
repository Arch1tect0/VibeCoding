# Product Requirements Document
## Weather-Aware Personal Assistant (CLI)

---

### Overview

A command-line tool that combines real-time weather data with a local calendar file to deliver context-aware daily advice. Instead of checking weather and your schedule separately, the assistant synthesizes both into plain-English recommendations.

**Example output:**
```
☔ Tomorrow (Tue Jun 20): Rain expected 2–6pm (80% chance).
   → Your "Team Standup" at 2:00pm overlaps with heavy rain. Bring an umbrella.
   → "Lunch with Sarah" at 12:30pm looks fine — partly cloudy, 74°F.
```

---

### Problem Statement

People check weather apps and calendars independently, then manually reason about conflicts ("will it rain during my commute?"). This is low-value cognitive work a program can do instantly.

---

### Goals

| # | Goal |
|---|------|
| 1 | Fetch accurate weather for the user's location (today + next 7 days) |
| 2 | Parse a structured local calendar file (`calendar.json`) |
| 3 | Match calendar events to weather windows and generate advice |
| 4 | Run entirely from the terminal with zero GUI dependencies |
| 5 | Work offline for calendar; degrade gracefully if weather API is down |

---

### Non-Goals

- No GUI or web interface
- No cloud sync or OAuth (calendar is a local JSON file)
- No push notifications
- No support for recurring events (out of scope v1)

---

### User Stories

**US-1 — Morning briefing**
> As a user, I run `python assistant.py` each morning and get a summary of today's and tomorrow's events with weather context.

**US-2 — Week ahead**
> As a user, I run `python assistant.py --days 7` to see the full week.

**US-3 — Specific day**
> As a user, I run `python assistant.py --date 2025-06-22` to focus on one day.

**US-4 — Rain warning**
> As a user, I get an explicit warning whenever precipitation probability exceeds 50% during a scheduled event.

**US-5 — Extreme weather**
> As a user, I get a high-priority alert for temperatures above 95°F / below 20°F or wind > 40mph during any event.

---

### Functional Requirements

#### Weather Module
- Source: [Open-Meteo](https://open-meteo.com/) (free, no API key required)
- Data fetched: hourly temperature, precipitation probability, wind speed, weather code
- Location: latitude/longitude from `config.json` (defaults to Houston, TX)
- Cache: responses cached to `weather_cache.json` for 1 hour to avoid redundant calls

#### Calendar Module
- Input: `calendar.json` in the project root
- Schema:
```json
[
  {
    "title": "Team Standup",
    "date": "2025-06-20",
    "start_time": "14:00",
    "end_time":   "14:30",
    "location": "Office"
  }
]
```
- Validation: malformed entries are skipped with a warning, not fatal errors

#### Advice Engine
- For each event, look up weather for the event's time window
- Trigger advice for:
  - Rain/snow probability ≥ 50%
  - Temperature > 95°F or < 32°F
  - Wind speed > 30 mph
  - Thunderstorm weather codes (WMO 95–99)
- Always show temperature + conditions even when no warnings apply

#### CLI Interface
```
python assistant.py [--days N] [--date YYYY-MM-DD] [--location "City, ST"] [--no-cache]
```

---

### Success Metrics

| Metric | Target |
|--------|--------|
| Cold start to output | < 3 seconds on typical broadband |
| Calendar parse accuracy | 100% of valid events parsed |
| Weather match accuracy | Event matched to correct hourly slot |
| Test coverage | ≥ 80% of logic covered by automated tests |
| Graceful degradation | App does not crash when API is unreachable |

---

### Out of Scope (v2 ideas)
- Google Calendar / iCal integration
- SMS/email delivery
- Historical weather lookup
- Multiple location support per event
