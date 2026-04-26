# tests/test_chart_reader.py
from unittest.mock import MagicMock
from agent.chart_reader import ChartReader


def make_reader(eval_return):
    cdp = MagicMock()
    cdp.evaluate.return_value = eval_return
    return ChartReader(cdp)


def test_get_labels_returns_list():
    fake_labels = [
        {"text": "Asia H", "price": 27135.75},
        {"text": "PM H", "price": 27462.5},
        {"text": "Settlement", "price": 27414.5},
    ]
    reader = make_reader(fake_labels)
    labels = reader.get_pat25_labels()
    assert len(labels) == 3
    assert labels[0]["text"] == "Asia H"


def test_get_labels_returns_empty_on_none():
    reader = make_reader(None)
    labels = reader.get_pat25_labels()
    assert labels == []


def test_get_current_bar_returns_dict():
    fake_bar = {
        "time": 1777000000,
        "open": 27400.0,
        "high": 27450.0,
        "low": 27380.0,
        "close": 27440.0,
    }
    reader = make_reader(fake_bar)
    bar = reader.get_current_bar()
    assert bar["close"] == 27440.0
    assert bar["time"] == 1777000000


def test_labels_as_dict_maps_text_to_price():
    fake_labels = [
        {"text": "Asia H", "price": 27135.75},
        {"text": "LDN L", "price": 27016.25},
    ]
    reader = make_reader(fake_labels)
    reader.get_pat25_labels = lambda: fake_labels
    d = reader.labels_as_dict()
    assert d["Asia H"] == 27135.75
    assert d["LDN L"] == 27016.25
