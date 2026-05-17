# agent/cdp_client.py
from __future__ import annotations
import base64
import json
import threading
import requests
import websocket

_KEEPALIVE_INTERVAL = 20  # Sekunden – hält CDP-WS vor Timeout durch Inaktivität warm


class CdpClient:
    """Synchrone CDP-Verbindung zu TradingView via chrome-remote-interface Protokoll.

    Hält eine persistente WebSocket-Verbindung – verbindet sich nur bei Bedarf neu.
    """

    def __init__(self, host: str = "localhost", port: int = 9222):
        self.host = host
        self.port = port
        self._ws_url: str | None = None
        self._ws: websocket.WebSocket | None = None
        self._msg_id: int = 0
        self._keepalive_timer: threading.Timer | None = None

    def find_chart_target(self) -> dict | None:
        try:
            resp = requests.get(f"http://{self.host}:{self.port}/json/list", timeout=5)
            targets = resp.json()
        except (requests.RequestException, ValueError):
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
        self._ws_connect()

    def _ws_connect(self) -> None:
        """Öffnet die persistente WebSocket-Verbindung und startet Keepalive."""
        try:
            self._ws = websocket.create_connection(
                self._ws_url, timeout=10, suppress_origin=True
            )
        except websocket.WebSocketException as e:
            raise RuntimeError(f"WebSocket-Verbindung fehlgeschlagen: {e}") from e
        self._start_keepalive()

    def _start_keepalive(self) -> None:
        """Startet den Keepalive-Timer (rekursiv, alle 20s)."""
        t = threading.Timer(_KEEPALIVE_INTERVAL, self._send_keepalive)
        t.daemon = True
        t.start()
        self._keepalive_timer = t

    def _send_keepalive(self) -> None:
        """Sendet einen leichten CDP-Befehl um die Verbindung warm zu halten."""
        try:
            if self._ws and self._ws.connected:
                self._msg_id += 1
                msg = json.dumps(
                    {"id": self._msg_id, "method": "Runtime.getIsolateId", "params": {}}
                )
                self._ws.send(msg)
                self._ws.recv()  # Antwort verwerfen
        except Exception:  # noqa: BLE001
            pass  # Keepalive-Fehler ignorieren – _ensure_connected() handled Reconnect
        finally:
            if self._ws and self._ws.connected:
                self._start_keepalive()  # Nächsten Timer planen

    def _ensure_connected(self) -> None:
        """Stellt sicher dass die WS-Verbindung offen ist; verbindet bei Bedarf neu."""
        if not self._ws_url:
            self.connect()
            return
        if self._ws is None or not self._ws.connected:
            self._ws_connect()

    def _send_cdp(self, method: str, params: dict | None = None) -> dict:
        """Schickt einen CDP-Befehl über die persistente WebSocket-Verbindung."""
        self._ensure_connected()
        assert self._ws is not None
        self._msg_id += 1
        msg = json.dumps({"id": self._msg_id, "method": method, "params": params or {}})
        try:
            self._ws.send(msg)
            raw = self._ws.recv()
            return json.loads(raw)
        except (websocket.WebSocketException, json.JSONDecodeError) as e:
            self._ws = (
                None  # Verbindung als kaputt markieren → nächster Call reconnectet
            )
            raise RuntimeError(f"CDP-Kommunikationsfehler: {e}") from e

    def close(self) -> None:
        """Schließt die WebSocket-Verbindung und Keepalive-Timer sauber."""
        if self._keepalive_timer is not None:
            self._keepalive_timer.cancel()
            self._keepalive_timer = None
        if self._ws is not None:
            try:
                self._ws.close()
            except websocket.WebSocketException:
                pass
            self._ws = None

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
        if not data:
            raise RuntimeError("Screenshot fehlgeschlagen – keine Daten vom CDP")
        return base64.b64decode(data)
