"""DuckDB schema and helpers.

Three groups of tables: `raw_snapshots` (every download), the CSC releases and their percentile cells
(`csc_*`), and the offer benchmark fitted to them (`benchmark_*`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_snapshots (
    source        VARCHAR NOT NULL,
    url           VARCHAR NOT NULL,
    fetched_at    TIMESTAMPTZ NOT NULL,
    path_on_disk  VARCHAR NOT NULL,
    sha256        VARCHAR NOT NULL
);

-- A release is one distinct decoded payload; refetching an unchanged page only moves last_seen_at.
CREATE TABLE IF NOT EXISTS csc_releases (
    report          VARCHAR NOT NULL CHECK (report IN ('nil_go', 'revenue_share')),
    payload_sha256  VARCHAR NOT NULL,
    url             VARCHAR NOT NULL,
    first_seen_at   TIMESTAMPTZ NOT NULL,
    last_seen_at    TIMESTAMPTZ NOT NULL,
    archive_path    VARCHAR NOT NULL,
    n_cohorts       INTEGER NOT NULL
);

-- One row per published percentile cell. Long format: a cohort is
-- (report, gender, sport, position, cohort, population, window_label).
CREATE TABLE IF NOT EXISTS csc_percentiles (
    report          VARCHAR NOT NULL CHECK (report IN ('nil_go', 'revenue_share')),
    payload_sha256  VARCHAR NOT NULL,
    gender          VARCHAR NOT NULL CHECK (gender IN ('men', 'women', 'mixed')),
    sport           VARCHAR NOT NULL,
    position        VARCHAR NOT NULL,
    cohort          VARCHAR NOT NULL,
    a4              BOOLEAN,
    population      VARCHAR NOT NULL CHECK (population IN ('all_rostered', 'paid', 'deal_holders')),
    n               INTEGER,
    n_text          VARCHAR,
    percentile      INTEGER NOT NULL,
    value_usd       DOUBLE,
    min_n           INTEGER,
    window_start    DATE,
    window_end      DATE,
    as_of           DATE,
    window_label    VARCHAR,
    source_ref      VARCHAR NOT NULL
);

CREATE OR REPLACE VIEW csc_latest AS
SELECT p.* FROM csc_percentiles p
JOIN (SELECT report, arg_max(payload_sha256, first_seen_at) AS payload_sha256
      FROM csc_releases GROUP BY report) r USING (report, payload_sha256);

-- Offer benchmark (benchmark.py): one fitted curve per cohort of a release ...
CREATE TABLE IF NOT EXISTS benchmark_fits (
    payload_sha256  VARCHAR NOT NULL,
    report          VARCHAR NOT NULL,
    gender          VARCHAR NOT NULL,
    sport           VARCHAR NOT NULL,
    position        VARCHAR NOT NULL,
    cohort          VARCHAR NOT NULL,
    window_label    VARCHAR,
    population      VARCHAR NOT NULL,      -- the positive part the curve describes: paid | deal_holders
    n               INTEGER,
    n_all           INTEGER,               -- revenue share: everyone rostered, when published
    zero_share      DOUBLE,                -- revenue share: 1 - n / n_all
    method          VARCHAR NOT NULL,      -- pchip | linear | lognormal | bracket_only
    n_knots         INTEGER NOT NULL,
    tail_slope      DOUBLE,                -- log dollars per normal score beyond the published percentiles
    top_tail_mult   DOUBLE,                -- scale on that slope past the top point (calibrated football tails)
    knots           VARCHAR NOT NULL       -- JSON [[q, dollars, source], ...]
);

-- ... and its value at every whole percentile, per population.
CREATE TABLE IF NOT EXISTS benchmark_curves (
    payload_sha256  VARCHAR NOT NULL,
    report          VARCHAR NOT NULL,
    gender          VARCHAR NOT NULL,
    sport           VARCHAR NOT NULL,
    position        VARCHAR NOT NULL,
    cohort          VARCHAR NOT NULL,
    window_label    VARCHAR,
    population      VARCHAR NOT NULL,      -- paid | all_rostered | deal_holders
    percentile      INTEGER NOT NULL,      -- 1 to 99
    value_usd       DOUBLE NOT NULL,
    extrapolated    BOOLEAN NOT NULL       -- beyond the published percentiles
);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def connect(path: Path | str | None = None) -> duckdb.DuckDBPyConnection:
    path = Path(path) if path is not None else config.DB_PATH
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute("SET TimeZone = 'UTC'")
    return con


def init_db(con: duckdb.DuckDBPyConnection) -> list[str]:
    con.execute(SCHEMA)
    con.execute("ALTER TABLE benchmark_fits ADD COLUMN IF NOT EXISTS top_tail_mult DOUBLE")
    return sorted(r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall())


def insert_df(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> int:
    """Append rows, matching columns by name."""
    if df.empty:
        return 0
    cols = ", ".join(df.columns)
    con.register("_insert_df", df)
    try:
        con.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM _insert_df")
    finally:
        con.unregister("_insert_df")
    return len(df)
