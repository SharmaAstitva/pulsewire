"""Keeps the API's database in sync with the snapshot published by the
pipeline workflow (the `data` branch on GitHub).

Why: the AI pipeline needs far more memory than a free web server has, so it
runs on GitHub Actions. The API only has to download the finished database."""
import logging
import os
import threading
import time
from datetime import UTC, datetime

import httpx

from app import config, database

log = logging.getLogger("pulsewire.sync")

_state: dict = {"enabled": False, "etag": None, "last_sync": None, "last_error": None}
_lock = threading.Lock()


def status() -> dict:
    return {k: v for k, v in _state.items() if k != "etag"}


def sync_once(url: str | None = None) -> bool:
    """Download the snapshot if it changed. Returns True when a new file was installed."""
    url = url or config.DATA_URL
    with _lock:
        headers = {"If-None-Match": _state["etag"]} if _state["etag"] else {}
        response = httpx.get(url, headers=headers, timeout=60, follow_redirects=True)
        if response.status_code == 304:
            return False
        response.raise_for_status()
        if not response.content.startswith(b"SQLite format 3"):
            raise ValueError("Downloaded snapshot is not a SQLite database")

        target = config.DB_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".download")
        tmp.write_bytes(response.content)
        os.replace(tmp, target)  # atomic swap
        database.configure(target)

        _state.update(
            etag=response.headers.get("etag"),
            last_sync=datetime.now(UTC).isoformat(),
            last_error=None,
        )
        log.info("Installed new snapshot (%d KB)", len(response.content) // 1024)
        return True


def _refresh_loop() -> None:
    while True:
        time.sleep(config.DATA_REFRESH_MINUTES * 60)
        try:
            sync_once()
        except Exception as exc:
            _state["last_error"] = str(exc)
            log.warning("Snapshot refresh failed: %s", exc)


def start() -> None:
    if not config.DATA_URL:
        return
    _state["enabled"] = True
    try:
        sync_once()
    except Exception as exc:
        _state["last_error"] = str(exc)
        log.warning("Initial snapshot download failed: %s", exc)
    threading.Thread(target=_refresh_loop, daemon=True, name="snapshot-sync").start()
