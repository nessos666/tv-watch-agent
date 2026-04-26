# agent/snapshot.py
from __future__ import annotations
import time
from agent.cdp_client import CdpClient
from agent.chart_reader import ChartReader
from agent.session_classifier import classify_session, session_boundary_crossed
from agent.data_logger import DataLogger, Snapshot


def capture_snapshot(
    cdp: CdpClient,
    reader: ChartReader,
    logger: DataLogger,
    prev_session: str,
) -> tuple[str, bool]:
    """
    Liest aktuellen Chart-State + PAT25 Levels.
    Gibt zurück: (current_session, snapshot_saved).
    Macht Screenshot + CSV-Eintrag NUR bei Session-Wechsel.
    """
    bar = reader.get_current_bar()
    if not bar:
        return prev_session, False

    chart_ts = bar["time"]
    price = bar["close"]
    current_session = classify_session(chart_ts)

    if session_boundary_crossed(prev_session, current_session):
        labels = reader.labels_as_dict()
        png = cdp.screenshot()
        screenshot_path = logger.save_screenshot(png, chart_ts, current_session)
        snap = Snapshot(
            chart_ts=chart_ts,
            real_ts=time.time(),
            session=current_session,
            price=price,
            levels=labels,
            screenshot_path=screenshot_path,
        )
        logger.log(snap)
        return current_session, True

    return current_session, False
