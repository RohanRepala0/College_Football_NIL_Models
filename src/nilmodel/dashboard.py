"""Data files for the College Athlete Pay Benchmarks dashboard.

`nil dashboard-data` writes the JSON files to data/dashboard/, one per dashboard source: the
published percentiles of the latest releases (cohorts), the benchmark at every percentile (curves),
the benchmark's validation, and the releases on file. Upload them to the dashboard after a new release.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

from . import benchmark as bm
from . import config
from .csc import PERCENTILES


REPORT_LABELS = {"revenue_share": "Revenue share", "nil_go": "NIL Go"}
POPULATION_LABELS = {"paid": "Paid athletes", "all_rostered": "Everyone rostered", "deal_holders": "Athletes with a deal"}
TEST_LABELS = {"cross": "With $0 placed by a Without $0 fit", "loo_interior": "Leave one out, interior",
               "loo_tail": "Leave one out, tail"}


def _key(report, gender, sport, position, cohort, population) -> str:
    return "|".join([report, gender, sport, position, cohort, population])


def _clean(v):
    """A JSON-ready scalar: missing values (None, NaN, pandas NA) as None, numpy numbers as Python ones."""
    if v is None or pd.isna(v):
        return None
    return v.item() if hasattr(v, "item") else v


def build(con: duckdb.DuckDBPyConnection) -> dict[str, list[dict]]:
    cells = ", ".join(f"max(value_usd) FILTER (WHERE percentile = {p}) AS p{p}" for p in sorted(PERCENTILES))
    wide = con.execute(f"""
        SELECT report, gender, sport, position, cohort, a4, population, n, n_text, {cells}, window_label,
               CAST(window_start AS VARCHAR) AS window_start, CAST(window_end AS VARCHAR) AS window_end,
               left(payload_sha256, 12) AS release
        FROM csc_latest GROUP BY ALL
        ORDER BY report, gender, sport, position, cohort, population""").df()
    cohorts = [{"id": _key(r.report, r.gender, r.sport, r.position, r.cohort, r.population),
                "report_label": REPORT_LABELS[r.report], "population_label": POPULATION_LABELS[r.population],
                **{k: _clean(v) for k, v in r._asdict().items() if k != "Index"}}
               for r in wide.itertuples()]

    df = con.execute("SELECT * FROM csc_latest").df()
    curves = []
    for c in bm.calibrated_curves(df)[0]:
        if not c.fitted:
            continue
        k = c.key
        q_lo, q_hi = c.knots[0][0], c.knots[-1][0]
        pops = [(c.population, 0.0, q_lo, q_hi, c.n)]
        if c.zero_share is not None:
            z = c.zero_share
            pops.append(("all_rostered", z, z + (1 - z) * q_lo, z + (1 - z) * q_hi, c.n_all))
        for pop, zero, lo, hi, n in pops:
            curves.append({"id": _key(k.report, k.gender, k.sport, k.position, k.cohort, pop), "report": k.report,
                           "gender": k.gender, "sport": k.sport, "position": k.position, "cohort": k.cohort,
                           "population": pop, "n": n, "method": c.method, "top_tail_mult": c.top_mult,
                           "zero_pct": round(100 * zero, 2), "pub_lo": round(100 * lo, 2), "pub_hi": round(100 * hi, 2),
                           "values": [round(bm.value_at(c, p, pop)[0], 2) for p in range(1, 100)]})

    summary = bm.summarize(bm.validate(df))
    validation = [{"id": f"{r.report}|{r.test}|{r.method}", "report": r.report, "test": r.test, "method": r.method,
                   "report_label": REPORT_LABELS[r.report], "test_label": TEST_LABELS[r.test],
                   "points": int(r.points), "mean": round(r.mean, 2), "median": round(r.median, 2),
                   "p90": round(r.p90, 2)} for r in summary.itertuples()]

    releases = [{"id": f"{r[0]}|{r[1]}", "report": r[0], "release": r[1], "first_seen": r[2], "cohorts": r[3],
                 "archive": Path(r[4]).name}
                for r in con.execute("""SELECT report, left(payload_sha256, 12), strftime(first_seen_at, '%Y-%m-%d'),
                                               n_cohorts, archive_path FROM csc_releases
                                        ORDER BY report, first_seen_at""").fetchall()]
    out = {"cohorts": cohorts, "curves": curves, "validation": validation, "releases": releases,
           "totals": totals(df)}
    surplus = sorted((config.DATA_DIR / "players").glob("surplus_*.csv"))
    if surplus:                     # team totals from `nil surplus`, newest season
        from .triangulate import CAP_CALENDAR_2026

        t = pd.read_csv(surplus[-1])
        out["rosters"] = [{"id": r.team, "team": r.team, "conference": r.conference, "players": int(r.players),
                           "value": round(r.value), "low": round(r.low), "high": round(r.high),
                           "points": round(r.points, 2), "on_field_value": round(r.on_field_value),
                           "surplus": round(r.surplus), "points_per_million": round(r.points_per_million, 3),
                           "sp_rating": round(r.sp_rating, 1), "cap": CAP_CALENDAR_2026}
                          for r in t.itertuples()]
    return out


def totals(df: pd.DataFrame) -> list[dict]:
    """A4 football revenue share per program from the triangulation: the floor the percentiles imply with no
    model, its share of the calendar-2026 cap, and the A4 quarterback 99th percentile under the fitted tail
    and under the tail calibrated to the cap."""
    from . import triangulate as tri

    pp = tri.per_program(tri.roll_up(tri.cohort_totals(df)))
    cal = tri.calibrate(df)
    mult = float(cal[(cal.report == "revenue_share") & (cal.case == "central")].tail_mult.iloc[0])
    qb = bm.find(bm.curves(df)[0], "revenue_share", "Football", "Quarterback", "A4")
    return [{"id": "revenue_share|A4", "report": "revenue_share", "cohort": "A4", "programs": pp["programs"],
             "rostered_per_program": round(pp["rostered_per_program"], 1), "floor_per_program": round(pp["floor"]),
             "floor_cap_share": round(pp["floor_cap_share"], 4), "cap": tri.CAP_CALENDAR_2026,
             "tail_mult": round(mult, 4), "qb_p90": dict(qb.published[qb.population]).get(90),
             "qb_p99_fitted": round(tri.tail_value(qb, 99, 1.0)), "qb_p99_calibrated": round(tri.tail_value(qb, 99, mult))}]


def export(con: duckdb.DuckDBPyConnection, out_dir: Path | None = None) -> list[Path]:
    out_dir = out_dir or config.DATA_DIR / "dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, rows in build(con).items():
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(rows, separators=(",", ":"), sort_keys=True))
        paths.append(path)
    return paths
