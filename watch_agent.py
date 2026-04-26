#!/usr/bin/env python3
"""
TV Watch Agent – beobachtet TradingView Replay und zeichnet PAT25-Sessions auf.

Usage:
    python watch_agent.py                    # default config
    python watch_agent.py --interval 3       # poll alle 3 Sekunden
    python watch_agent.py --output /tmp/tv   # anderer Output-Ordner
"""

from __future__ import annotations
import argparse
import sys
import time
import tomllib
from pathlib import Path

from agent.cdp_client import CdpClient
from agent.chart_reader import ChartReader
from agent.data_logger import DataLogger
from agent.snapshot import capture_snapshot


def load_config(path: Path = Path("config.toml")) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="TV Watch Agent")
    parser.add_argument(
        "--interval", type=float, default=None, help="Poll-Intervall in Sekunden"
    )
    parser.add_argument("--output", type=str, default=None, help="Output-Ordner")
    parser.add_argument("--config", type=str, default="config.toml")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    interval = args.interval or cfg["agent"]["poll_interval_sec"]
    output_dir = Path(args.output or cfg["agent"]["output_dir"])
    backup_every = max(1, cfg["agent"].get("backup_every_n_snapshots", 10))

    print("TV Watch Agent gestartet")
    print(f"Output: {output_dir.resolve()}")
    print(f"Poll-Intervall: {interval}s")
    print("Verbinde zu CDP...")

    cdp = CdpClient(host=cfg["cdp"]["host"], port=cfg["cdp"]["port"])
    cdp.connect()
    print("CDP verbunden. Warte auf Replay...")

    reader = ChartReader(cdp)
    logger = DataLogger(output_dir)
    prev_session = "OFF"
    snapshots_total = 0

    try:
        while True:
            try:
                prev_session, saved = capture_snapshot(
                    cdp, reader, logger, prev_session
                )
                if saved:
                    snapshots_total += 1
                    print(
                        f"  [{snapshots_total}] Session: {prev_session} -> Snapshot gespeichert"
                    )
                    if snapshots_total % backup_every == 0:
                        bak = logger.backup(f"auto_{snapshots_total}")
                        if bak:
                            print(f"  [BACKUP] -> {bak}")
            except Exception as e:  # noqa: BLE001
                print(f"  WARN: {e}", file=sys.stderr)
            time.sleep(interval)
    except KeyboardInterrupt:
        bak = logger.backup("exit")
        if bak:
            print(f"\nBackup gespeichert: {bak}")
        print(f"Agent gestoppt. {snapshots_total} Snapshots -> {output_dir.resolve()}")


if __name__ == "__main__":
    main()
