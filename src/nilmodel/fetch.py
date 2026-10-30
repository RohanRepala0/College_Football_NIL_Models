"""Polite HTTP fetching with immutable raw snapshots.

Every response is written to data/raw/<source>/<YYYY-MM-DD>/ and recorded in `raw_snapshots`.
Nothing is overwritten. Without fresh=True the newest snapshot on disk is reused.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import duckdb
import httpx

from . import config
from .db import utcnow


def _slug(url: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._=-]+", "_", re.sub(r"^https?://", "", url)).strip("_")
    return f"{stem[:120]}_{hashlib.sha256(url.encode()).hexdigest()[:10]}"


@dataclass
class Snapshot:
    body: bytes
    fetched_at: datetime
    path: Path
    url: str


class Fetcher:
    def __init__(self, con: duckdb.DuckDBPyConnection, raw_dir: Path | None = None,
                 client: httpx.Client | None = None, min_interval: float = 1.0):
        self.con = con
        self.raw_dir = raw_dir or config.RAW_DIR
        self.client = client or httpx.Client(timeout=config.TIMEOUT_SECONDS, follow_redirects=True,
                                             headers={"User-Agent": config.USER_AGENT})
        self.min_interval = min_interval
        self._last_request = 0.0

    def cached(self, url: str) -> Snapshot | None:
        row = self.con.execute("SELECT path_on_disk, fetched_at FROM raw_snapshots WHERE url = ? "
                               "ORDER BY fetched_at DESC LIMIT 1", [url]).fetchone()
        if row and Path(row[0]).exists():
            return Snapshot(Path(row[0]).read_bytes(), row[1], Path(row[0]), url)
        return None

    def fetch(self, source: str, url: str, fresh: bool = False, ext: str = "txt") -> Snapshot:
        snap = None if fresh else self.cached(url)
        if snap is not None:
            return snap
        wait = self.min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        resp = self.client.get(url)
        self._last_request = time.monotonic()
        resp.raise_for_status()
        fetched_at = utcnow()
        out_dir = self.raw_dir / source / fetched_at.strftime("%Y-%m-%d")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{_slug(url)}_{fetched_at.strftime('%H%M%S%f')}.{ext}"
        out.write_bytes(resp.content)
        self.con.execute("INSERT INTO raw_snapshots VALUES (?, ?, ?, ?, ?)",
                         [source, url, fetched_at, str(out), hashlib.sha256(resp.content).hexdigest()])
        return Snapshot(resp.content, fetched_at, out, url)
