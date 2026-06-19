"""
src/formatter.py
Renders advice output to the terminal with optional color.
"""

import sys
from datetime import datetime, date

# ANSI color codes — only used when stdout is a real terminal
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[36m"
YELLOW = "\033[33m"
RED    = "\033[31m"
GREEN  = "\033[32m"
DIM    = "\033[2m"


def _use_color() -> bool:
    """Return True if the terminal supports ANSI color codes."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    """Wrap text in an ANSI color code (only if terminal supports it)."""
    if _use_color():
        return f"{code}{text}{RESET}"
    return text


def print_header(location_name: str, generated_at: Optional[str] = None) -> None:
    """Print the app banner."""
    from typing import Optional  # local import to avoid circular
    ts = generated_at or datetime.now().strftime("%a %b %d, %Y %I:%M %p")
    print()
    print(_c(BOLD + CYAN, "╔══════════════════════════════════════════╗"))
    print(_c(BOLD + CYAN, f"  🌤  Weather-Aware Assistant — {location_name}"))
    print(_c(BOLD + CYAN, f"  📅  {ts}"))
    print(_c(BOLD + CYAN, "╚══════════════════════════════════════════╝"))
    print()


def print_day_section(date_str: str) -> None:
    """Print a section header for a calendar day."""
    try:
        d = date.fromisoformat(date_str)
        label = d.strftime("%A, %B %-d")  # e.g. "Tuesday, June 20"
    except (ValueError, AttributeError):
        label = date_str
    print(_c(BOLD + YELLOW, f"  ── {label} ──"))


def print_event_advice(advice: dict, indent: int = 4) -> None:
    """Print formatted advice for one event."""
    pad = " " * indent
    event = advice["event"]
    warnings = advice.get("warnings", [])
    summary = advice.get("summary", "")
    conditions = advice.get("conditions")

    time_str = f"{event['start_time']}–{event['end_time']}"
    title = event["title"]
    location = f"  📍 {event['location']}" if event.get("location") else ""

    print(f"{pad}{_c(BOLD, title)}  {_c(DIM, time_str)}{location}")
    print(f"{pad}   {summary}")

    for w in warnings[1:]:   # first warning already in summary; show extras
        print(f"{pad}   {w}")

    print()


def print_no_events(date_str: str) -> None:
    """Inform the user there are no events for a given day."""
    print(f"    {_c(DIM, 'No events scheduled.')}")
    print()


def print_footer(days_shown: int) -> None:
    """Print a short footer."""
    print(_c(DIM, f"  Showing {days_shown} day(s). Run with --help for options."))
    print()
