"""The release report: what is on file, the checks, football in each report, and the benchmark's validation.

Deterministic (no run timestamps), so rewriting it for an unchanged release changes nothing in git.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
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
        *[f"- {note}" for note in tri.constraint_notes(df)],
        "\nThe multiplier is solved so the football total matches the target. \"Below a flat tail\" means even "
        "paying everyone in the top 10% exactly the published 90th overshoots, so that assumption is ruled out.\n",
        _md(cal_table),
        *caps_section(df, cal),
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
    curves = bm.calibrated_curves(df)[0]
    claims, issues = cl.load(claims_path)
    placed = cl.place(claims, curves)
    high, central = cl.lenient_tails(df, "high"), cl.lenient_tails(df, "central")
    ev = cl.evidence(placed, curves, df)
    bias = cl.source_bias(claims)
    counts = cl.tail_counts(placed, df)
    summary = cl.summary(placed, ev, bias)
    if len(summary):
        summary["bias"] = summary.bias.map(lambda v: "" if pd.isna(v) else _pct_signed(v))
    pfmt = lambda v: "<0.001" if v < 0.001 else f"{v:.3f}"        # noqa: E731
    flagged = ev[ev.strong | ev.moderate].assign(
        value=lambda d: d.value.map(_usd), evidence=lambda d: np.where(d.strong, "strong", "moderate"),
        p_strong=lambda d: d.p_strong.map(pfmt), p_central=lambda d: d.p_central.map(pfmt))
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
        f"Claims that even the cohort's k-th best-paid athlete is unlikely (p < {cl.ALPHA}) to reach. **Strong**: "
        "fails under the most generous football tail the outside totals allow "
        f"(x{high.get('revenue_share', 1):.2f} revenue share, x{high.get('nil_go', 1):.2f} NIL Go). **Moderate**: "
        f"fails only under the central tail (x{central.get('revenue_share', 1):.2f}, x{central.get('nil_go', 1):.2f}).\n",
        _md(flagged[["claim_id", "source", "position", "cohort", "value", "k", "n", "evidence", "p_strong", "p_central"]]),
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


def simulation_report(con, seeds: tuple[int, ...] = (0, 1, 2), path: Path | None = None) -> Path:
    """The estimation and credibility methods on synthetic markets built from the real curves, where the
    truth is known."""
    from . import simulate as sim

    df = con.execute("SELECT * FROM csc_latest").df()
    newest = con.execute("SELECT strftime(max(first_seen_at), '%Y-%m-%d') FROM csc_releases").fetchone()[0]
    transports = sim.football_transports(df)
    mult = next(iter(transports.values())).tail_mult
    methods, cred = sim.run(df, seeds)
    order = ["features only", "+ claims as training labels", "+ claims as anchors", "+ anchors + school totals"]
    m = (methods.groupby(["scenario", "players", "method"], as_index=False)[["rank_corr", "median_log_error", "coverage_80"]]
         .mean())
    m["method"] = pd.Categorical(m.method, order, ordered=True)
    m = m.sort_values(["scenario", "players", "method"])
    table = pd.DataFrame({"features": m.scenario, "players": m.players, "method": m.method.astype(str),
                          "rank correlation": m.rank_corr.map("{:.3f}".format),
                          "typical miss": np.exp(m.median_log_error).map("x{:.2f}".format),
                          "80% interval covers": m.coverage_80.map("{:.0%}".format)})
    c = cred.groupby("source", as_index=False).agg(true_bias=("true_bias", "first"), mean=("estimated_bias", "mean"),
                                                   low=("estimated_bias", "min"), high=("estimated_bias", "max"),
                                                   claims=("claims", "sum"), strong=("strong", "sum"),
                                                   moderate=("moderate", "sum"))
    src = pd.DataFrame({"source": c.source, "true bias": c.true_bias.map(_pct_signed),
                        "estimated bias": c["mean"].map(_pct_signed),
                        "range over markets": [f"{_pct_signed(a)} to {_pct_signed(b)}" for a, b in zip(c.low, c.high)],
                        "claims": c.claims, "strong flags": c.strong, "moderate flags": c.moderate})

    def val(scen, players, method, col):
        return float(m[(m.scenario == scen) & (m.players == players) & (m.method == method)][col].iloc[0])

    lines = []
    for scen in sim.SCENARIOS:
        f, lab, anc, tot = (val(scen, "all", x, "rank_corr") for x in order)
        cf, ca = val(scen, "claimed", order[0], "median_log_error"), val(scen, "claimed", order[2], "median_log_error")
        da, dt = val(scen, "disclosed schools", order[2], "rank_corr"), val(scen, "disclosed schools", order[3], "rank_corr")
        lines.append(f"- **{scen.capitalize()}**: features alone rank pay at {f:.3f}. Training on the claims drops that "
                     f"to {lab:.3f}; anchoring on them keeps {anc:.3f} and cuts the typical miss for claimed players "
                     f"from x{np.exp(cf):.2f} to x{np.exp(ca):.2f}. School totals lift the disclosed schools from "
                     f"{da:.3f} to {dt:.3f} (all players {tot:.3f}).")
    world = sim.market(transports, seed=seeds[0])
    parts = [
        f"# Simulation, release {newest}\n",
        "Real individual pay is private, so the methods are tested on synthetic markets where it is known. Each "
        f"market has the CSC's {len(world['players']):,} rostered A4 football players by position, spread over "
        f"{tri_programs()} programs. A player's latent value is talent plus his school's spending effect plus "
        "noise, and his true revenue share is his position's quantile at that rank, so every position reproduces "
        f"the published percentiles, with the tail calibrated to the cap (x{mult:.2f}). The analyst sees two noisy "
        f"features, {len(world['disclosed'])} schools' disclosed totals, and claims about the best-paid players "
        f"from {len(sim.SOURCES)} sources with known biases. {len(seeds)} markets per scenario; method: "
        "[`docs/ESTIMATION.md`](../docs/ESTIMATION.md).\n",
        "## Estimating each player's pay\n",
        "Rank correlation is between the estimated and true pay rankings within each position. Typical miss is the "
        "median factor between estimate and truth (on 1 + pay, so an unpaid player estimated at $0 is exact).\n",
        _md(table, ".3f"),
        *lines,
        "\n## Checking sources\n",
        "Estimated bias comes from athletes reported by more than one source, anchored to school records. Strong "
        "flags fail the order test under the most generous tail the cap allows; moderate flags fail only under "
        "the central tail.\n",
        _md(src),
        "## Limits\n",
        "- The synthetic market is built to match what is published; how pay really depends on talent and school "
        "is assumed, and the features' quality is set by the scenario. Real features need the CFBD data.",
        "- Moderate inflation (+30%) is caught through overlapping sources, not by the aggregate tests; those catch "
        "only claims far beyond what the distribution allows.",
        "- The intervals cover the truth somewhat more often than 80%, so they are cautious.",
    ]
    path = path or config.REPORTS_DIR / f"simulation_{newest}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))
    return path


def tri_programs() -> int:
    from .triangulate import A4_FOOTBALL_PROGRAMS

    return A4_FOOTBALL_PROGRAMS


def rosters_report(con, season: int, table: pd.DataFrame, players: pd.DataFrame, path: Path | None = None) -> Path:
    """A4 roster market values: the roster layer checked against the CSC, feature coverage, and each
    program's value with its range. Team totals only; no individual estimates."""
    from . import players as pl
    from . import triangulate as tri

    published = con.execute("SELECT * FROM csc_latest").df()
    calls = con.execute("SELECT count(*) FROM raw_snapshots WHERE source = 'cfbd'").fetchone()[0]
    check = pl.roster_check(players, published)
    cov = players.groupby("group").agg(players=("id", "size"), rating=("rating", lambda s: s.notna().mean()),
                                       production=("production", lambda s: s.notna().mean()),
                                       transfers=("transfer", "mean")).reset_index()
    for col in ("rating", "production", "transfers"):
        cov[col] = cov[col].map("{:.0%}".format)

    def m(v):
        return f"${v / 1e6:.1f}M"

    teams = pd.DataFrame({
        "rank": range(1, len(table) + 1), "program": table.team, "conference": table.conference,
        "players": table.players, "market value": table.value.map(m),
        "80% range": [f"{m(a)} to {m(b)}" for a, b in zip(table.low, table.high)],
        "vs cap": (table.value / tri.CAP_CALENDAR_2026).map("{:.0%}".format),
        "top-5 share": table.top5_share.map("{:.0%}".format)})
    conf = table.groupby("conference").value.agg(programs="count", mean="mean", low="min", high="max").reset_index()
    for col in ("mean", "low", "high"):
        conf[col] = conf[col].map(m)
    over = int((table.value > tri.CAP_CALENDAR_2026).sum())
    parts = [
        f"# A4 roster market values, {season}\n",
        "What each A4 football roster would cost in revenue share if every player were paid his position's A4 "
        "market rate at his rank. The rates are the CSC's published distributions (with the cap-calibrated tail); "
        "the ranks come from public data. **This is not what a school spends**: it is the market price of the "
        "roster, the first half of a surplus-value comparison. Team totals only; individual estimates stay in "
        f"the local database. Data: CollegeFootballData, {calls} API calls. Method: "
        "[`docs/ESTIMATION.md`](../docs/ESTIMATION.md).\n",
        "## Rosters against the CSC\n",
        f"A4 players on {season} rosters by CSC group, against the CSC's count of everyone on a {season} roster "
        "during the calendar year. They agree within a few percent, except that the CSC leaves 162 players' "
        "positions unspecified and counts fewer defensive linemen.\n",
        _md(check),
        "## What ranks the players\n",
        "Within each group: last season's production (usage and expected points added on offense; tackles, "
        f"sacks, tackles for loss, pass breakups and interceptions on defense) {pl.WEIGHTS['production']:.0%}, "
        f"recruiting or portal rating {pl.WEIGHTS['rating']:.0%}, class year {pl.WEIGHTS['experience']:.0%}. "
        f"Groups without individual production (linemen on offense, specialists) use rating "
        f"{pl.WEIGHTS_NO_PRODUCTION['rating']:.0%} and class year {pl.WEIGHTS_NO_PRODUCTION['experience']:.0%}. "
        "These weights are a stated prior. A missing rating counts as the group's 10th percentile; no production "
        f"last season counts as the group's lowest. Ranks are treated as tracking pay at {pl.RANK_CORR}, inside "
        "the simulation's 0.43 to 0.66 range, and that uncertainty gives each program's range.\n",
        _md(cov),
        "## Market value by program\n",
        f"Average ${table.value.mean() / 1e6:.1f}M against a calendar-2026 cap of "
        f"${tri.CAP_CALENDAR_2026 / 1e6:.2f}M. {over} rosters would cost more than the cap at market rates, so "
        "their players must take less than market in revenue share or be paid through NIL.\n",
        _md(teams),
        "## By conference\n", _md(conf),
        "## Limits\n",
        "- Ranks come from public features with prior weights, not from contracts.",
        "- Transfers are matched to the portal by name and school; transfers from outside FBS have no production here.",
        "- Linemen on offense and specialists rank on rating and class year alone.",
        "- Rosters include walk-ons; they rank low and mostly add $0, as the CSC's unpaid share says they should.",
    ]
    path = path or config.REPORTS_DIR / f"rosters_{season}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))
    return path


def surplus_report(con, season: int, result: dict, path: Path | None = None) -> Path:
    """Surplus value per A4 program: learned weights, position values, and on-field value against market value."""
    from . import surplus as su

    def m(v):
        return f"${v / 1e6:.1f}M"

    grid, best = result["grid"], result["best"].set_index("unit")
    prior = grid[grid.prior].set_index("unit").cv_r2
    weights = pd.DataFrame([{"unit": u.replace("_", " "), "production": f"{b.production:.1f}", "rating": f"{b.rating:.1f}",
                             "class year": f"{b.experience:.1f}", "R² learned": f"{b.cv_r2:.2f}",
                             "R² prior weights": f"{prior[u]:.2f}"} for u, b in best.iterrows()])
    g = result["groups"]
    groups = pd.DataFrame({"unit": g.unit.str.replace("_", " "), "position": g.group, "starters": g.starters,
                           "points per starter group": g.starter_points.map("{:.2f}".format)})
    t = result["teams"]
    teams = pd.DataFrame({
        "rank": range(1, len(t) + 1), "program": t.team, "conference": t.conference,
        "market value": t.value.map(m), "on-field points": t.points.map("{:.1f}".format),
        "on-field value": t.on_field_value.map(m), "surplus": t.surplus.map(lambda v: ("+" if v >= 0 else "-") + m(abs(v))),
        "points per $1M": t.points_per_million.map("{:.2f}".format), "SP+": t.sp_rating.map("{:.1f}".format)})
    conf = t.groupby("conference").agg(programs=("team", "count"), surplus=("surplus", "mean"),
                                       efficiency=("points_per_million", "mean")).reset_index()
    conf["surplus"] = conf.surplus.map(lambda v: ("+" if v >= 0 else "-") + m(abs(v)))
    conf["efficiency"] = conf.efficiency.map("{:.2f}".format)
    parts = [
        f"# Surplus value, {season}\n",
        "What each A4 roster delivers on the field against what it would cost at market rates. On-field value "
        f"comes from SP+ team ratings for all {result['fit_teams']} FBS teams: a regression of each unit's rating "
        "(offense, defense, special teams) on its position groups' quality (starters' scores above a national "
        "replacement level, weights kept non-negative) prices each position in rating points. The player score's "
        "weights are learned the same way, by cross-validation against every team's rating, so no selection is "
        f"involved. Points are priced at the A4 market: **${result['price_per_point']:,.0f} per rating point** "
        "(total A4 roster market value / total A4 points). Market value uses last season's production (what was "
        "known when deals were struck); on-field points use this season's. Team totals only. Method: "
        "[`docs/ESTIMATION.md`](../docs/ESTIMATION.md).\n",
        "## Weights learned from team results\n",
        "Out-of-sample R² of each unit's regression (5 folds) under the best weights on a 0.1 grid, against the "
        "prior weights the market value uses.\n", _md(weights, ".2f"),
        "## What each position is worth\n",
        f"The average team's points from each position's starters (and rotation), above replacement. Summed, player "
        f"quality correlates {result['check_corr']:.2f} with SP+ overall team ratings.\n", _md(groups),
        "## Surplus by program\n",
        f"On-field value minus market value. One rating point is about {su.WINS_PER_POINT:.2f} wins over a 12-game "
        "season.\n", _md(teams),
        "## By conference\n", _md(conf),
        "## Limits\n",
        "- This season's production partly reflects team quality, so strong teams' players look productive; the "
        "regression measures that association, not cause.",
        "- Offensive linemen and specialists have no individual production; special teams show almost no signal.",
        "- Market value is a market price for the roster, not what the school pays; surplus is relative to that price.",
        "- Ratings are SP+ as of this pull, mid-season.",
    ]
    path = path or config.REPORTS_DIR / f"surplus_{season}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))
    return path


def ratings_report(season: int, result: dict, path: Path | None = None) -> Path:
    """Surplus fit against several team ratings: how well each is explained, what the weights learn, and how
    much each program's surplus moves with the rating."""
    from . import ratings as rt

    def m(v):
        return "" if pd.isna(v) else f"{'+' if v >= 0 else '−'}${abs(v) / 1e6:.1f}M"

    s, notes, sur = result["summary"], result["notes"], result["surplus"]
    cols = list(result["targets"].columns)
    fit = pd.DataFrame({"rating": s.label, "preseason prior": s.prior,
                        "weights (production / recruiting / class year)": [f"{r.production:.1f} / {r.rating:.1f} / {r.experience:.1f}" for r in s.itertuples()],
                        "R² learned": s.cv_r2.map("{:.2f}".format), "R² prior weights": s.cv_r2_prior_weights.map("{:.2f}".format),
                        "R² production only": s.cv_r2_production_only.map("{:.2f}".format),
                        "R² recruiting + class only": s.cv_r2_rating_class_only.map("{:.2f}".format),
                        "QB points": s.pts_Quarterback.map("{:.1f}".format), "DL points": s["pts_Defensive Lineman"].map("{:.1f}".format),
                        "$ per point": s.price_per_point.map(lambda v: f"${v:,.0f}")})
    rc = result["surplus_rank_corr"].rename(index=rt.LABELS, columns=rt.LABELS).round(2).reset_index(names="")
    counts = sur.agree.value_counts()

    table = pd.DataFrame({"program": sur.index, "conference": sur.conference, "market value": (sur.value / 1e6).map("${:.1f}M".format),
                          **{rt.LABELS[c]: sur[c].map(m) for c in cols},
                          "range": [f"{m(a)} to {m(b)}" for a, b in zip(sur.low, sur.high)], "median": sur["median"].map(m),
                          "call": sur.agree})
    r, y = notes["results"], notes.get("yours")
    parts = [
        f"# Surplus value against several ratings, {season}\n",
        "The surplus model asks how much of each team's rating its players explain. This runs the same fit against six "
        "ratings instead of SP+ alone, each as a team total on every position group, with the player-score weights "
        "chosen by cross-validation for that rating, and prices surplus under each. Method: "
        "[`src/nilmodel/ratings.py`](../src/nilmodel/ratings.py).\n",
        f"- **2026 results only** is fit here from {r['games']} completed FBS-vs-FBS games through week {r['through_week']} "
        f"(last game {r['last_game']}), margins capped at {rt.MARGIN_CAP:.0f}; home edge {r['home_edge']:.1f} points. No prior.",
        (f"- **Your model** is the team rating implied by CollegeFootballRatings2026's posted model margins, {y['games']} "
         f"games, {y['weeks'].replace('-', ' ')}; home edge {y['home_edge']:.1f}. Those files stop at week 8.\n" if y else ""),
        "- SP+, ESPN FPI, SRS and Elo are CollegeFootballData's current 2026 ratings. Player production is this season's.\n",
        "## How well each rating is explained\n",
        "Out-of-sample R² (5 folds over 138 FBS teams). \"Recruiting + class only\" leaves production out: a rating that "
        "leans on a preseason prior built from recruiting should be explained better by it.\n",
        _md(fit, ".2f"),
        "## Do the ratings agree on surplus?\n",
        "Rank correlation of program surplus between ratings:\n",
        _md(rc, ".2f"),
        f"- Under the four published ratings (SP+, FPI, SRS, Elo), which the roster numbers use, "
        f"**{counts.get('surplus everywhere', 0)}** programs show a surplus under all four and "
        f"**{counts.get('deficit everywhere', 0)}** a deficit; **{counts.get('depends on rating', 0)}** depend on the rating. "
        "The results-only rating is a check on SP+'s prior, and your model is kept apart as the market's view.\n",
        "## Every A4 program\n",
        "Sorted by median surplus across the four published ratings; range and call are theirs too.\n",
        _md(table),
    ]
    path = path or config.ROOT / "reports" / f"ratings_{season}.md"
    path.write_text("\n".join(parts))
    return path


def caps_section(df: pd.DataFrame, cal: pd.DataFrame) -> list[str]:
    """The published revenue-share cohorts against CAPS's year-one totals, and the non-A4 tail calibration."""
    from . import triangulate as tri

    def m(v):
        return f"${v / 1e6:,.1f}M"

    fb = tri.football_a4_cap_year(df)          # cap-year terms, to compare with CAPS
    na = tri.calibrate_non_a4(df)
    mult = na[na.case == "central"].tail_mult.iloc[0]
    c = tri.caps_check(df, fb, None if pd.isna(mult) else float(mult))
    g = c["groups"]
    table = pd.DataFrame({"group": g.group, "": g["where"], "paid athletes": g.athletes.map("{:,}".format),
                          "floor (no model)": g.floor.map(m), "estimate": g.estimate.map(m)})
    na_table = pd.DataFrame({"case": na.case.map({"central": "central", "high": "generous", "low": "strict"}),
                             "A4 schools pay": na.a4_spend_share.map("{:.1%} of the cap".format),
                             "left for non-A4": na.target.map(m), "flat-tail total": na.flat_tail_total.map(m),
                             "fitted-tail total": na.fitted_total.map(m),
                             "tail multiplier": ["below a flat tail" if pd.isna(v) else f"x{v:.2f}" for v in na.tail_mult]})
    caps = tri.CAPS_2025_26
    return [
        "## Checked against what schools actually paid\n",
        f"CAPS recorded [{m(caps['revenue_share'])} in revenue-share payments]({tri.CAPS_SOURCE}) in the first cap year "
        f"(July 1, 2025 to June 30, 2026), to {caps['athletes']:,} athletes at {caps['schools_paid']} schools; "
        f"{caps['schools_at_cap']} schools paid the cap or came within 5% of it. The published cohorts, by group. Most "
        "sports' window is that cap year; basketball's ends April 6, 2026; football's is calendar 2026. Estimates put "
        "A4 football at its assumed share of the 2025-26 cap (the cap-year figure), the non-A4 tails as calibrated below, "
        "and fitted tails elsewhere.\n",
        _md(table),
        f"- **Floors:** {m(c['floor_total'])}, safely under CAPS's {m(c['caps_total'])}. The published cohorts hold "
        f"{c['athletes_published']:,} paid athletes against CAPS's {c['athletes_caps']:,} (CAPS counts each athlete "
        "once, and football's window differs, so the counts don't compare exactly).",
        f"- **With fitted tails outside A4 football** the published cohorts would total {m(c['fitted_total'])}, more "
        f"than schools paid. With the non-A4 tails calibrated they total {m(c['estimate_total'])}, against CAPS's "
        f"{m(c['caps_total'])}.",
        f"- **Football's share of the A4 cap:** A4 schools can pay at most {m(c['a4_cap_total'])} (68 x the 2025-26 cap), "
        f"and their other sports were paid at least {m(c['other_a4_floor'])}, so football can take at most "
        f"**{c['football_share_max']:.0%}**. The tail calibration's high case is held there. With the published sports' "
        f"estimates ({m(c['other_a4_estimate'])}) football's share would be about {c['football_share_published']:.0%}, "
        "and less once the unpublished sports are counted, which fits the assumed 75%.\n",
        "### Non-A4 tails\n",
        "What CAPS recorded, less the A4 schools' spending, is what every non-A4 cohort can sum to. The 68 schools at "
        "the cap or within 5% of it are taken to be the 68 A4 programs. Sports too small to publish get no allowance, "
        "so the tails are thinned only as far as the total forces. One multiplier on the fitted slope past the 90th "
        "covers every non-A4 cohort (football, basketball and the other sports); the offer check uses the central case.\n",
        _md(na_table),
    ]


def football_validation_report(result: dict, gates: pd.DataFrame, verdicts: pd.DataFrame, path: Path | None = None) -> Path:
    """The football stress tests: verdicts, gates, and every test's table."""
    status = {"ready": "Ready", "caution": "Use with caution", "not ready": "Not ready"}
    v = verdicts.assign(status=verdicts.status.map(status))[["output", "status", "evidence"]]
    g = gates.assign(value=[("" if x is None or pd.isna(x) else f"{x:.2f}") for x in gates.value],
                     passed=gates.passed.map({True: "pass", False: "FAIL"}))[["check", "value", "threshold", "passed", "note"]]
    s, o = result["surplus"], result["season"]
    loco = s["loco"].pivot_table(index="held_out", columns="source", values="corr").round(2).reset_index()
    parts = [
        "# Football model review\n",
        "Stress tests for the football models before reading insights off them. Method: "
        "[`src/nilmodel/football_validation.py`](../src/nilmodel/football_validation.py). Rerun with `nil validate-football`.\n",
        "## Verdicts\n", _md(v),
        "## Quality gates\n", "The weekly job stops before publishing when one fails.\n", _md(g, ".2f"),
        "## Offer benchmark on football\n", "Mean, median and 90th-percentile miss in percentile points, leave-one-out.\n",
        _md(result["benchmark"], ".2f"),
        "## The top of the A4 market\n", _md(result["tails"].assign(
            qb_p95=result["tails"].qb_p95.map(lambda x: "" if pd.isna(x) else f"${x / 1e6:.2f}M"),
            qb_p99=result["tails"].qb_p99.map(lambda x: "" if pd.isna(x) else f"${x / 1e6:.2f}M")), ".2f"),
        "## Roster market value under other assumptions\n", _md(result["market"]["variants"], ".3f"),
        "## On-field value\n", "Placebo: players dealt to random teams within their position.\n",
        _md(s["placebo"], ".3f"), f"Leave one conference out (correlation of predicted and actual ratings):\n", _md(loco, ".2f"),
        f"Position values, bootstrap over teams ({s['boots']} resamples, four ratings): average points per team "
        "from each group, median and 10th to 90th percentile.\n", _md(s["positions"], ".2f"),
        f"Out of season: fit on 2025 ({o['teams_2025']} teams, weights {o['weights']}, CV R² {o['cv_r2_2025']:.2f}), "
        "predicting 2026.\n", _md(o["results"], ".3f"),
        "## Program surplus under resampling\n", _md(s["programs"].assign(
            surplus_median=s["programs"].surplus_median.map(lambda x: f"${x / 1e6:+.1f}M"),
            surplus_low=s["programs"].surplus_low.map(lambda x: f"${x / 1e6:+.1f}M"),
            surplus_high=s["programs"].surplus_high.map(lambda x: f"${x / 1e6:+.1f}M")), ".0f"),
    ]
    path = path or config.REPORTS_DIR / "football_validation.md"
    path.write_text("\n".join(parts))
    return path
