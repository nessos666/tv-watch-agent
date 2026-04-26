# agent/cdp_client.py
from __future__ import annotations
import base64
import json
import requests
import websocket


class CdpClient:
    """Synchrone CDP-Verbindung zu TradingView via chrome-remote-interface Protokoll."""

    def __init__(self, host: str = "localhost", port: int = 9222):
        self.host = host
        self.port = port
        self._ws_url: str | None = None

    def find_chart_target(self) -> dict | None:
        try:
            resp = requests.get(f"http://{self.host}:{self.port}/json/list", timeout=5)
            targets = resp.json()
        except Exception:
            return None
        tv = next(
            (
                t
                for t in targets
                if t.get("type") == "page"
                and "tradingview.com/chart" in t.get("url", "")
            ),
            None,
        )
        if tv:
            return tv
        return next(
            (
                t
                for t in targets
                if t.get("type") == "page" and "tradingview" in t.get("url", "").lower()
            ),
            None,
        )

    def connect(self) -> None:
        target = self.find_chart_target()
        if not target:
            raise RuntimeError("Kein TradingView Chart gefunden – ist TV offen?")
        self._ws_url = target["webSocketDebuggerUrl"]

    def _send_cdp(self, method: str, params: dict | None = None) -> dict:
        """Schickt einen CDP-Befehl via WebSocket (sync)."""
        if not self._ws_url:
            self.connect()
        ws = websocket.create_connection(self._ws_url, timeout=10)
        try:
            msg = json.dumps({"id": 1, "method": method, "params": params or {}})
            ws.send(msg)
            raw = ws.recv()
            return json.loads(raw)
        finally:
            ws.close()

    def evaluate(self, expression: str) -> object:
        result = self._send_cdp(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
            },
        )
        inner = result.get("result", {})
        if "exceptionDetails" in inner:
            raise RuntimeError(f"JS Fehler: {inner['exceptionDetails']}")
        return inner.get("result", {}).get("value")

    def screenshot(self) -> bytes:
        result = self._send_cdp("Page.captureScreenshot", {"format": "png"})
        inner = result.get("result", {})
        data = inner.get("data", "")
        return base64.b64decode(data)
