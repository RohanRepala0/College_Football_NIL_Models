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


def triangulation_report(con, path: Path | None = None) -> Path:
    """What the latest release implies about football totals: hard floors, tail scenarios, and the tail
    calibrated to outside totals. Each report is totalled on its own."""
    from . import triangulate as tri

    df = con.execute("SELECT * FROM csc_latest").df()
    newest = con.execute("SELECT strftime(max(first_seen_at), '%Y-%m-%d') FROM csc_releases").fetchone()[0]
    rolled = tri.roll_up(tri.cohort_totals(df))
    pp = tri.per_program(rolled)

    def m(v):
        return "" if pd.isna(v) else f"${v / 1e6:,.1f}M"

    totals = pd.DataFrame({
        "report": rolled.report, "group": rolled.cohort, "athletes": rolled.athletes.astype(int),
        "floor (no model)": rolled.floor.map(m), "light tail (x0.5)": rolled.light.map(m),
        "fitted tail (x1.0)": rolled.fitted.map(m), "heavy tail (x1.5)": rolled.heavy.map(m)})
    cal = tri.calibrate(df)
    cal_table = pd.DataFrame({
        "report": cal.report, "assumption": cal.case, "football share": cal.assumed_share.map("{:.0%}".format),
        "target": cal.target.map(m), "flat-tail total": cal.flat_tail_total.map(m),
        "fitted-tail total": cal.fitted_total.map(m),
        "tail multiplier": ["below a flat tail" if pd.isna(v) else f"x{v:.2f}" for v in cal.tail_mult]})

    curves = bm.curves(df)[0]
    rows = []
    for report in ("revenue_share", "nil_go"):
        mult = cal[(cal.report == report) & (cal.case == "central")].tail_mult.iloc[0]
        for pos in ("Quarterback", "Wide Receiver", "Offensive Lineman", "Defensive Lineman"):
            c = bm.find(curves, report, "Football", pos, "A4")
            rows.append({"report": report, "A4 position": pos, "published 90th": m(dict(c.published[c.population]).get(90)),
                         "95th fitted": m(tri.tail_value(c, 95, 1.0)), "95th calibrated": m(tri.tail_value(c, 95, mult)),
                         "99th fitted": m(tri.tail_value(c, 99, 1.0)), "99th calibrated": m(tri.tail_value(c, 99, mult))})

    parts = [
        f"# Triangulation, release {newest}\n",
        "What the published percentiles imply about football totals, first with no model and then with the "
        "benchmark curves. Revenue share and NIL Go are totalled separately and never added together. Method: "
        "[`docs/ESTIMATION.md`](../docs/ESTIMATION.md).\n",
        "## Hard floors\n",
        "Each athlete between two published percentiles is paid at least the lower of the two, so share x lower "
        "value, summed, is a floor that needs no model. Nothing caps the top 10%, so there is no matching ceiling.\n",
        f"- A4 football revenue share is at least **{m(pp['floor'])} per program** across the {pp['programs']} A4 "
        f"programs, **{pp['floor_cap_share']:.0%} of the calendar-2026 cap** (${tri.CAP_CALENDAR_2026 / 1e6:.2f}M, "
        "which also has to cover every other sport).",
        f"- The CSC counts {pp['rostered_per_program']:.0f} rostered football players per A4 program, above the "
        "105-player roster limit: everyone on a 2026 roster at any point in the calendar year is counted, so "
        "turnover adds names.\n",
        "## Totals under each tail\n",
        "Between published percentiles the curve is the benchmark's; past the 10th and 90th it is lognormal with "
        "the fitted slope times the multiplier.\n",
        _md(totals),
        f"Under the fitted tail, A4 football alone would take {pp['fitted_cap_share']:.0%} of the cap, and under "
        f"the heavy tail {pp['heavy_cap_share']:.0%}, which is impossible.\n",
        "## Tails calibrated to outside totals\n",
        *[f"- {note}" for note in tri.CONSTRAINT_NOTES],
        "\nThe multiplier is solved so the football total matches the target. \"Below a flat tail\" means even "
        "paying everyone in the top 10% exactly the published 90th overshoots, so that assumption is ruled out.\n",
        _md(cal_table),
        "## What calibration changes at the top\n",
        "Dollars past the published 90th, A4 football, at the central assumption. The fitted tail is what the "
        "benchmark extrapolates with today.\n",
        _md(pd.DataFrame(rows)),
    ]
    path = path or config.REPORTS_DIR / f"triangulation_{newest}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))
    return path


def _pct_signed(v: float) -> str:
    return "0%" if abs(v) < 0.005 else f"{v:+.0%}"


def claims_report(con, claims_path: Path, path: Path | None = None) -> Path:
    """Credibility of a claims file against the latest release: per-source summary, tail counts,
    order-test flags and source bias."""
    from . import claims as cl

    df = con.execute("SELECT * FROM csc_latest").df()
    curves = bm.curves(df)[0]
    claims, issues = cl.load(claims_path)
    placed = cl.place(claims, curves)
    tails = cl.lenient_tails(df)
    order = cl.order_test(placed, curves, tails)
    bias = cl.source_bias(claims)
    counts = cl.tail_counts(placed, df)
    summary = cl.summary(placed, order, bias)
    if len(summary):
        summary["flagged_share"] = summary.flagged_share.map(lambda v: "" if pd.isna(v) else f"{v:.0%}")
        summary["bias"] = summary.bias.map(lambda v: "" if pd.isna(v) else _pct_signed(v))
    flagged = order[order.flagged].assign(value=lambda d: d.value.map(_usd),
                                          p_value=lambda d: d.p_value.map(lambda v: "<0.001" if v < 0.001 else f"{v:.3f}"))
    over = counts[counts.excess > 0].assign(threshold=lambda d: d.threshold.map(_usd))
    unplaced = placed[~placed.placed][["claim_id", "source", "report", "position", "cohort", "why"]]
    parts = [
        f"# Claims check: {claims_path.name}\n",
        f"{len(claims)} claims read, {len(issues)} rejected. Each claim is read against one CSC report; "
        "revenue-share amounts are per year, NIL amounts are full contract value. Method: "
        "[`docs/ESTIMATION.md`](../docs/ESTIMATION.md).\n",
        "## By source\n", _md(summary),
        "## Provable overstatements (no model)\n",
        "Distinct claimed athletes above a published percentile, against the most the cohort can have there. "
        "Each excess is a floor on how many of those claims overstate pay or count money the report doesn't.\n",
        _md(over),
        "## Flagged by the order test\n",
        f"Claims that even the cohort's k-th best-paid athlete is unlikely (p < {cl.ALPHA}) to reach, under the "
        "heaviest football tail the outside totals allow "
        f"(x{tails.get('revenue_share', 1):.2f} revenue share, x{tails.get('nil_go', 1):.2f} NIL Go).\n",
        _md(flagged[["claim_id", "source", "position", "cohort", "value", "k", "n", "p_value"]]),
        "## Source bias\n",
        "From athletes reported by more than one source: each source's typical over- or under-statement, anchored "
        "to school records where they overlap.\n",
        _md(bias.assign(bias=bias.bias.map(_pct_signed), se=bias.se.map("{:.2f}".format)) if len(bias) else bias),
        "## Not placed\n", _md(unplaced),
        *([ "## Rejected rows\n", _md(pd.DataFrame(issues))] if issues else []),
    ]
    path = path or config.REPORTS_DIR / f"claims_{claims_path.stem}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))
    return path
