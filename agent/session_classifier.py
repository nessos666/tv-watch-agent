# agent/session_classifier.py
from __future__ import annotations
from datetime import datetime, timezone

# (session_name, start_utc_hour_inclusive, end_utc_hour_exclusive)
_SESSIONS: list[tuple[str, float, float]] = [
    ("ASIA", 1.0, 5.0),
    ("LONDON", 7.0, 11.5),
    ("PREMARKT", 11.5, 13.5),
    ("NY_AM", 13.5, 16.5),
    ("LUNCH", 16.5, 18.0),
    ("PM", 18.0, 21.0),
]


def classify_session(unix_ts: float) -> str:
    """Gibt Session-Name zurück basierend auf UTC-Stunde des Chart-Bar-Timestamps."""
    dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    h = dt.hour + dt.minute / 60.0
    for name, start, end in _SESSIONS:
        if start <= h < end:
            return name
    return "OFF"


def session_boundary_crossed(prev: str, current: str) -> bool:
    """True wenn Session gewechselt hat."""
    return prev != current
