<p align="center">
  <h1 align="center">TV Watch Agent</h1>
  <p align="center">
    <strong>Automated TradingView chart watcher — CDP-based screenshot agent with session-aware logging.</strong>
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> · <a href="#how-it-works">How It Works</a> · <a href="#configuration">Configuration</a> · <a href="#api">API</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/sessions-5_auto_classify-orange" alt="Session classification">
  <img src="https://img.shields.io/badge/CDP-Chrome_DevTools_Protocol-blue" alt="CDP mode">
</p>

---

## Why?

If you're running algorithmic NQ strategies, you need to know what the market is doing at any given time. Not just price — but **market structure**: session transitions, key levels getting hit, order blocks forming, sweeps happening.

**TV Watch Agent connects to TradingView via Chrome DevTools Protocol (CDP), takes periodic snapshots, classifies market sessions automatically, and logs everything to CSV.**

No API keys needed. No Pine Script injection required. Just the chart.

---

## Quick Start

```bash
git clone https://github.com/nessos666/tv-watch-agent.git
cd tv-watch-agent
pip install -r requirements.txt

# Start watching (requires TradingView running with --remote-debugging-port=9222)
python watch_agent.py
```

---

## How It Works

```
┌─────────────┐     CDP (port 9222)    ┌──────────────────┐
│ TradingView  │ ◄────────────────────── │  Watch Agent     │
│ (Chrome)     │      Page.captureScreenshot   │  (CDP client)    │
└─────────────┘                           │                  │
                                          │  Classifies      │
┌─────────────┐                           │  session type    │
│ Market data  │ ◄────────────────────── │  (NY AM/London/   │
│ (TV via CDP) │                           │   Asia/PM/Off)   │
└─────────────┘                           │                  │
                                          │  Logs to CSV     │
                                          └──────────────────┘
```

The agent uses **Chrome DevTools Protocol** to:

1. Connect to a running TradingView Chrome instance
2. Capture screenshots at configurable intervals
3. Classify the current market session (NY AM, London, Asia, PM, Off-hours)
4. Log all data to timestamped CSV files with automatic backup rotation

### Session Classification

The agent automatically detects which market session is active:

| Session | Time (ET) | Description |
|---------|-----------|-------------|
| Asia | 19:00–03:00 | Overnight session |
| London | 03:00–09:30 | European open |
| Pre-Market | 07:00–09:30 | US pre-market preparation |
| NY AM | 09:30–12:00 | US morning session (highest volume) |
| Lunch | 12:00–13:30 | Midday pause |
| PM | 13:30–16:00 | US afternoon session |
| Off | 17:00–18:00 | Daily market pause, Sunday/Friday close |

Screenshots are named by session type for easy review.

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
python watch_agent.py --interval 60 --cdp-port 9222
python watch_agent.py --output /path/to/screenshots
```

---

## API Components

### CDP Client (`agent/cdp_client.py`)

Low-level Chrome DevTools Protocol wrapper:

- `connect()` — attach to a CDP endpoint
- `capture_screenshot()` — capture current page as PNG
- `execute_script()` — run JavaScript in page context
- `get_dom_snapshot()` — snapshot the DOM tree

### Chart Reader (`agent/chart_reader.py`)

Extracts visible chart data from the TradingView DOM:

- Current price and OHLC
- Visible date range
- Active indicators (RSI, MACD, etc.)
- Drawn levels and annotations

### Session Classifier (`agent/session_classifier.py`)

Time-based market session detection:

- Full schedule for NQ futures (Sunday 18:00 – Friday 17:00 ET)
- Automatic off-hours detection
- Holiday calendar awareness

### Data Logger (`agent/data_logger.py`)

Persistent logging with backup:

- Writes timestamped CSV rows
- Automatic backup every N snapshots
- Exit-safe (saves CSV on Ctrl+C / SIGINT)
- Configurable output directory

---

## Project Structure

```
.
├── watch_agent.py         # Entrypoint — connects CDP, loops snapshots
├── config.toml            # Configuration
├── agent/
│   ├── cdp_client.py      # Chrome DevTools Protocol client
│   ├── chart_reader.py    # TV chart DOM parser
│   ├── data_logger.py     # CSV logger with backup rotation
│   ├── session_classifier.py  # Session detection
│   └── snapshot.py        # Screenshot orchestrator
├── tests/
│   ├── test_cdp_client.py
│   ├── test_chart_reader.py
│   ├── test_data_logger.py
│   └── test_session_classifier.py
└── requirements.txt
```

---

## Output

```
output/
├── watch_log.csv           # Main log (timestamp, price, session, etc.)
├── backups/
│   └── watch_log_*.csv     # Automatic backups at intervals
└── shots/
    └── snap_*.png          # Session-labeled screenshots
```

All output goes to the configured `output_dir` (default: `output/`).

---

## License

MIT

<p align="center">
  <small>Built for systematic NQ futures research.<br>
  <strong>github.com/nessos666</strong></small>
</p>
