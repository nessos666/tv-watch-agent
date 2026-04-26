# tests/test_data_logger.py
import csv
import tempfile
from pathlib import Path
from agent.data_logger import DataLogger, Snapshot


def make_snapshot(session="NY_AM", price=27440.0):
    return Snapshot(
        chart_ts=1777000000,
        real_ts=1777000001.0,
        session=session,
        price=price,
        levels={"Asia H": 27135.75, "PM H": 27462.5, "Settlement": 27414.5},
        screenshot_path="output/shots/snap_001.png",
    )


def test_logger_creates_csv():
    with tempfile.TemporaryDirectory() as d:
        logger = DataLogger(output_dir=Path(d))
        logger.log(make_snapshot())
        csv_file = Path(d) / "watch_log.csv"
        assert csv_file.exists()


def test_logger_writes_header_and_row():
    with tempfile.TemporaryDirectory() as d:
        logger = DataLogger(output_dir=Path(d))
        logger.log(make_snapshot())
        rows = list(csv.DictReader(open(Path(d) / "watch_log.csv")))
        assert len(rows) == 1
        assert rows[0]["session"] == "NY_AM"
        assert float(rows[0]["price"]) == 27440.0
        assert "Asia H" in rows[0]


def test_logger_appends_multiple_rows():
    with tempfile.TemporaryDirectory() as d:
        logger = DataLogger(output_dir=Path(d))
        logger.log(make_snapshot("LONDON", 27100.0))
        logger.log(make_snapshot("NY_AM", 27440.0))
        rows = list(csv.DictReader(open(Path(d) / "watch_log.csv")))
        assert len(rows) == 2


def test_screenshot_saved():
    with tempfile.TemporaryDirectory() as d:
        logger = DataLogger(output_dir=Path(d))
        path = logger.save_screenshot(
            b"PNG_FAKE_DATA", chart_ts=1777000000, session="NY_AM"
        )
        assert Path(path).exists()
        assert Path(path).read_bytes() == b"PNG_FAKE_DATA"
