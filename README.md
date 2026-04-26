# TV Watch Agent

Autonomer Python-Agent der TradingView Replay beobachtet und PAT25 Session-Levels aufzeichnet.
Verbindet via CDP (Port 9222) direkt zu TradingView Desktop – kein Plugin, kein API-Key.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests websocket-client Pillow pytest
```

## Benutzung

1. TradingView öffnen (Chart mit **PAT25 Sessions** Indikator sichtbar)
2. Agent starten:
   ```bash
   python watch_agent.py
   ```
3. In TradingView: Replay auf gewünschtes Datum zurücksetzen (z.B. 01.10.2025)
4. Replay starten – beliebige Speed
5. Agent läuft automatisch: bei jedem Session-Wechsel → Screenshot + CSV-Eintrag
6. Abbrechen: `Ctrl+C`

## Optionen

```bash
python watch_agent.py --interval 3      # poll alle 3 Sekunden (default: 5)
python watch_agent.py --output /tmp/tv  # anderer Output-Ordner
python watch_agent.py --config my.toml  # andere Config
```

## Output

- `output/watch_log.csv` – alle Session-Übergänge mit PAT25 Levels + Preis
- `output/shots/` – Screenshots bei jedem Session-Wechsel

## CSV-Spalten

`chart_ts, chart_datetime, real_ts, session, price, screenshot,`
`Asia H, Asia L, LDN H, LDN L, PreM H, PreM L, AM H, AM L,`
`Lunch H, Lunch L, PM H, PM L, LHoT H, LHoT L, Settlement, 00:00`

## Sessions (UTC)

| Session | UTC | Beschreibung |
|---------|-----|-------------|
| ASIA | 01:00–05:00 | Asiatische Session |
| LONDON | 07:00–11:30 | Londoner Session |
| PREMARKT | 11:30–13:30 | Pre-Market NY |
| NY_AM | 13:30–16:30 | NY Morning Session |
| LUNCH | 16:30–18:00 | NY Lunch |
| PM | 18:00–21:00 | PM Session |

## Tests

```bash
pytest tests/ -v
```

## Architektur

```
watch_agent.py          ← CLI Entry Point
agent/
  cdp_client.py         ← CDP WebSocket Verbindung
  chart_reader.py       ← PAT25 Labels + OHLCV lesen
  session_classifier.py ← UTC-Zeit → Session-Name
  snapshot.py           ← Snapshot-Logik (nur bei Session-Wechsel)
  data_logger.py        ← CSV + Screenshot speichern
```
