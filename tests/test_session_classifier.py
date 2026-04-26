# tests/test_session_classifier.py
from datetime import datetime, timezone
from agent.session_classifier import classify_session, session_boundary_crossed


def ts(hour, minute=0):
    """UTC-Timestamp erstellen."""
    return datetime(2025, 10, 1, hour, minute, tzinfo=timezone.utc).timestamp()


def test_asia_session():
    assert classify_session(ts(2)) == "ASIA"


def test_london_session():
    assert classify_session(ts(8)) == "LONDON"


def test_premarkt_session():
    assert classify_session(ts(12)) == "PREMARKT"


def test_ny_am_session():
    assert classify_session(ts(14)) == "NY_AM"


def test_lunch_session():
    assert classify_session(ts(17)) == "LUNCH"


def test_pm_session():
    assert classify_session(ts(19)) == "PM"


def test_off_session():
    assert classify_session(ts(22)) == "OFF"


def test_boundary_crossed_detects_change():
    assert session_boundary_crossed("ASIA", "LONDON") is True


def test_boundary_not_crossed():
    assert session_boundary_crossed("LONDON", "LONDON") is False
