# Rules & Tech Stack
## Weather-Aware Personal Assistant

---

### Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Language | Python 3.10+ | Standard library covers most needs; widely available |
| HTTP client | `urllib.request` (stdlib) | Zero dependencies for weather fetch |
| JSON | `json` (stdlib) | Calendar + cache files |
| Date/time | `datetime` (stdlib) | No arrow/pendulum needed for v1 |
| CLI args | `argparse` (stdlib) | Built-in, no Click/Typer overhead |
| Testing | `unittest` (stdlib) | No pytest required; keeps deps at zero |
| Weather API | [Open-Meteo](https://open-meteo.com/) | Free, no API key, returns JSON |

**Dependency policy: zero third-party packages.** The app must run with `python assistant.py` on any machine with Python 3.10+ and internet access — no `pip install` required.

---

### Project Structure

```
weather-assistant/
├── assistant.py          # Entry point / CLI
├── config.json           # User config (location, units)
├── calendar.json         # User's calendar events
├── weather_cache.json    # Auto-generated; gitignored
├── src/
│   ├── weather.py        # Fetch + parse Open-Meteo data
│   ├── calendar_parser.py# Load + validate calendar.json
│   ├── advice.py         # Match events to weather, generate text
│   └── formatter.py      # Terminal output (colors, layout)
├── tests/
│   ├── test_weather.py
│   ├── test_calendar.py
│   ├── test_advice.py
│   └── fixtures/         # Static JSON fixtures for tests
├── specs/PRD.md
├── docs/rules.md         # ← this file
└── README.md
```

---

### Coding Style

#### General
- Follow **PEP 8** strictly (4-space indent, 79-char line limit)
- All public functions have **docstrings** (one-line minimum)
- **Type hints** on all function signatures (Python 3.10+ style)
- No global mutable state — pass data explicitly between modules

#### Naming
- `snake_case` for functions and variables
- `PascalCase` for classes (used sparingly; prefer plain functions)
- Constants in `UPPER_SNAKE_CASE` at module top

#### Error handling
- Never use bare `except:`
- Catch the most specific exception possible
- API failures → print warning, return `None`, continue
- Calendar parse errors → skip entry, print warning with line number
- Never `sys.exit()` inside modules — only in `assistant.py`

#### No magic numbers
```python
# ❌ Bad
if precip > 50:

# ✅ Good
RAIN_WARNING_THRESHOLD_PCT = 50
if precip > RAIN_WARNING_THRESHOLD_PCT:
```

---

### Constraints

1. **No API key required.** Open-Meteo is used specifically because it needs no authentication.
2. **Single-file entry point.** `python assistant.py` is the only command a user needs.
3. **Config over code.** Location, units (metric/imperial), and thresholds live in `config.json`, not hardcoded.
4. **Cache courtesy.** Weather API responses are cached for 60 minutes. Do not hammer free APIs.
5. **No network in tests.** All tests use local fixtures — no real HTTP calls.
6. **Fail loudly for dev, softly for users.** Raise real exceptions during tests; show friendly messages at runtime.
7. **Cross-platform.** Must work on macOS, Linux, and Windows. No `os.system()` calls with shell-specific syntax.

---

### Config Schema (`config.json`)

```json
{
  "latitude": 29.7604,
  "longitude": -95.3698,
  "location_name": "Houston, TX",
  "units": "imperial",
  "cache_ttl_minutes": 60,
  "thresholds": {
    "rain_pct": 50,
    "temp_high_f": 95,
    "temp_low_f": 32,
    "wind_mph": 30
  }
}
```

---

### Git Hygiene

- `weather_cache.json` is in `.gitignore`
- Commit messages: imperative mood ("Add rain threshold logic", not "Added")
- One logical change per commit
