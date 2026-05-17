<p align="center">
  <h1 align="center">TV Watch Agent</h1>
  <p align="center">
    <strong>Automated TradingView chart surveillance — CDP-based screenshot agent with session-aware logging, backup rotation, and 24/7 systemd operation.</strong>
  </p>
  <p align="center">
    <a href="#why">Why</a> · <a href="#cdp">CDP Protocol</a> · <a href="#24-7">24/7 Operation</a> · <a href="#session-classification">Session Classification</a> · <a href="#api">API</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/sessions-7_auto_classify-orange" alt="Session classification">
  <img src="https://img.shields.io/badge/CDP-Chrome_DevTools_Protocol-blue" alt="CDP mode">
  <img src="https://img.shields.io/badge/24x7-systemd_ready-success" alt="systemd ready">
  <img src="https://img.shields.io/github/stars/nessos666/tv-watch-agent?style=social" alt="Stars">
</p>

---

## Why?

If you're running algorithmic NQ futures strategies, you face a blind spot: **you don't know what the chart looks like right now**.

Price data alone isn't enough. You need to see:

- **Session transitions** — is NY AM about to open? Did London just end?
- **Key levels getting hit** — are my support/resistance levels being tested?
- **Order blocks forming** — is price reacting at expected zones?
- **Sweeps happening** — did liquidity get taken out above/below structure?
- **Indicator divergence** — is RSI showing hidden divergence that my code hasn't flagged yet?

**TV Watch Agent solves this.** It connects to TradingView via Chrome DevTools Protocol (CDP), takes periodic snapshots, automatically classifies the market session, and logs everything to CSV with backup rotation.

No API keys. No Pine Script injection. No cloud dependency. Just the chart.

---

## CDP: How It Connects

Chrome DevTools Protocol (CDP) is the same protocol Chrome's DevTools uses — it gives you programmatic access to a running browser instance.

```
┌───────────────────┐     CDP WebSocket (ws://127.0.0.1:9222)     ┌──────────────────┐
│   TradingView     │ ◄──────────────────────────────────────────► │   Watch Agent    │
│   (Chrome)        │                                              │   (Python CDP)   │
│                   │   Page.captureScreenshot() ◄─────────────    │                  │
│   --remote-       │   Runtime.evaluate() ◄──────────────────    │   watch_agent.py │
│   debugging-      │   Page.getLayoutMetrics() ◄─────────────    │                  │
│   port=9222       │                                              │                  │
└───────────────────┘                                              └──────────────────┘
```

### Why CDP instead of Selenium or Playwright?

| Approach | Requires | Speed | Stability | TradingView Compatible |
|----------|----------|-------|-----------|----------------------|
| **CDP (this project)** | Chrome with `--remote-debugging-port` | Fast | Very stable | ✅ Full chart rendering |
| **Selenium** | WebDriver + browser driver | Medium | Can be flaky | ⚠️ TradingView blocks some automation |
| **Playwright** | Browser binary download | Medium | Good | ⚠️ TV can detect headless Chrome |
| **Screenshot tool** | xdotool, scrot | Fast | OS-dependent | ✅ Works but no page interaction |

**CDP is the sweet spot:** it attaches to your *existing* TradingView Chrome instance — no new browser needed, no automation detection, full chart rendering quality.

### Launching TradingView with CDP

```bash
# Linux: Launch TV Desktop with remote debugging enabled
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/tv-profile

# Verify connection
curl -s http://localhost:9222/json/list | python3 -m json.tool
```

---

## 24/7 Operation (systemd)

The agent is designed to run **24 hours a day, 7 days a week**. Two systemd services handle this:

### Service 1: TradingView Chrome instance

```ini
[Unit]
Description=TradingView Chrome (CDP)
After=network.target

[Service]
ExecStart=/usr/bin/google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/tv-profile
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

### Service 2: Watch Agent

```ini
[Unit]
Description=TV Watch Agent
After=tv-chrome.service
BindsTo=tv-chrome.service

[Service]
ExecStart=/path/to/venv/bin/python /path/to/watch_agent.py
Restart=always
RestartSec=10
EnvironmentFile=/path/to/.env

[Install]
WantedBy=default.target
```

### Start everything

```bash
systemctl --user enable --now tv-chrome tv-watch-agent
```

The agent:
- Survives reboots (systemd restarts automatically)
- Restarts on crash (RestartSec=10)
- Connects immediately when Chrome is ready (BindsTo)
- Logs rotation handled by systemd journal

---

## Session Classification

The agent automatically detects which market session is active based on Eastern Time:

| Session | Time (ET) | Characteristics |
|---------|-----------|-----------------|
| **Asia** | 19:00–03:00 | Low volume, range-bound, overnight positioning |
| **London** | 03:00–09:30 | European open, increased volatility, participation |
| **Pre-Market** | 07:00–09:30 | US futures active, positioning before NY cash open |
| **NY AM** | 09:30–12:00 | **Highest volume**, institutional order flow, breakouts |
| **Lunch** | 12:00–13:30 | Volume drop, mean reversion, consolidation |
| **PM** | 13:30–16:00 | Second session, often continuation or reversal of NY AM |
| **Off** | 17:00–18:00 | Daily market pause. Also during weekends (Fri 17:00 – Sun 18:00) |

Screenshots are **named by session type** for easy visual review:

```
output/shots/
├── snap_1759455300_ASIA.png
├── snap_1759470600_OFF.png
├── snap_1759485900_LONDON.png
├── snap_1759501500_NY_AM.png
├── snap_1759516800_PM.png
├── snap_1759707000_OFF.png
...
```

This lets you quickly scan which sessions had interesting price action without opening every screenshot.

---

## Quick Start

```bash
# 1. Start TradingView with CDP
google-chrome --remote-debugging-port=9222

# 2. Install and run the agent
git clone https://github.com/nessos666/tv-watch-agent.git
cd tv-watch-agent
pip install -r requirements.txt
python watch_agent.py
```

---

## Configuration

Edit `config.toml`:

```toml
[cdp]
host = "127.0.0.1"
port = 9222

[agent]
interval = 300  # seconds between snapshots
output_dir = "output"
auto_backup_interval = 10  # saves every N snapshots
```

### Command-line options

```bash
python watch_agent.py --interval 60     # every 60 seconds
python watch_agent.py --cdp-port 9222
python watch_agent.py --output /path/to/screenshots
```

---

## API Components

### CDP Client (`agent/cdp_client.py`)

Low-level Chrome DevTools Protocol wrapper:

- `connect()` — attach to a CDP endpoint via WebSocket
- `capture_screenshot()` — capture current page as PNG (returns bytes)
- `execute_script(js)` — run JavaScript in page context, return result
- `get_dom_snapshot()` — snapshot the DOM tree for parsing

### Chart Reader (`agent/chart_reader.py`)

Extracts visible chart data from the TradingView DOM:

- Current price and OHLC values
- Visible date range on chart
- Active indicators (RSI, MACD, Bollinger Bands)
- Drawn levels and annotations

### Session Classifier (`agent/session_classifier.py`)

Time-based market session detection:

- Full NQ futures schedule (Sunday 18:00 – Friday 17:00 ET)
- Automatic off-hours detection (daily pause 17:00-18:00 ET)
- Weekend detection (no false alerts on Saturday)

### Data Logger (`agent/data_logger.py`)

Persistent logging with crash-safe backup:

- Writes timestamped CSV rows on each snapshot
- Automatic backup every N snapshots (configurable)
- SIGINT-safe — saves CSV on Ctrl+C
- Configurable output directory

---

## Output

```
output/
├── watch_log.csv           # Main log — timestamp, session, price, etc.
├── backups/
│   └── watch_log_*.csv     # Automatic backups at configurable intervals
└── shots/
    └── snap_unix_ts_SESSION.png  # Session-labeled screenshots
```

Example log row:

```csv
timestamp,session,price,trend,volume,indicators
2026-03-21T09:35:00-04:00,NY_AM,19250.00,bullish,high,RSI:62.4
```

---

## Project Structure

```
.
├── watch_agent.py         # Entrypoint — connects CDP, loops snapshots (105 lines)
├── config.toml            # Configuration
├── agent/
│   ├── cdp_client.py      # Chrome DevTools Protocol client
│   ├── chart_reader.py    # TV chart DOM parser
│   ├── data_logger.py     # CSV logger with backup rotation
│   ├── session_classifier.py  # NQ futures session detection
│   └── snapshot.py        # Screenshot orchestrator
├── tests/
│   ├── test_cdp_client.py
│   ├── test_chart_reader.py
│   ├── test_data_logger.py
│   └── test_session_classifier.py
└── requirements.txt
```

---

## Testing

```bash
pytest tests/ -v
```

---

## Related

Part of the NQ research infrastructure ecosystem:

- [chart-vision-mcp](https://github.com/nessos666/chart-vision-mcp) — Visual chart structure analysis via OpenCV
- [topstepx-api-health-monitor](https://github.com/nessos666/topstepx-api-health-monitor) — API health checks for trading connections
- [nq-strategy-builder](https://github.com/nessos666/nq-strategy-builder) — Full anti-overfitting backtesting framework

---

## License

MIT

<p align="center">
  <small>Built for systematic NQ futures research. 24/7 chart surveillance, zero API costs.<br>
  <strong>github.com/nessos666</strong></small>
</p>
