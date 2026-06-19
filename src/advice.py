"""
src/advice.py
Matches calendar events to weather windows and generates human-readable advice.
"""

from typing import Optional
from src.weather import get_weather_for_window, worst_conditions, WMO_THUNDERSTORM_CODES, WMO_SNOW_CODES


DEFAULT_THRESHOLDS = {
    "rain_pct": 50,
    "temp_high_f": 95,
    "temp_low_f": 32,
    "wind_mph": 30,
}


def generate_advice(
    event: dict,
    weather_data: Optional[dict],
    units: str = "imperial",
    thresholds: Optional[dict] = None,
) -> dict:
    """
    Generate weather-aware advice for a single calendar event.

    Returns a dict with:
      - event: the original event
      - conditions: worst-case weather slot (or None)
      - warnings: list of warning strings
      - summary: one-line human-readable advice
    """
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    temp_unit = "°F" if units == "imperial" else "°C"
    wind_unit = "mph" if units == "imperial" else "km/h"

    if not weather_data:
        return {
            "event": event,
            "conditions": None,
            "warnings": [],
            "summary": f"No weather data available for '{event['title']}'.",
        }

    slots = get_weather_for_window(
        weather_data,
        event["date"],
        event["start_time"],
        event["end_time"],
    )
    worst = worst_conditions(slots)

    if not worst:
        return {
            "event": event,
            "conditions": None,
            "warnings": [],
            "summary": f"No weather data available for this time window.",
        }

    warnings = _check_warnings(worst, t, temp_unit, wind_unit)

    summary = _build_summary(event, worst, warnings, temp_unit)

    return {
        "event": event,
        "conditions": worst,
        "warnings": warnings,
        "summary": summary,
    }


def _check_warnings(
    slot: dict,
    thresholds: dict,
    temp_unit: str,
    wind_unit: str,
) -> list[str]:
    """Generate a list of warning strings from a weather slot."""
    warnings = []
    code = slot.get("code", 0)
    precip = slot.get("precip_pct", 0) or 0
    temp = slot.get("temp")
    wind = slot.get("wind", 0) or 0

    if code in WMO_THUNDERSTORM_CODES:
        warnings.append("⛈️  Thunderstorm likely — consider rescheduling outdoor plans.")
    elif code in WMO_SNOW_CODES:
        warnings.append("🌨️  Snow expected — allow extra travel time.")
    elif precip >= thresholds["rain_pct"]:
        warnings.append(f"☔ {precip}% chance of rain — bring an umbrella.")

    if temp is not None:
        if temp >= thresholds["temp_high_f"]:
            warnings.append(f"🥵 High of {temp}{temp_unit} — stay hydrated, limit outdoor exposure.")
        elif temp <= thresholds["temp_low_f"]:
            warnings.append(f"🥶 Temperature {temp}{temp_unit} — dress warmly.")

    if wind >= thresholds["wind_mph"]:
        warnings.append(f"💨 Wind {wind}{wind_unit} — watch for gusts if outdoors.")

    return warnings


def _build_summary(
    event: dict,
    worst: dict,
    warnings: list[str],
    temp_unit: str,
) -> str:
    """Compose the one-line summary shown next to the event."""
    desc = worst.get("description", "Unknown conditions")
    temp = worst.get("temp")
    temp_str = f", {temp}{temp_unit}" if temp is not None else ""
    base = f"{desc}{temp_str}"

    if not warnings:
        return f"✅ {base} — looks good!"
    # Lead with the first (most severe) warning's emoji + short text
    lead = warnings[0].split("—")[0].strip()
    return f"{lead} ({base})"


def build_day_report(
    date_str: str,
    events: list[dict],
    weather_data: Optional[dict],
    units: str = "imperial",
    thresholds: Optional[dict] = None,
) -> list[dict]:
    """
    Generate advice for every event on a given day.
    Returns a list of advice dicts (same structure as generate_advice output).
    """
    return [
        generate_advice(event, weather_data, units=units, thresholds=thresholds)
        for event in events
    ]
