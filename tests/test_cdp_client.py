# tests/test_cdp_client.py
from unittest.mock import patch
from agent.cdp_client import CdpClient


def test_find_chart_target_returns_none_when_no_tv():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = []
        client = CdpClient(host="localhost", port=9222)
        target = client.find_chart_target()
        assert target is None


def test_evaluate_returns_value():
    client = CdpClient(host="localhost", port=9222)
    client._ws_url = "ws://localhost:9222/fake"
    with patch.object(client, "_send_cdp") as mock_send:
        mock_send.return_value = {"result": {"result": {"value": 42}}}
        result = client.evaluate("1 + 1")
        assert result == 42


def test_screenshot_returns_bytes():
    import base64

    client = CdpClient(host="localhost", port=9222)
    client._ws_url = "ws://localhost:9222/fake"
    with patch.object(client, "_send_cdp") as mock_send:
        fake_png = base64.b64encode(b"PNG_DATA").decode()
        mock_send.return_value = {"result": {"data": fake_png}}
        data = client.screenshot()
        assert isinstance(data, bytes)
        assert len(data) > 0


def test_evaluate_raises_on_exception_details():
    import pytest

    client = CdpClient(host="localhost", port=9222)
    client._ws_url = "ws://localhost:9222/fake"
    with patch.object(client, "_send_cdp") as mock_send:
        mock_send.return_value = {
            "result": {"exceptionDetails": {"text": "ReferenceError: x is not defined"}}
        }
        with pytest.raises(RuntimeError, match="JS Fehler"):
            client.evaluate("x")


def test_screenshot_raises_on_empty_data():
    import pytest

    client = CdpClient(host="localhost", port=9222)
    client._ws_url = "ws://localhost:9222/fake"
    with patch.object(client, "_send_cdp") as mock_send:
        mock_send.return_value = {"result": {"data": ""}}
        with pytest.raises(RuntimeError, match="Screenshot fehlgeschlagen"):
            client.screenshot()
