"""The CSC's NIL Data Reports: deal counts and dollars cleared (and not cleared) through NIL Go.

A report is a WordPress post under /nil-data-report/, listed at /news/nil-data-reports/, published roughly every
two months. Recent reports carry two tables with a row per period since NIL Go launched: deals and value cleared
and not cleared, and cleared deals split into Associated (school-connected entities such as collectives) and
Non-Associated. Older reports show only headline cards. Every report is captured like the pay pages: its parsed
content is hashed, archived under data/csc/nil_data/ and stored with first and last sightings, so a correction
becomes a new version instead of overwriting the old one.

The period series used downstream is the table of the newest report (`latest_periods`), exported to
data/csc/nil_data_periods.csv. These are all-sports totals; nothing here is split by sport, and nothing here is
ever combined with revenue share.
"""

from __future__ import annotations

import gzip
import hashlib
import html as htmllib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from . import config
from .fetch import Fetcher

LISTING_URL = "https://www.collegesportscommission.org/news/nil-data-reports/"
ARCHIVE_DIR = config.DATA_DIR / "csc" / "nil_data"
PERIODS_CSV = config.DATA_DIR / "csc" / "nil_data_periods.csv"
LAUNCH = date(2025, 6, 11)                     # NIL Go opened June 11, 2025
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
FIELDS = ["cleared_deals", "cleared_value", "not_cleared_deals", "not_cleared_value",
          "associated_deals", "associated_value", "non_associated_deals", "non_associated_value"]


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def money(s: str) -> float:
    """'$127.21M' -> 127210000.0; K, M and B suffixes."""
    m = re.fullmatch(r"\$?\s*([\d,]+(?:\.\d+)?)\s*([KMB])?", s.strip(), re.I)
    if not m:
        raise ValueError(f"not a dollar amount: {s!r}")
    return round(float(m.group(1).replace(",", "")) * {"K": 1e3, "M": 1e6, "B": 1e9, None: 1}[(m.group(2) or "").upper() or None], 2)


def count(s: str) -> int:
    return int(s.replace(",", "").strip())


def _month_day(s: str) -> tuple[int, int, int | None]:
    m = re.fullmatch(r"([A-Za-z]+)\.?\s+(\d{1,2})(?:,\s*(\d{4}))?", s.strip())
    if not m or m.group(1)[:3].lower() not in MONTHS:
        raise ValueError(f"not a date: {s!r}")
    return MONTHS[m.group(1)[:3].lower()], int(m.group(2)), int(m.group(3)) if m.group(3) else None


def period_dates(label: str) -> tuple[date, date]:
    """'Sept. 1 – Oct. 31, 2026' -> (2026-09-01, 2026-10-31); 'Launch – Dec. 31, 2025' starts at NIL Go's launch."""
    left, right = [p.strip() for p in re.split(r"\s*[–—-]\s*", label, maxsplit=1)]
    em, ed, ey = _month_day(right)
    if ey is None:
        raise ValueError(f"no year in {label!r}")
    end = date(ey, em, ed)
    if left.lower() == "launch":
        return LAUNCH, end
    sm, sd, sy = _month_day(left)
    return date(sy or (ey if sm <= em else ey - 1), sm, sd), end


def report_links(listing_html: str) -> list[tuple[str, str]]:
    """(title, url) of every report linked from the listing, newest first, without duplicates."""
    titles: dict[str, str] = {}
    for url, inner in re.findall(r'<a[^>]+href="(https://www\.collegesportscommission\.org/nil-data-report/[^"#?]+/)"[^>]*>(.*?)</a>',
                                 listing_html, re.S):
        title = _text(inner)
        if url not in titles or (title and titles[url].lower() in ("", "read more") and title.lower() != "read more"):
            titles[url] = title
    return [(t, u) for u, t in titles.items()]


def _rows(table: str) -> list[list[str]]:
    return [[_text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)] for tr in re.findall(r"<tr.*?</tr>", table, re.S)]


def parse_report(page: str) -> dict:
    """Title, the 'current as of' date, registered users, and the period tables when the report has them."""
    title = _text(m.group(1)) if (m := re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)) else ""
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    text = _text(body.replace("<", " <"))
    as_of = None
    if m := re.search(r"current as of\s+([A-Z][a-z]+\.?\s+\d{1,2},\s*\d{4})", text):
        mo, d, y = _month_day(m.group(1))
        as_of = date(y, mo, d).isoformat()
    users = {}
    for key, label in (("student_athletes", "Student-Athlete Users"), ("institutions", "Institution Users"),
                       ("representatives", "Representative Users")):
        if m := re.search(r"([\d,]{3,})\s+" + label, text):
            users[key] = count(m.group(1))
    periods: dict[str, dict] = {}
    for table in re.findall(r"<table.*?</table>", page, re.S):
        rows = _rows(table)
        head = " ".join(" ".join(r) for r in rows[:2])
        kind = "associated" if "Associated" in head else "cleared" if "Not Cleared" in head else None
        if kind is None:
            continue
        cols = ["associated_deals", "associated_value", "non_associated_deals", "non_associated_value"] if kind == "associated" \
            else ["cleared_deals", "cleared_value", "not_cleared_deals", "not_cleared_value"]
        for r in rows:
            if len(r) != 5 or not r[0] or r[0].lower().startswith("total") or not re.search(r"\d", r[1]):
                continue
            start, end = period_dates(r[0])
            p = periods.setdefault(r[0], {"period": r[0], "start": start.isoformat(), "end": end.isoformat()})
            p.update({cols[0]: count(r[1]), cols[1]: money(r[2]), cols[2]: count(r[3]), cols[3]: money(r[4])})
    return {"title": title, "as_of": as_of, "users": users,
            "periods": sorted(periods.values(), key=lambda p: p["start"])}


def content_sha256(parsed: dict) -> str:
    return hashlib.sha256(json.dumps(parsed, sort_keys=True).encode()).hexdigest()


def _slug(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def _ensure(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""CREATE TABLE IF NOT EXISTS nil_data_reports (
        url VARCHAR, title VARCHAR, payload_sha256 VARCHAR, as_of DATE, first_seen_at TIMESTAMPTZ,
        last_seen_at TIMESTAMPTZ, archive_path VARCHAR, n_periods INTEGER)""")
    con.execute("""CREATE TABLE IF NOT EXISTS nil_data_periods (
        url VARCHAR, payload_sha256 VARCHAR, period VARCHAR, period_start DATE, period_end DATE,
        cleared_deals BIGINT, cleared_value DOUBLE, not_cleared_deals BIGINT, not_cleared_value DOUBLE,
        associated_deals BIGINT, associated_value DOUBLE, non_associated_deals BIGINT, non_associated_value DOUBLE)""")


def store(con: duckdb.DuckDBPyConnection, url: str, parsed: dict, seen_at: datetime, archive_dir: Path = ARCHIVE_DIR) -> dict:
    """Record a sighting. New content is a new version: archived (content-addressed, byte-stable) and stored."""
    _ensure(con)
    sha = content_sha256(parsed)
    prev = con.execute("SELECT first_seen_at, last_seen_at FROM nil_data_reports WHERE url = ? AND payload_sha256 = ?",
                       [url, sha]).fetchone()
    first, last = (min(prev[0], seen_at), max(prev[1], seen_at)) if prev else (seen_at, seen_at)
    existing = sorted(archive_dir.glob(f"{_slug(url)}_*_{sha[:12]}.json.gz")) if archive_dir.exists() else []
    path = existing[0] if existing else archive_dir / f"{_slug(url)}_{first:%Y-%m-%d}_{sha[:12]}.json.gz"
    if not existing:
        archive_dir.mkdir(parents=True, exist_ok=True)
        envelope = {"url": url, "first_seen_at": first.isoformat(), "payload_sha256": sha, "payload": parsed}
        path.write_bytes(gzip.compress(json.dumps(envelope, sort_keys=True, indent=1).encode(), mtime=0))
    con.execute("DELETE FROM nil_data_reports WHERE url = ? AND payload_sha256 = ?", [url, sha])
    con.execute("INSERT INTO nil_data_reports VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [url, parsed["title"], sha, parsed["as_of"], first, last, str(path), len(parsed["periods"])])
    con.execute("DELETE FROM nil_data_periods WHERE url = ? AND payload_sha256 = ?", [url, sha])
    for p in parsed["periods"]:
        con.execute("INSERT INTO nil_data_periods VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [url, sha, p["period"], p["start"], p["end"], *[p.get(f) for f in FIELDS]])
    return {"url": url, "title": parsed["title"], "release": sha[:12], "new": prev is None, "periods": len(parsed["periods"])}


def ingest_archive(con: duckdb.DuckDBPyConnection, archive_dir: Path = ARCHIVE_DIR) -> list[dict]:
    out = []
    for path in sorted(archive_dir.glob("*.json.gz")) if archive_dir.exists() else []:
        env = json.loads(gzip.decompress(path.read_bytes()))
        r = store(con, env["url"], env["payload"], datetime.fromisoformat(env["first_seen_at"]), archive_dir)
        out.append({**r, "new": False})
    return out


def capture(con: duckdb.DuckDBPyConnection, fetcher: Fetcher, archive_dir: Path = ARCHIVE_DIR) -> list[dict]:
    """Fetch the listing and every report on it; store each one's content."""
    listing = fetcher.fetch("csc_nil_data", LISTING_URL, fresh=True, ext="html").body.decode("utf-8", "replace")
    links = report_links(listing)
    if not links:
        raise RuntimeError("the NIL Data Reports listing links no reports; its layout may have changed")
    seen_at = datetime.now(timezone.utc)
    return [store(con, url, parse_report(fetcher.fetch("csc_nil_data", url, fresh=True, ext="html").body.decode("utf-8", "replace")), seen_at, archive_dir)
            for _, url in links]


def latest_periods(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """The period table of the newest report that has one: the one covering the latest period, then by its
    'current as of' date (which a page can get wrong: July-August 2026 says July 1), then first sighting."""
    _ensure(con)
    return con.execute("""
        WITH newest AS (
            SELECT r.url, r.payload_sha256, r.as_of FROM nil_data_reports r
            JOIN (SELECT url, payload_sha256, max(period_end) AS covers FROM nil_data_periods GROUP BY ALL) c USING (url, payload_sha256)
            ORDER BY c.covers DESC, r.as_of DESC NULLS LAST, r.first_seen_at DESC LIMIT 1)
        SELECT p.period, p.period_start, p.period_end, p.cleared_deals, p.cleared_value, p.not_cleared_deals,
               p.not_cleared_value, p.associated_deals, p.associated_value, p.non_associated_deals,
               p.non_associated_value, n.as_of, p.url AS source_url
        FROM nil_data_periods p JOIN newest n USING (url, payload_sha256)
        ORDER BY p.period_start""").df()


def export_periods(con: duckdb.DuckDBPyConnection, path: Path = PERIODS_CSV) -> Path:
    df = latest_periods(con)
    for c in ("period_start", "period_end", "as_of"):
        df[c] = pd.to_datetime(df[c]).dt.strftime("%Y-%m-%d")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
