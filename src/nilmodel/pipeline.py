"""The capture pipeline, run daily by .github/workflows/capture.yml.

1. Load every archived release (data/csc/releases/), so a fresh checkout knows what it has seen.
2. Fetch both CSC pages. A payload not seen before is a new release: archived, then stored. The same for every
   NIL Data Report (data/csc/nil_data/), whose newest period table is exported to data/csc/nil_data_periods.csv.
3. Check the latest release of each report and fit the offer benchmark to it.
4. Only when something is new (or on request), rewrite the exports, the release report and the
   dashboard's data files. A day with no change therefore commits nothing.
"""

from __future__ import annotations

import duckdb

from . import benchmark, config, csc, dashboard, nil_data, reports
from .fetch import Fetcher


def refresh(con: duckdb.DuckDBPyConnection, fetcher: Fetcher | None = None, archive_dir=None,
            export: bool = False) -> dict:
    archive_dir = archive_dir or csc.ARCHIVE_DIR
    archived = csc.ingest_archive(con, archive_dir)
    fetched = csc.ingest(con, fetcher, fresh=True, archive_dir=archive_dir) if fetcher else []
    nil_dir = nil_data.ARCHIVE_DIR if archive_dir == csc.ARCHIVE_DIR else archive_dir.parent / "nil_data"
    nil_data.ingest_archive(con, nil_dir)
    nil_new = [r for r in (nil_data.capture(con, fetcher, nil_dir) if fetcher and nil_data_enabled(fetcher) else []) if r["new"]]
    files = []
    if nil_new or export:           # before the curves: the NIL tail calibration reads this file
        files.append(nil_data.export_periods(con, nil_dir.parent / "nil_data_periods.csv"))
    latest = dict(con.execute("SELECT DISTINCT report, left(payload_sha256, 12) FROM csc_latest").fetchall())

    issues, reported = [], set()
    for r in reversed(archived + fetched):          # the newest parse of each report's latest release
        if latest.get(r["report"]) == r["release"] and r["report"] not in reported:
            reported.add(r["report"])
            issues += r["issues"]
    df = con.execute("SELECT * FROM csc_latest").df()
    issues += csc.check(df)
    curves, curve_issues = benchmark.calibrated_curves(df)
    issues += curve_issues
    benchmark.store(con, curves)

    new = [r for r in fetched if r["new"]]
    if new or nil_new or export:
        files += [csc.export_latest(con),
                 benchmark.export(con, config.DATA_DIR / "benchmark" / "curves.csv"),
                 reports.release_report(con, issues, benchmark.validate(df), curves),
                 *dashboard.export(con)]
    return {"archived": archived, "fetched": fetched, "new": new, "nil_data_new": nil_new, "issues": issues, "files": files}


def nil_data_enabled(fetcher) -> bool:
    """The real fetcher captures NIL Data Reports; a test fetcher serving only the two pay pages doesn't, unless it
    sets `nil_data = True`."""
    return getattr(fetcher, "nil_data", isinstance(fetcher, Fetcher))
