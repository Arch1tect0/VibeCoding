"""
src/weather.py
Fetches hourly weather data from Open-Meteo API and caches results locally.
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, date
from typing import Optional

# WMO Weather Code groups
WMO_THUNDERSTORM_CODES = {95, 96, 99}
WMO_SNOW_CODES = {71, 73, 75, 77, 85, 86}
WMO_RAIN_CODES = {51, 53, 55, 61, 63, 65, 80, 81, 82}

WMO_DESCRIPTIONS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


def _build_url(lat: float, lon: float, units: str) -> str:
    """Build the Open-Meteo API URL for hourly forecast data."""
    temp_unit = "fahrenheit" if units == "imperial" else "celsius"
    wind_unit = "mph" if units == "imperial" else "kmh"
    params = (
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation_probability,weathercode,windspeed_10m"
        f"&temperature_unit={temp_unit}"
        f"&windspeed_unit={wind_unit}"
        f"&forecast_days=8"
        f"&timezone=auto"
    )
    return f"{OPEN_METEO_BASE}?{params}"


def fetch_weather(
    lat: float,
    lon: float,
    units: str = "imperial",
    cache_path: str = "weather_cache.json",
    cache_ttl_minutes: int = 60,
) -> Optional[dict]:
    """
    Fetch hourly weather from Open-Meteo, using a local cache when fresh.

    Returns a dict keyed by ISO datetime string (e.g. "2025-06-20T14:00")
    with weather details, or None if the fetch fails.
    """
    cached = _load_cache(cache_path, cache_ttl_minutes)
    if cached is not None:
        return cached

    url = _build_url(lat, lon, units)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"⚠️  Weather fetch failed: {e.reason}. Proceeding without weather data.")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected error fetching weather: {e}")
        return None

    parsed = _parse_response(raw)
    _save_cache(cache_path, parsed)
    return parsed


def _parse_response(raw: dict) -> dict:
    """
    Convert Open-Meteo hourly arrays into a dict keyed by datetime string.

    Example key: "2025-06-20T14:00"
    Example value: {
        "temp": 82.4,
        "precip_pct": 70,
        "wind": 12.3,
        "code": 63,
        "description": "Moderate rain"
    }
    """
    hourly = raw.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    precips = hourly.get("precipitation_probability", [])
    codes = hourly.get("weathercode", [])
    winds = hourly.get("windspeed_10m", [])

    result = {}
    for i, t in enumerate(times):
        result[t] = {
            "temp": temps[i] if i < len(temps) else None,
            "precip_pct": precips[i] if i < len(precips) else 0,
            "wind": winds[i] if i < len(winds) else 0,
            "code": codes[i] if i < len(codes) else 0,
            "description": WMO_DESCRIPTIONS.get(codes[i] if i < len(codes) else 0, "Unknown"),
        }
    return result


def get_weather_for_window(
    weather_data: dict,
    event_date: str,
    start_time: str,
    end_time: str,
) -> list[dict]:
    """
    Return hourly weather slots that overlap with a calendar event window.

    Args:
        weather_data: Output of fetch_weather()
        event_date:   "YYYY-MM-DD"
        start_time:   "HH:MM"
        end_time:     "HH:MM"

    Returns list of matching hourly weather dicts (may be empty).
    """
    if not weather_data:
        return []

    start_dt = datetime.fromisoformat(f"{event_date}T{start_time}")
    end_dt = datetime.fromisoformat(f"{event_date}T{end_time}")

    slots = []
    for key, val in weather_data.items():
        try:
            slot_dt = datetime.fromisoformat(key)
        except ValueError:
            continue
        # Include slot if it starts within the event window
        if start_dt <= slot_dt < end_dt:
            slots.append({**val, "time": key})

    return slots


def worst_conditions(slots: list[dict]) -> Optional[dict]:
    """
    From a list of hourly slots, return the single worst-case slot
    (highest precipitation probability, breaking ties by wind speed).
    Returns None if slots is empty.
    """
    if not slots:
        return None
    return max(slots, key=lambda s: (s.get("precip_pct", 0), s.get("wind", 0)))


def _load_cache(cache_path: str, ttl_minutes: int) -> Optional[dict]:
    """Load cached weather if it exists and is still fresh."""
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, "r") as f:
            cache = json.load(f)
        saved_at = cache.get("_saved_at", 0)
        age_minutes = (time.time() - saved_at) / 60
        if age_minutes < ttl_minutes:
            return cache.get("data")
    except (json.JSONDecodeError, KeyError, OSError):
        pass
    return None


def _save_cache(cache_path: str, data: dict) -> None:
    """Save weather data to local cache with a timestamp."""
    try:
        with open(cache_path, "w") as f:
            json.dump({"_saved_at": time.time(), "data": data}, f)
    except OSError as e:
        print(f"⚠️  Could not write weather cache: {e}")
