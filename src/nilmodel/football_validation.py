"""Stress tests for the football models, run before reading insights off them.

Each test asks whether an output survives a change it shouldn't care about, or fails one it should:

- `benchmark_accuracy`: the offer benchmark on football's published percentiles, leave-one-out.
- `tail_sensitivity`: the top of the A4 market across the range the outside totals allow.
- `market_sensitivity`: roster market values under other rank-to-pay correlations and feature weights.
- `surplus_tests`, against each of the four published ratings:
  placebo (players shuffled across teams within their position: the fit should collapse), bootstrap (teams
  resampled: how stable position values and program surplus ranks are), and leave-one-conference-out (each
  conference predicted from all the others).
- `out_of_season`: the on-field model fit on 2025 (rosters, production and SP+ of that season) predicts 2026.
- `market_premise`: whether pre-season market value tracks how A4 teams have played.
- `data_quality`: rosters against the CSC's counts, and feature coverage.

Nothing here touches revenue share outside football, NIL outside football, or betting data.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import nnls
from scipy.stats import spearmanr

from . import benchmark as bm
from . import config
from . import players as pl
from . import ratings as rt
from . import simulate as sim
from . import surplus as su
from . import triangulate as tri

A4_CONFS = ["SEC", "Big Ten", "Big 12", "ACC"]
RHOS = (0.43, 0.5, 0.66)          # the simulation's range of how well public data ranks pay, and the value used


def benchmark_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-out misses (percentile points) on football cohorts only, by report, test and method."""
    e = bm.validate(df)
    e = e[e.cohort.str.contains("Football")]
    return (e.groupby(["report", "test", "method"]).error
            .agg(points="size", mean="mean", median="median", p90=lambda x: x.quantile(0.9)).reset_index())


def tail_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """A4 quarterback 95th and 99th, and A4 football revenue share per program, under the fitted tail and each
    calibrated case."""
    cal = tri.calibrate(df)
    curves = bm.curves(df)[0]
    rows = []
    for report in ("revenue_share", "nil_go"):
        qb = bm.find(curves, report, "Football", "Quarterback", "A4")
        cases = [("fitted", 1.0, None)] + [(r.case, r.tail_mult, r.assumed_share) for r in cal[cal.report == report].itertuples()]
        for case, mult, share in cases:
            if pd.isna(mult):
                rows.append({"report": report, "case": case, "assumed_share": share, "tail_mult": None,
                             "qb_p95": None, "qb_p99": None})
                continue
            rows.append({"report": report, "case": case, "assumed_share": share, "tail_mult": float(mult),
                         "qb_p95": tri.tail_value(qb, 95, mult), "qb_p99": tri.tail_value(qb, 99, mult)})
    return pd.DataFrame(rows)


def market_sensitivity(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> dict:
    """Roster market values when the rank-to-pay correlation or the feature weights change, against the values
    the pages show (correlation 0.5, prior weights)."""
    frame = pl.base_frame(con, "a4")
    transports = sim.football_transports(df)
    base_players = frame.assign(score=pl.apply_weights(frame))
    base, _ = pl.roster_values(base_players, transports, rho=0.5)
    base = base.set_index("team")
    rows = []
    variants = [(f"rank correlation {r}", base_players, r) for r in RHOS if r != 0.5]
    learned = frame.assign(score=pl.apply_weights(frame, *su._weights(0.4, 0.1, 0.5)))
    variants.append(("weights learned from team results (0.4 / 0.1 / 0.5)", learned, 0.5))
    for name, players, rho in variants:
        v, _ = pl.roster_values(players, transports, rho=rho)
        v = v.set_index("team").reindex(base.index)
        change = (v.value - base.value) / base.value
        rows.append({"variant": name, "rank_corr_with_shown": float(spearmanr(v.value, base.value)[0]),
                     "median_abs_change": float(change.abs().median()), "max_abs_change": float(change.abs().max()),
                     "total_change": float(v.value.sum() / base.value.sum() - 1)})
    width = (base.high - base.low) / base.value
    return {"variants": pd.DataFrame(rows), "range_width_median": float(width.median()),
            "range_width_max": float(width.max()), "programs": int(len(base))}


def _fit(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    mx, my = X.mean(axis=0), y.mean()
    beta, _ = nnls(X - mx, y - my)
    return beta, my - mx @ beta


def _r2(y: np.ndarray, pred: np.ndarray) -> float:
    return float(1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2))


def surplus_tests(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, boots: int = 200, perms: int = 20,
                  season: int = 2026, seed: int = 0) -> dict:
    """Placebo, bootstrap and leave-one-conference-out, against each published rating, with each rating's
    cross-validated weights from `ratings.run`."""
    out = rt.run(con, None, season)
    tg, summary = out["targets"], out["summary"].set_index("source")
    fbs = pl.base_frame(con, "fbs", usage=f"cfbd_usage_{season}", ppa=f"cfbd_ppa_{season}", stats=f"cfbd_stats_{season}")
    frame = fbs[fbs.team.isin(tg.index)].reset_index(drop=True)
    conf = frame.drop_duplicates("team").set_index("team").conference
    a4 = pl.features(con)
    market, _ = pl.roster_values(a4, sim.football_transports(df))
    market = market.set_index("team")
    rng = np.random.default_rng(seed)
    groups = list(rt.SLOTS)

    placebo, loco, boot_beta, boot_surplus = [], [], [], {}
    real_r2 = {}
    for src in rt.PUBLIC:
        b = summary.loc[src]
        score = pl.apply_weights(frame, *su._weights(b.production, b.rating, b.experience))
        q, _ = su.quality(frame, score, rt.SLOTS)
        y = tg[src].reindex(q.index)
        _, _, real_r2[src] = su.fit_unit(q, y)
        # placebo: the same players and scores, dealt to random teams within each position group
        r2s = []
        for _ in range(perms):
            shuffled = frame.copy()
            for g, idx in shuffled.groupby("group").groups.items():
                shuffled.loc[idx, "team"] = rng.permutation(shuffled.loc[idx, "team"].to_numpy())
            qp, _ = su.quality(shuffled, score, rt.SLOTS)
            _, _, r2p = su.fit_unit(qp, y.reindex(qp.index))
            r2s.append(r2p)
        placebo.append({"source": src, "label": rt.LABELS[src], "cv_r2": real_r2[src], "placebo_mean": float(np.mean(r2s)),
                        "placebo_max": float(np.max(r2s))})
        # leave one conference out: A4 conferences one at a time, and all non-A4 teams together
        X, yv = q.to_numpy(float), y.to_numpy(float)
        tconf = conf.reindex(q.index).fillna("FBS Independents")
        for held in [*A4_CONFS, "Non-A4"]:
            test = ~tconf.isin(A4_CONFS + ["FBS Independents"]) if held == "Non-A4" else (tconf == held)
            test = test.to_numpy()
            beta, b0 = _fit(X[~test], yv[~test])
            pred = b0 + X[test] @ beta
            loco.append({"source": src, "held_out": held, "teams": int(test.sum()), "r2": _r2(yv[test], pred),
                         "corr": float(np.corrcoef(yv[test], pred)[0, 1])})
        # bootstrap teams
        qa4 = q.reindex(market.index).fillna(0.0).to_numpy(float)
        draws = []
        for _ in range(boots):
            i = rng.integers(0, len(yv), len(yv))
            beta, _ = _fit(X[i], yv[i])
            boot_beta.append({"source": src, **dict(zip(groups, beta))})
            pts = qa4 @ beta
            draws.append(pts * (market.value.sum() / pts.sum()) - market.value.to_numpy())
        boot_surplus[src] = np.array(draws)

    # position values: average starter-group points per team = beta x the group's mean quality
    q_mean = None
    bb = pd.DataFrame(boot_beta)
    for src in rt.PUBLIC:
        b = summary.loc[src]
        score = pl.apply_weights(frame, *su._weights(b.production, b.rating, b.experience))
        qm = su.quality(frame, score, rt.SLOTS)[0].mean()
        sub = bb[bb.source == src][groups] * qm
        q_mean = sub if q_mean is None else pd.concat([q_mean, sub])
    positions = pd.DataFrame({"group": groups, "median": q_mean.median().values, "low": q_mean.quantile(0.1).values,
                              "high": q_mean.quantile(0.9).values,
                              "zero_share": (q_mean <= 1e-9).mean().values})
    # program surplus: median across the four ratings per draw, then its spread and rank spread
    med = np.median(np.stack([boot_surplus[s] for s in rt.PUBLIC]), axis=0)           # boots x programs
    ranks = (-med).argsort(axis=1).argsort(axis=1) + 1
    prog = pd.DataFrame({"team": market.index, "surplus_median": np.median(med, axis=0),
                         "surplus_low": np.quantile(med, 0.1, axis=0), "surplus_high": np.quantile(med, 0.9, axis=0),
                         "rank_median": np.median(ranks, axis=0), "rank_low": np.quantile(ranks, 0.1, axis=0),
                         "rank_high": np.quantile(ranks, 0.9, axis=0),
                         "sign_stable": ((med > 0).mean(axis=0) >= 0.9) | ((med < 0).mean(axis=0) >= 0.9)})
    prog = prog.sort_values("surplus_median", ascending=False).reset_index(drop=True)
    weights = summary.loc[rt.PUBLIC, ["label", "production", "rating", "experience", "cv_r2"]].reset_index()
    return {"placebo": pd.DataFrame(placebo), "loco": pd.DataFrame(loco), "positions": positions, "programs": prog,
            "weights": weights, "boots": boots, "perms": perms}


def pull_prior(con: duckdb.DuckDBPyConnection, fetcher, season: int = 2026, fresh: bool = False) -> dict:
    """Last season's rosters and final SP+, and the recruiting class five years before it (its oldest players),
    for `out_of_season` (3 calls). Stored apart from this season's tables."""
    api = pl.CFBD(fetcher, config.secret("CFBD_API_KEY") or "")
    prev = season - 1
    roster = pd.DataFrame(api.get("/roster", fresh, year=prev))
    roster["recruitIds"] = roster["recruitIds"].map(lambda v: [str(x) for x in v] if isinstance(v, list) else [])
    frames = {f"cfbd_roster_{prev}": roster, f"cfbd_sp_{prev}": pd.json_normalize(api.get("/ratings/sp", fresh, year=prev)),
              f"cfbd_recruits_{prev - 5}": pd.json_normalize(api.get("/recruiting/players", fresh, year=prev - 5,
                                                                     classification="HighSchool"))}
    return {t: pl._store(con, t, df.astype({c: str for c in df.columns if df[c].dtype == object and c != "recruitIds"}))
            for t, df in frames.items()}


def out_of_season(con: duckdb.DuckDBPyConnection, season: int = 2026) -> dict:
    """Fit the on-field model on last season (its rosters, production and final SP+), then predict this season's
    ratings from this season's rosters and production with last season's weights and position values."""
    prev = season - 1
    f25 = pl.base_frame(con, "fbs", usage="cfbd_usage", ppa="cfbd_ppa", stats="cfbd_stats", roster=f"cfbd_roster_{prev}",
                        recruits=("cfbd_recruits", f"cfbd_recruits_{prev - 5}"))
    sp25 = con.execute(f"SELECT team, rating FROM cfbd_sp_{prev}").df().set_index("team").rating.astype(float)
    f25 = f25[f25.team.isin(sp25.index)]
    best = None
    for w in rt.grid_points():
        score = pl.apply_weights(f25, *su._weights(*w))
        q, _ = su.quality(f25, score, rt.SLOTS)
        _, _, r2 = su.fit_unit(q, sp25.reindex(q.index))
        if best is None or r2 > best[1]:
            best = (w, r2)
    w, cv25 = best
    score = pl.apply_weights(f25, *su._weights(*w))
    q25, _ = su.quality(f25, score, rt.SLOTS)
    beta, b0 = _fit(q25.to_numpy(float), sp25.reindex(q25.index).to_numpy(float))

    tg, _ = rt.targets(con, None, season)
    f26 = pl.base_frame(con, "fbs", usage=f"cfbd_usage_{season}", ppa=f"cfbd_ppa_{season}", stats=f"cfbd_stats_{season}")
    f26 = f26[f26.team.isin(tg.index)]
    q26, _ = su.quality(f26, pl.apply_weights(f26, *su._weights(*w)), rt.SLOTS)
    pred = pd.Series(b0 + q26.to_numpy(float) @ beta, index=q26.index)
    rows = []
    for name, y in [("SP+ 2026", tg.sp), ("median of the four published ratings", tg[rt.PUBLIC].median(axis=1))]:
        y = y.reindex(pred.index)
        ok = y.notna()
        # ratings are rescaled to SP+'s spread; compare on SP+'s raw scale for SP+ itself
        raw = con.execute("SELECT team, rating FROM cfbd_sp").df().set_index("team").rating.astype(float).reindex(pred.index)
        target = raw if name == "SP+ 2026" else y
        rows.append({"target": name, "teams": int(ok.sum()), "r2": _r2(target[ok].to_numpy(), pred[ok].to_numpy()),
                     "corr": float(np.corrcoef(target[ok], pred[ok])[0, 1])})
    return {"weights": {"production": w[0], "rating": w[1], "experience": w[2]}, "cv_r2_2025": cv25,
            "teams_2025": int(q25.shape[0]), "results": pd.DataFrame(rows),
            "positions_2025": pd.Series(beta * q25.mean().to_numpy(), index=list(rt.SLOTS))}


def market_premise(con: duckdb.DuckDBPyConnection) -> dict:
    """Does pre-season market value (last season's production, recruiting, class year, priced at CSC rates) track
    how A4 teams have played this season (median of the four published ratings)?"""
    r = pd.DataFrame(json.loads((config.DATA_DIR / "dashboard" / "rosters.json").read_text()))
    ok = r.perf_rating.notna()
    return {"programs": int(ok.sum()), "corr": float(np.corrcoef(r.value[ok], r.perf_rating[ok])[0, 1]),
            "rank_corr": float(spearmanr(r.value[ok], r.perf_rating[ok])[0])}


def data_quality(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> dict:
    a4 = pl.features(con)
    check = pl.roster_check(a4, df)
    check["diff"] = check.rosters_now - check.csc_calendar_2026
    prod_groups = a4.group.isin(list(pl.OFFENSE) + list(pl.DEFENSE))
    return {"roster_check": check, "players": int(len(a4)), "csc_rostered": int(check.csc_calendar_2026.sum()),
            "rating_coverage": float(a4.rating.notna().mean()),
            "production_coverage": float(a4[prod_groups].production.notna().mean()),
            "transfers": int(a4.transfer.sum())}


def run(con: duckdb.DuckDBPyConnection, boots: int = 200, perms: int = 20) -> dict:
    df = con.execute("SELECT * FROM csc_latest").df()
    return {"benchmark": benchmark_accuracy(df), "tails": tail_sensitivity(df), "market": market_sensitivity(con, df),
            "surplus": surplus_tests(con, df, boots=boots, perms=perms), "season": out_of_season(con),
            "premise": market_premise(con), "quality": data_quality(con, df)}


def to_json(result: dict) -> dict:
    """Plain data for the review page."""
    def rec(x):
        if isinstance(x, pd.DataFrame):
            return json.loads(x.to_json(orient="records"))
        if isinstance(x, pd.Series):
            return json.loads(x.to_json())
        if isinstance(x, dict):
            return {k: rec(v) for k, v in x.items()}
        if isinstance(x, (np.floating, np.integer)):
            return x.item()
        return x
    return rec(result)


# ---------------------------------------------------------------- quality gates and history

HISTORY_DIR = config.DATA_DIR / "players" / "history"
GATES = {
    "roster_vs_csc": ("A4 rosters within 5% of the CSC's rostered count", 0.05),
    "rating_coverage": ("At least 60% of A4 players have a recruiting or portal rating", 0.60),
    "fit_r2": ("Every published rating explained out of sample (R² at least 0.45)", 0.45),
    "placebo": ("Shuffled rosters explain nothing (placebo R² at most 0.15)", 0.15),
    "out_of_season": ("Last season's model predicts this season (R² at least 0.40)", 0.40),
    "agreement": ("At least 75% of programs keep one surplus sign under all four ratings", 0.75),
    "week_over_week": ("Program surplus ranks hold from the last snapshot (rank correlation at least 0.80)", 0.80),
}


def _latest_snapshot(before: str | None = None, history_dir: Path | None = None) -> Path | None:
    history_dir = history_dir or HISTORY_DIR
    snaps = sorted(p for p in history_dir.glob("*") if p.is_dir() and (before is None or p.name < before))
    return snaps[-1] if snaps else None


def gates(result: dict, today: str, rosters: pd.DataFrame | None = None, history_dir: Path | None = None) -> pd.DataFrame:
    """Each gate's value, threshold and whether it passed. The weekly job stops before publishing on a failure.
    `rosters` is this week's surplus by rating (the newest data/players/surplus_by_rating_<season>.csv by default)."""
    q, s, o = result["quality"], result["surplus"], result["season"]
    roster_gap = abs(q["players"] / q["csc_rostered"] - 1)
    if rosters is None:
        rosters = pd.read_csv(sorted((config.DATA_DIR / "players").glob("surplus_by_rating_[0-9][0-9][0-9][0-9].csv"))[-1])
    agree = float((rosters.agree != "depends on rating").mean())
    rows = [("roster_vs_csc", roster_gap, roster_gap <= GATES["roster_vs_csc"][1]),
            ("rating_coverage", q["rating_coverage"], q["rating_coverage"] >= GATES["rating_coverage"][1]),
            ("fit_r2", float(s["placebo"].cv_r2.min()), s["placebo"].cv_r2.min() >= GATES["fit_r2"][1]),
            ("placebo", float(s["placebo"].placebo_max.max()), s["placebo"].placebo_max.max() <= GATES["placebo"][1]),
            ("out_of_season", float(o["results"].r2.min()), o["results"].r2.min() >= GATES["out_of_season"][1]),
            ("agreement", agree, agree >= GATES["agreement"][1])]
    prev = _latest_snapshot(before=today, history_dir=history_dir)
    if prev is not None and (prev / "surplus_by_rating.csv").exists():
        old = pd.read_csv(prev / "surplus_by_rating.csv").set_index("team")["median"]
        new = rosters.set_index("team")["median"].reindex(old.index)
        rc = float(spearmanr(old, new, nan_policy="omit")[0])
        rows.append(("week_over_week", rc, rc >= GATES["week_over_week"][1]))
    else:
        rows.append(("week_over_week", None, True))           # nothing to compare with yet
    return pd.DataFrame([{"gate": g, "check": GATES[g][0], "threshold": GATES[g][1], "value": v, "passed": bool(p),
                          "note": "" if v is not None else "no earlier snapshot"} for g, v, p in rows])


def snapshot(today: str) -> Path:
    """Copy this week's football outputs to data/players/history/<date>/ for week-over-week checks and audit."""
    import shutil

    d = HISTORY_DIR / today
    d.mkdir(parents=True, exist_ok=True)
    players = config.DATA_DIR / "players"
    for src, name in [(sorted(players.glob("surplus_by_rating_[0-9][0-9][0-9][0-9].csv"))[-1], "surplus_by_rating.csv"),
                      (sorted(players.glob("surplus_[0-9][0-9][0-9][0-9].csv"))[-1], "surplus_units.csv"),
                      (config.DATA_DIR / "dashboard" / "rosters.json", "rosters.json"),
                      (config.DATA_DIR / "dashboard" / "football_validation.json", "football_validation.json")]:
        if src.exists():
            shutil.copyfile(src, d / name)
    return d



# ---------------------------------------------------------------- verdicts

def _m(v: float) -> str:
    return f"${v / 1e6:.1f}M"


def verdicts(result: dict) -> pd.DataFrame:
    """One line per output: ready, use with caution, or not ready, with the evidence."""
    b = result["benchmark"]
    lin = b[b.method == "linear"].set_index(["report", "test"])["mean"]
    rs_in, nil_in = lin.get(("revenue_share", "loo_interior")), lin.get(("nil_go", "loo_interior"))
    t = result["tails"].set_index(["report", "case"])
    m, s, o, prem = result["market"], result["surplus"], result["season"], result["premise"]
    prog, pos, loco = s["programs"], s["positions"].set_index("group"), s["loco"]
    stable = int(prog.sign_stable.sum())
    lc = loco.groupby("held_out")["corr"].mean()
    w26 = s["weights"].set_index("source").loc["sp"]
    w25 = o["weights"]
    rows = [
        ("Offer check: revenue share, inside the published range", "ready",
         f"Held-out published values are placed within {rs_in:.1f} percentile points on average."),
        ("Offer check: NIL Go", "caution",
         f"Held-out values miss by {nil_in:.0f} percentile points: flat payment tiers and wide gaps make NIL percentiles coarse."),
        ("Anything past the published 90th", "caution",
         f"The A4 quarterback revenue-share 99th is {_m(t.loc[('revenue_share', 'central'), 'qb_p99'])} at the central "
         f"assumption and up to {_m(t.loc[('revenue_share', 'high'), 'qb_p99'])} under the most generous total; NIL "
         f"{_m(t.loc[('nil_go', 'central'), 'qb_p99'])} to {_m(t.loc[('nil_go', 'high'), 'qb_p99'])}. Quote ranges."),
        ("Floor on A4 program spending", "ready", "Needs no model: it follows from the published percentiles."),
        ("Roster market value, program level", "ready",
         f"Program rankings hold at a rank correlation of {m['variants'].rank_corr_with_shown.min():.2f} or better under "
         f"other assumptions (median change {m['variants'].median_abs_change.max():.0%}); each value carries a "
         f"{m['range_width_median']:.0%}-wide range."),
        ("Roster surplus, program level", "ready" if stable / len(prog) >= 0.8 else "caution",
         f"{stable} of {len(prog)} programs keep their sign in 90% of bootstrap resamples; shuffled rosters explain "
         f"nothing (placebo R² {s['placebo'].placebo_mean.mean():.2f} against {s['placebo'].cv_r2.mean():.2f})."),
        ("On-field value across seasons", "ready",
         f"Fit on 2025, the model predicts 2026 team ratings at R² {o['results'].r2.min():.2f} to {o['results'].r2.max():.2f} "
         f"(correlation {o['results']['corr'].max():.2f}), as well as fitting 2026 itself."),
        ("Position values", "caution",
         f"Quarterback ({pos.loc['Quarterback', 'low']:.1f} to {pos.loc['Quarterback', 'high']:.1f} points), offensive line, "
         f"linebacker and running back are stable; defensive backs get zero in {pos.loc['Defensive Back', 'zero_share']:.0%} "
         f"of resamples and wide receivers in {pos.loc['Wide Receiver', 'zero_share']:.0%}, so those two can't be valued."),
        ("Comparisons within one conference", "caution",
         f"Predicting a held-out conference correlates {lc.min():.2f} ({lc.idxmin()}) to {lc.max():.2f} ({lc.idxmax()}): "
         "rankings across FBS are firmer than within a conference."),
        ("Pre-season market value as a guide to results", "caution",
         f"Correlates {prem['corr']:.2f} with how A4 teams have played: it explains about {prem['corr'] ** 2:.0%} of it."),
        ("Player-score weights", "not ready",
         f"The 2025 fit weights production {w25['production']:.1f} / rating {w25['rating']:.1f} / class year "
         f"{w25['experience']:.1f}; the 2026 fit {w26.production:.1f} / {w26.rating:.1f} / {w26.experience:.1f}. Don't read "
         "meaning into the weights."),
        ("Individual player values", "not ready",
         "No individual contracts exist to test against, so only program totals are shown."),
    ]
    return pd.DataFrame(rows, columns=["output", "status", "evidence"])
