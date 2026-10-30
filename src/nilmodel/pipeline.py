"""The capture pipeline, run daily by .github/workflows/capture.yml.

1. Load every archived release (data/csc/releases/), so a fresh checkout knows what it has seen.
2. Fetch both CSC pages. A payload not seen before is a new release: archived, then stored.
3. Check the latest release of each report and fit the offer benchmark to it.
4. Only when something is new (or on request), rewrite the exports and the release report. A day
   with no change therefore commits nothing.
"""

from __future__ import annotations

import duckdb

from . import benchmark, config, csc, reports
from .fetch import Fetcher


def refresh(con: duckdb.DuckDBPyConnection, fetcher: Fetcher | None = None, archive_dir=None,
            export: bool = False) -> dict:
    archive_dir = archive_dir or csc.ARCHIVE_DIR
    archived = csc.ingest_archive(con, archive_dir)
    fetched = csc.ingest(con, fetcher, fresh=True, archive_dir=archive_dir) if fetcher else []
    latest = dict(con.execute("SELECT DISTINCT report, left(payload_sha256, 12) FROM csc_latest").fetchall())

    issues, reported = [], set()
    for r in reversed(archived + fetched):          # the newest parse of each report's latest release
        if latest.get(r["report"]) == r["release"] and r["report"] not in reported:
            reported.add(r["report"])
            issues += r["issues"]
    df = con.execute("SELECT * FROM csc_latest").df()
    issues += csc.check(df)
    curves, curve_issues = benchmark.curves(df)
    issues += curve_issues
    benchmark.store(con, curves)

    new = [r for r in fetched if r["new"]]
    files = []
    if new or export:
        files = [csc.export_latest(con),
                 benchmark.export(con, config.DATA_DIR / "benchmark" / "curves.csv"),
                 reports.release_report(con, issues, benchmark.validate(df), curves)]
    return {"archived": archived, "fetched": fetched, "new": new, "issues": issues, "files": files}
