# agent/data_logger.py
from __future__ import annotations
import csv
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Alle bekannten PAT25 Level-Namen – werden zu CSV-Spalten
_LEVEL_NAMES: list[str] = [
    "Asia H",
    "Asia L",
    "LDN H",
    "LDN L",
    "PreM H",
    "PreM L",
    "AM H",
    "AM L",
    "Lunch H",
    "Lunch L",
    "PM H",
    "PM L",
    "LHoT H",
    "LHoT L",
    "Settlement",
    "00:00",
]


@dataclass
class Snapshot:
    chart_ts: float  # UTC-Timestamp vom Chart (letzter Bar)
    real_ts: float  # Echter Zeitpunkt der Aufzeichnung
    session: str  # z.B. "NY_AM"
    price: float  # Close des letzten Bars
    levels: dict[str, float]  # PAT25 Labels → Preis
    screenshot_path: str  # Pfad zum Screenshot


class DataLogger:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.shots_dir = output_dir / "shots"
        self.csv_path = output_dir / "watch_log.csv"
        output_dir.mkdir(parents=True, exist_ok=True)
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        self._header_written = self.csv_path.exists()

    def _fieldnames(self) -> list[str]:
        return [
            "chart_ts",
            "chart_datetime",
            "real_ts",
            "session",
            "price",
            "screenshot",
        ] + _LEVEL_NAMES

    def log(self, snap: Snapshot) -> None:
        row: dict[str, object] = {
            "chart_ts": snap.chart_ts,
            "chart_datetime": datetime.fromtimestamp(
                snap.chart_ts, tz=timezone.utc
            ).isoformat(),
            "real_ts": snap.real_ts,
            "session": snap.session,
            "price": snap.price,
            "screenshot": snap.screenshot_path,
        }
        for name in _LEVEL_NAMES:
            row[name] = snap.levels.get(name, "")

        with open(self.csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames())
            if not self._header_written:
                writer.writeheader()
                self._header_written = True
            writer.writerow(row)

    def save_screenshot(self, png_data: bytes, chart_ts: float, session: str) -> str:
        fname = f"snap_{int(chart_ts)}_{session}.png"
        path = self.shots_dir / fname
        path.write_bytes(png_data)
        return str(path)

    def backup(self, label: str) -> "Path | None":
        """Kopiert die aktuelle CSV in output/backups/ mit Timestamp + Label.

        Gibt den Backup-Pfad zurück, oder None wenn noch keine CSV existiert.
        """
        if not self.csv_path.exists():
            return None
        backups_dir = self.output_dir / "backups"
        backups_dir.mkdir(exist_ok=True)
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = backups_dir / f"watch_log_{ts}_{label}.csv"
        shutil.copy2(self.csv_path, dest)
        return dest
