"""Surplus value against several team ratings, not SP+ alone.

The surplus model asks how much of a team's rating its players explain. With one rating, that rating's
choices become the model's, and SP+ still blends in a preseason projection built partly from recruiting
and returning production, which the player scores also use. So the same fit is run against:

- `sp`: SP+ (CollegeFootballData), with a fading preseason prior.
- `fpi`: ESPN FPI, also with a prior.
- `srs`: CollegeFootballData's simple rating system: opponent-adjusted scoring margin.
- `elo`: CollegeFootballData's Elo, which starts each season from the last.
- `results`: this repository's fit to every completed 2026 FBS game: home margin = home edge + home rating
  - away rating, margins capped at 28 so blowouts don't dominate. No prior of any kind.
- `yours`: the team ratings implied by the CollegeFootballRatings2026 weekly model margins (its blend of
  public ratings and the market), fit the same way from its posted games.

Each rating is put on SP+'s spread (points per game) and fit as a team total on every position group, with
the player-score weights chosen by cross-validation for that rating. Surplus is then priced per rating. The
roster numbers use the four published ratings (`PUBLIC`): each program's surplus is their median, with their
range, and a call only where all four agree on the sign. The results-only rating is a check, and `yours` is
kept apart as the market's view. Comparing what the weights learn under ratings with and without a
prior is the check on whether SP+'s prior was doing some of the work.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from . import config
from . import players as pl
from . import surplus as su
from .fetch import Fetcher

SLOTS = {g: k for unit in su.UNITS.values() for g, k in unit.items()}   # every group, one team total
PUBLIC = ["sp", "fpi", "srs", "elo"]          # the published ratings the roster numbers use
MARGIN_CAP = 28.0
LABELS = {"sp": "SP+", "fpi": "ESPN FPI", "srs": "SRS", "elo": "Elo", "results": "2026 results only",
          "yours": "Your model (weeks 1-8)"}
PRIOR = {"sp": "yes, fading", "fpi": "yes", "srs": "no", "elo": "carries over last season", "results": "no",
         "yours": "market and SP+/FEI, which have priors"}


def pull(con: duckdb.DuckDBPyConnection, fetcher: Fetcher, season: int = 2026, fresh: bool = False) -> dict:
    """This season's games and the FPI, SRS and Elo ratings (4 calls)."""
    api = pl.CFBD(fetcher, config.secret("CFBD_API_KEY") or "")
    frames = {f"cfbd_games_{season}": pd.json_normalize(api.get("/games", fresh, year=season, seasonType="regular")),
              f"cfbd_fpi_{season}": pd.json_normalize(api.get("/ratings/fpi", fresh, year=season)),
              f"cfbd_srs_{season}": pd.json_normalize(api.get("/ratings/srs", fresh, year=season)),
              f"cfbd_elo_{season}": pd.json_normalize(api.get("/ratings/elo", fresh, year=season))}
    return {t: pl._store(con, t, df.astype({c: str for c in df.columns if df[c].dtype == object}))
            for t, df in frames.items()}


def fit_margins(games: pd.DataFrame, cap: float = MARGIN_CAP, ridge: float = 1e-3) -> tuple[pd.Series, float]:
    """(team ratings, home edge) from games with home, away, margin (home minus away) and neutral columns,
    by least squares on capped margins. Ratings average zero."""
    teams = sorted(set(games.home) | set(games.away))
    ix = {t: i for i, t in enumerate(teams)}
    X = np.zeros((len(games), len(teams) + 1))
    for r, g in enumerate(games.itertuples(index=False)):
        X[r, ix[g.home]], X[r, ix[g.away]] = 1.0, -1.0
        X[r, -1] = 0.0 if g.neutral else 1.0
    y = games.margin.clip(-cap, cap).to_numpy(float)
    A = np.vstack([X, np.sqrt(ridge) * np.eye(len(teams) + 1)[:-1], np.r_[np.ones(len(teams)), 0.0][None, :] * 10])
    sol, *_ = np.linalg.lstsq(A, np.r_[y, np.zeros(len(teams)), 0.0], rcond=None)
    return pd.Series(sol[:-1], index=teams), float(sol[-1])


def results_rating(con: duckdb.DuckDBPyConnection, season: int = 2026) -> tuple[pd.Series, dict]:
    g = con.execute(f"SELECT * FROM cfbd_games_{season}").df()
    g = g[(g.completed.astype(str) == "True") & (g.homeClassification == "fbs") & (g.awayClassification == "fbs")]
    games = pd.DataFrame({"home": g.homeTeam, "away": g.awayTeam, "neutral": g.neutralSite.astype(str) == "True",
                          "margin": pd.to_numeric(g.homePoints) - pd.to_numeric(g.awayPoints)}).dropna()
    rating, hfa = fit_margins(games)
    return rating, {"games": len(games), "home_edge": hfa, "through_week": int(pd.to_numeric(g.week).max()),
                    "last_game": str(g.startDate.max())[:10]}


def model_rating(weeks_dir: Path) -> tuple[pd.Series, dict]:
    """Team ratings implied by the weekly model margins in CollegeFootballRatings2026/2026/week-NN/ratings.csv
    (model_margin is the home team's expected margin)."""
    files = sorted(weeks_dir.glob("week-*/ratings.csv"))
    d = pd.concat([pd.read_csv(f).assign(week=f.parent.name) for f in files], ignore_index=True)
    d = d.dropna(subset=["model_margin"])
    games = pd.DataFrame({"home": d.home_team, "away": d.away_team, "neutral": d.neutral_site.astype(str) == "True",
                          "margin": d.model_margin})
    rating, hfa = fit_margins(games, cap=np.inf)
    return rating, {"games": len(games), "home_edge": hfa, "weeks": f"{files[0].parent.name} to {files[-1].parent.name}"}


def targets(con: duckdb.DuckDBPyConnection, weeks_dir: Path | None, season: int = 2026) -> tuple[pd.DataFrame, dict]:
    """One column per rating source, indexed by team, each rescaled to SP+'s spread across the FBS teams."""
    num = lambda s: pd.to_numeric(s, errors="coerce")
    sp = con.execute("SELECT team, rating FROM cfbd_sp").df()
    fpi = con.execute(f'SELECT team, fpi FROM cfbd_fpi_{season}').df()
    srs = con.execute(f"SELECT team, rating FROM cfbd_srs_{season}").df()
    elo = con.execute(f"SELECT team, elo FROM cfbd_elo_{season}").df()
    t = pd.DataFrame({"sp": num(sp.set_index("team").rating)})
    t["fpi"] = num(fpi.set_index("team").fpi)
    t["srs"] = num(srs.drop_duplicates("team").set_index("team").rating)
    t["elo"] = num(elo.set_index("team").elo)
    res, info = results_rating(con, season)
    t["results"] = res
    notes = {"results": info}
    if weeks_dir is not None and weeks_dir.exists():
        yours, yinfo = model_rating(weeks_dir)
        t["yours"] = yours
        notes["yours"] = yinfo
    t = t.dropna(subset=["sp"])
    sd = t.sp.std()
    for c in t.columns:
        t[c] = (t[c] - t[c].mean()) / t[c].std() * sd
    return t, notes


def grid_points(step: float = su.GRID_STEP) -> list[tuple[float, float, float]]:
    n = int(round(1 / step))
    return [(round(i * step, 2), round(j * step, 2), round((n - i - j) * step, 2)) for i in range(n + 1) for j in range(n + 1 - i)]


def run(con: duckdb.DuckDBPyConnection, weeks_dir: Path | None = None, season: int = 2026) -> dict:
    from . import simulate as sim

    tg, notes = targets(con, weeks_dir, season)
    fbs = pl.base_frame(con, "fbs", usage=f"cfbd_usage_{season}", ppa=f"cfbd_ppa_{season}", stats=f"cfbd_stats_{season}")
    frame = fbs[fbs.team.isin(tg.index)].copy()
    prior = (pl.WEIGHTS["production"], pl.WEIGHTS["rating"], pl.WEIGHTS["experience"])
    grid = []
    cache = {}
    for w in [*grid_points(), prior]:
        score = pl.apply_weights(frame, *su._weights(*w))
        q, contrib = su.quality(frame, score, SLOTS)
        cache[w] = (q, contrib)
        for src in tg.columns:
            y = tg[src].reindex(q.index)
            ok = y.notna()
            _, _, r2 = su.fit_unit(q[ok], y[ok])
            grid.append({"source": src, "production": w[0], "rating": w[1], "experience": w[2], "cv_r2": r2,
                         "prior": w == prior})
    grid = pd.DataFrame(grid)

    a4 = pl.features(con)
    market, _ = pl.roster_values(a4, sim.football_transports(con.execute("SELECT * FROM csc_latest").df()))
    market = market.set_index("team")
    summary, teams = [], {}
    for src in tg.columns:
        g = grid[grid.source == src]
        best = g[~g.prior].sort_values("cv_r2", ascending=False).iloc[0]
        w = (best.production, best.rating, best.experience)
        q, contrib = cache[w]
        y = tg[src].reindex(q.index)
        ok = y.notna()
        beta, _, r2 = su.fit_unit(q[ok], y[ok])
        pts = pd.Series(0.0, index=frame.index)
        for grp in SLOTS:
            m = frame.group == grp
            pts[m] = beta[grp] * contrib[m]
        team_pts = pts.groupby(frame.team).sum()
        a4_pts = team_pts.reindex(market.index).fillna(0.0)
        price = market.value.sum() / a4_pts.sum()
        teams[src] = a4_pts * price - market.value
        corr = float(np.corrcoef(team_pts.reindex(y[ok].index), y[ok])[0, 1])
        row = lambda wp, wr, we: float(g[(g.production == wp) & (g.rating == wr) & (g.experience == we)].cv_r2.iloc[0])
        summary.append({"source": src, "label": LABELS[src], "prior": PRIOR[src], "teams": int(ok.sum()),
                        "production": best.production, "rating": best.rating, "experience": best.experience,
                        "cv_r2": r2, "cv_r2_prior_weights": row(*prior), "cv_r2_production_only": row(1.0, 0.0, 0.0),
                        "cv_r2_rating_class_only": row(0.0, 0.5, 0.5), "fit_corr": corr, "price_per_point": price,
                        **{f"pts_{grp}": float(pts[frame.group == grp].groupby(frame.team[frame.group == grp]).sum().mean())
                           for grp in ("Quarterback", "Defensive Lineman", "Offensive Lineman", "Wide Receiver")}})
    surplus = pd.DataFrame(teams)
    surplus["conference"] = market.conference.reindex(surplus.index)
    surplus["value"] = market.value
    cols = [c for c in PUBLIC if c in surplus]
    surplus["low"], surplus["high"] = surplus[cols].min(axis=1), surplus[cols].max(axis=1)
    surplus["median"] = surplus[cols].median(axis=1)
    surplus["agree"] = np.where((surplus[cols] > 0).all(axis=1), "surplus everywhere",
                                np.where((surplus[cols] < 0).all(axis=1), "deficit everywhere", "depends on rating"))
    surplus["perf_rating"] = tg[cols].median(axis=1).reindex(surplus.index)
    if "yours" in tg:
        surplus["market_rating"] = tg["yours"].reindex(surplus.index)
    return {"targets": tg, "notes": notes, "grid": grid, "summary": pd.DataFrame(summary),
            "surplus": surplus.sort_values("median", ascending=False), "rating_corr": tg.corr(),
            "surplus_rank_corr": surplus[cols].corr(method="spearman")}
