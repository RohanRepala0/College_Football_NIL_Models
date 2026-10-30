"""The release report: what is on file, the checks, football in each report, and the benchmark's validation.

Deterministic (no run timestamps), so rewriting it for an unchanged release changes nothing in git.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import benchmark as bm
from . import config
from .csc import FOOTBALL_POSITIONS

POPULATIONS = {"paid": "paid athletes", "all_rostered": "everyone rostered", "deal_holders": "athletes with a deal"}
EXAMPLES = [("revenue_share", "Football", "Quarterback", "A4", 400_000),
            ("revenue_share", "Football", "Offensive Lineman", "Non-A4", 25_000),
            ("nil_go", "Football", "Wide Receiver", "A4", 50_000),
            ("nil_go", "Football", "Running Back", "Non-A4", 1_500)]


def _md(df: pd.DataFrame, floatfmt: str = ".1f") -> str:
    return df.to_markdown(index=False, floatfmt=floatfmt) + "\n" if len(df) else "_none_\n"


def _usd(v) -> str:
    return "" if pd.isna(v) else f"${v:,.0f}"


def ordinal(x: float) -> str:
    n = int(round(x))
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def estimate(b: bm.Benchmark) -> str:
    if b.low is None:
        return "-"
    text = ordinal(b.low) if b.high - b.low < 1 else f"{ordinal(b.low)} to {ordinal(b.high)}"
    return text + (" (extrapolated)" if b.extrapolated else "")


def published(b: bm.Benchmark) -> str:
    if b.matches:
        m = b.matches
        return f"equals the {ordinal(m[0])}" if len(m) == 1 else f"equals the {ordinal(m[0])} to {ordinal(m[-1])}"
    lo, hi = b.bracket
    if lo == 0:
        return f"below the {ordinal(hi)}"
    if hi == 100:
        return f"above the {ordinal(lo)}"
    return f"between the {ordinal(lo)} and {ordinal(hi)}"


def benchmark_rows(results: list[bm.Benchmark]) -> list[dict]:
    return [{"report": b.key.report, "cohort": b.key.label().split(" · ", 1)[1], "among": POPULATIONS[b.population],
             "n": b.n, "amount": _usd(b.amount), "percentile": estimate(b), "published percentiles": published(b)}
            for b in results]


def _football(df: pd.DataFrame, report: str) -> pd.DataFrame:
    cells = (df[(df.report == report) & (df.sport == "Football")]
             .pivot_table(index=["cohort", "position", "population", "n"], columns="percentile",
                          values="value_usd", aggfunc="first").reset_index())
    cells["position"] = pd.Categorical(cells.position, list(FOOTBALL_POSITIONS), ordered=True)
    cells = cells.sort_values(["cohort", "position"])
    if report == "nil_go":
        return pd.DataFrame({"cut": cells.cohort, "position": cells.position.astype(str), "deal holders": cells.n,
                             "median": cells[50].map(_usd), "90th": cells[90].map(_usd)})
    allr = cells[cells.population == "all_rostered"].set_index(["cohort", "position"])
    paid = cells[cells.population == "paid"].set_index(["cohort", "position"])
    j = allr[["n"]].join(paid[["n", 50, 90]], rsuffix="_paid").reset_index()
    return pd.DataFrame({"cut": j.cohort, "position": j.position.astype(str), "rostered": j.n,
                         "paid share": (j.n_paid / j.n).map("{:.0%}".format),
                         "paid median": j[50].map(_usd), "paid 90th": j[90].map(_usd)})


def release_report(con, issues: list[dict], errors: pd.DataFrame, curves: list[bm.Curve],
                   path: Path | None = None) -> Path:
    releases = con.execute("""
        SELECT report, left(payload_sha256, 12) AS release, CAST(first_seen_at AS DATE) AS first_seen,
               n_cohorts AS cohorts, archive_path
        FROM csc_releases ORDER BY report, first_seen_at""").df()
    releases["archive_path"] = [Path(p).name for p in releases.archive_path]
    releases["first_seen"] = pd.to_datetime(releases.first_seen).dt.strftime("%Y-%m-%d")
    newest = releases.first_seen.max()
    df = con.execute("SELECT * FROM csc_latest").df()

    checks = pd.DataFrame(issues, columns=["check", "severity", "report", "key", "detail"])
    summary = bm.summarize(errors).pivot(index=["report", "test"], columns="method", values="mean").reset_index()
    fitted = pd.DataFrame([{"report": c.key.report, "curve": c.fitted} for c in curves])
    coverage = fitted.groupby("report").curve.agg(cohorts="count", with_curve="sum").reset_index()
    examples = []
    for report, sport, position, cohort, amount in EXAMPLES:
        try:
            examples += bm.benchmark(bm.find(curves, report, sport, position, cohort), amount)
        except LookupError:
            continue

    parts = [
        f"# CSC release, {newest}\n",
        "Written by `nil refresh` whenever a new release appears. Each report is read on its own; the two are "
        "never compared. Method and caveats: [`docs/BENCHMARK.md`](../docs/BENCHMARK.md), "
        "[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).\n",
        "## Releases on file\n", _md(releases),
        "## Checks\n", "All passed.\n" if checks.empty else _md(checks),
        "## Football: revenue share\n",
        "Payments in calendar 2026, including scheduled performance incentives. Medians and 90th percentiles are "
        "among paid athletes.\n", _md(_football(df, "revenue_share")),
        "## Football: NIL Go\n",
        "Full contracted value of third-party deals cleared Jan 1 to Sep 30, 2026, among athletes with at least "
        "one such deal.\n", _md(_football(df, "nil_go")),
        "## Offer benchmark: validation\n",
        f"Mean miss in percentile points when a published percentile is held out (`loo_*`) or, for revenue share, "
        f"when the With $0 table is placed using a curve fit to the Without $0 table alone (`cross`). The default "
        f"method is `{bm.METHOD}`.\n", _md(summary, ".2f"),
        "Cohorts with at least two published points get a curve; the rest get published brackets only.\n",
        _md(coverage),
        "## Offer benchmark: examples\n", _md(pd.DataFrame(benchmark_rows(examples))),
    ]
    path = path or config.REPORTS_DIR / f"release_{newest}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))
    return path
