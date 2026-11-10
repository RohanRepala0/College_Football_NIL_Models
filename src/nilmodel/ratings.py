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
- `projected`: the team ratings implied by SP+'s and BCF Toys FEI's pre-game projections in the
  CollegeFootballRatings2026 weekly files, fit the same way from every game they projected.
- `yours`: the same from that repository's model margins (its blend of the projections and the betting market).

Each rating is put on SP+'s spread (points per game) and fit as a team total on every position group, with
the player-score weights chosen by cross-validation for that rating. Surplus is then priced per rating. The
roster numbers use the four published ratings (`PUBLIC`): each program's surplus is their median, with their
range, and a call only where all four agree on the sign. The results-only rating is a check, and `yours` is
kept apart as the market's view.

Pooled weights (`pooled_weights`): one set of player-score weights for both seasons. Each season's team quality is
built from that season's own rosters and production; the team-seasons are stacked with a baseline per season (the
data are centred within season), and cross-validation folds are grouped by program so a school is never in the
training and test folds in different seasons. The weights chosen are the ones with the best average out-of-sample
R² across the four published ratings, and each rating's position values are fit on both seasons. `nil ratings`
uses this whenever last season's tables are on hand (`nil validate-football --pull`). Comparing what the weights learn under ratings with and without a
prior is the check on whether SP+'s prior was doing some of the work.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import nnls

from . import config
from . import players as pl
from . import surplus as su
from .fetch import Fetcher

SLOTS = {g: k for unit in su.UNITS.values() for g, k in unit.items()}   # every group, one team total
PUBLIC = ["sp", "fpi", "srs", "elo"]          # the published ratings the roster numbers use
MARGIN_CAP = 28.0
LABELS = {"sp": "SP+", "fpi": "ESPN FPI", "srs": "SRS", "elo": "Elo", "results": "2026 results only",
          "projected": "SP+ and FEI projections (weeks 1-8)", "yours": "Your model (weeks 1-8)"}
PRIOR = {"sp": "yes, fading", "fpi": "yes", "srs": "no", "elo": "carries over last season", "results": "no",
         "projected": "yes: pre-game projections", "yours": "market and SP+/FEI, which have priors"}


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


def model_rating(weeks_dir: Path, column: str = "model_margin") -> tuple[pd.Series, dict]:
    """Team ratings implied by the home margins in CollegeFootballRatings2026/2026/week-NN/ratings.csv: the
    model's (`model_margin`, mostly the betting market) or the pre-game projections of SP+ and BCF Toys FEI
    averaged (`projected`)."""
    files = sorted(weeks_dir.glob("week-*/ratings.csv"))
    d = pd.concat([pd.read_csv(f).assign(week=f.parent.name) for f in files], ignore_index=True)
    d["projected"] = d[["sp_plus_margin", "bcftoys_margin"]].mean(axis=1)
    d = d.dropna(subset=[column])
    games = pd.DataFrame({"home": d.home_team, "away": d.away_team, "neutral": d.neutral_site.astype(str) == "True",
                          "margin": d[column]})
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
        t["projected"], notes["projected"] = model_rating(weeks_dir, "projected")
        t["yours"], notes["yours"] = model_rating(weeks_dir)
    t = t.dropna(subset=["sp"])
    sd = t.sp.std()
    for c in t.columns:
        t[c] = (t[c] - t[c].mean()) / t[c].std() * sd
    return t, notes


def public_targets(con: duckdb.DuckDBPyConnection, season: int, current: int = 2026) -> pd.DataFrame:
    """The four published ratings for one season, indexed by team, each rescaled to that season's SP+ spread."""
    num = lambda s: pd.to_numeric(s, errors="coerce")
    sfx = "" if season == current else f"_{season}"
    t = pd.DataFrame({"sp": num(con.execute(f"SELECT team, rating FROM cfbd_sp{sfx}").df().set_index("team").rating)})
    t["fpi"] = num(con.execute(f"SELECT team, fpi FROM cfbd_fpi_{season}").df().set_index("team").fpi)
    t["srs"] = num(con.execute(f"SELECT team, rating FROM cfbd_srs_{season}").df().drop_duplicates("team").set_index("team").rating)
    t["elo"] = num(con.execute(f"SELECT team, elo FROM cfbd_elo_{season}").df().set_index("team").elo)
    t = t.dropna(subset=["sp"])
    sd = t.sp.std()
    return pd.DataFrame({c: (t[c] - t[c].mean()) / t[c].std() * sd for c in t.columns})


def prior_season_ready(con: duckdb.DuckDBPyConnection, season: int = 2026) -> bool:
    prev = season - 1
    need = {f"cfbd_roster_{prev}", f"cfbd_sp_{prev}", f"cfbd_fpi_{prev}", f"cfbd_srs_{prev}", f"cfbd_elo_{prev}",
            f"cfbd_recruits_{prev - 5}", "cfbd_usage", "cfbd_ppa", "cfbd_stats"}
    have = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
    return need <= have


def season_frame(con: duckdb.DuckDBPyConnection, season: int, current: int = 2026) -> pd.DataFrame:
    """Every FBS player of one season with features from that season's roster and production."""
    if season == current:
        return pl.base_frame(con, "fbs", usage=f"cfbd_usage_{season}", ppa=f"cfbd_ppa_{season}", stats=f"cfbd_stats_{season}")
    assert season == current - 1, "production on hand covers this season and last"
    return pl.base_frame(con, "fbs", usage="cfbd_usage", ppa="cfbd_ppa", stats="cfbd_stats", roster=f"cfbd_roster_{season}",
                         recruits=("cfbd_recruits", f"cfbd_recruits_{season - 5}"))


def _centred_fit(blocks: list[tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, list[tuple[np.ndarray, float]]]:
    """NNLS on season-centred stacked blocks: (beta, each block's (x mean, y mean))."""
    means = [(X.mean(axis=0), y.mean()) for X, y in blocks]
    Xs = np.vstack([X - mx for (X, _), (mx, _) in zip(blocks, means)])
    ys = np.concatenate([y - my for (_, y), (_, my) in zip(blocks, means)])
    beta, _ = nnls(Xs, ys)
    return beta, means


def pooled_cv(blocks: list[tuple[pd.DataFrame, pd.Series]], folds: int = 5, seed: int = 0) -> float:
    """Out-of-sample R² of the season-centred fit, folds grouped by program, over every team-season, measured
    against each season's own mean."""
    teams = sorted(set().union(*[q.index for q, _ in blocks]))
    fold = dict(zip(teams, np.random.default_rng(seed).integers(folds, size=len(teams))))
    sse = sst = 0.0
    for f in range(folds):
        train, test = [], []
        for q, y in blocks:
            m = np.array([fold[t] == f for t in q.index])
            train.append((q.to_numpy(float)[~m], y.to_numpy(float)[~m]))
            test.append((q.to_numpy(float)[m], y.to_numpy(float)[m]))
        beta, means = _centred_fit(train)
        for (X, y), (mx, my) in zip(test, means):
            if len(y):
                sse += float(np.sum((y - (my + (X - mx) @ beta)) ** 2))
    for q, y in blocks:
        sst += float(np.sum((y.to_numpy(float) - y.mean()) ** 2))
    return 1 - sse / sst


def pooled_weights(con: duckdb.DuckDBPyConnection, season: int = 2026) -> dict:
    """One set of player-score weights from this season and last (see the module notes). Returns the grid (each
    weight set's out-of-sample R², pooled and per season, by rating), the chosen weights, and per season the
    frame, targets and team quality under them."""
    seasons = (season - 1, season)
    frames = {y: season_frame(con, y, season) for y in seasons}
    tgs = {y: public_targets(con, y, season) for y in seasons}
    frames = {y: f[f.team.isin(tgs[y].index)].copy() for y, f in frames.items()}
    prior = (pl.WEIGHTS["production"], pl.WEIGHTS["rating"], pl.WEIGHTS["experience"])
    rows, cache = [], {}
    for w in [*grid_points(), prior]:
        qs = {y: su.quality(f, pl.apply_weights(f, *su._weights(*w)), SLOTS) for y, f in frames.items()}
        cache[w] = qs
        for src in PUBLIC:
            blocks = []
            for y in seasons:
                q = qs[y][0]
                t = tgs[y][src].reindex(q.index)
                ok = t.notna()
                blocks.append((q[ok], t[ok]))
            row = {"source": src, "production": w[0], "rating": w[1], "experience": w[2], "prior": w == prior,
                   "cv_r2": pooled_cv(blocks)}
            for y, (q, t) in zip(seasons, blocks):
                row[f"cv_r2_{y}"] = su.fit_unit(q, t)[2]
            rows.append(row)
    grid = pd.DataFrame(rows)
    mean = grid[~grid.prior].groupby(["production", "rating", "experience"]).cv_r2.mean()
    best = mean.idxmax()
    return {"grid": grid, "weights": best, "seasons": seasons, "frames": frames, "targets": tgs, "quality": cache[best]}


def grid_points(step: float = su.GRID_STEP) -> list[tuple[float, float, float]]:
    n = int(round(1 / step))
    return [(round(i * step, 2), round(j * step, 2), round((n - i - j) * step, 2)) for i in range(n + 1) for j in range(n + 1 - i)]


def run(con: duckdb.DuckDBPyConnection, weeks_dir: Path | None = None, season: int = 2026,
        pooled: bool | None = None) -> dict:
    """Surplus under every rating. `pooled` (default: whenever last season's tables are on hand) uses one set of
    weights from both seasons and position values fit on both; otherwise each rating gets this season's best."""
    from . import simulate as sim

    if pooled is None:
        pooled = prior_season_ready(con, season)
    if pooled:
        return _run_pooled(con, weeks_dir, season)
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
    return _finish(tg, notes, grid, summary, teams, market, pooled=None)


def _finish(tg, notes, grid, summary, teams, market, pooled) -> dict:
    surplus = pd.DataFrame(teams)
    surplus["conference"] = market.conference.reindex(surplus.index)
    surplus["value"] = market.value
    cols = [c for c in PUBLIC if c in surplus]
    surplus["low"], surplus["high"] = surplus[cols].min(axis=1), surplus[cols].max(axis=1)
    surplus["median"] = surplus[cols].median(axis=1)
    surplus["agree"] = np.where((surplus[cols] > 0).all(axis=1), "surplus everywhere",
                                np.where((surplus[cols] < 0).all(axis=1), "deficit everywhere", "depends on rating"))
    surplus["perf_rating"] = tg[cols].median(axis=1).reindex(surplus.index)
    if "projected" in tg:
        surplus["expected_rating"] = tg["projected"].reindex(surplus.index)
    return {"targets": tg, "notes": notes, "grid": grid, "summary": pd.DataFrame(summary),
            "surplus": surplus.sort_values("median", ascending=False), "rating_corr": tg.corr(),
            "surplus_rank_corr": surplus[cols].corr(method="spearman"), "pooled": pooled}


def _run_pooled(con: duckdb.DuckDBPyConnection, weeks_dir: Path | None, season: int) -> dict:
    from . import simulate as sim

    tg, notes = targets(con, weeks_dir, season)
    pool = pooled_weights(con, season)
    w, (prev, cur) = pool["weights"], pool["seasons"]
    g = pool["grid"]
    frame = pool["frames"][cur]
    q_cur, contrib = pool["quality"][cur]
    a4 = pl.features(con)
    market, _ = pl.roster_values(a4, sim.football_transports(con.execute("SELECT * FROM csc_latest").df()))
    market = market.set_index("team")
    prior = (pl.WEIGHTS["production"], pl.WEIGHTS["rating"], pl.WEIGHTS["experience"])
    summary, teams = [], {}
    for src in tg.columns:
        y_cur = tg[src].reindex(q_cur.index)
        ok = y_cur.notna()
        if src in PUBLIC:            # position values from both seasons
            q_prev = pool["quality"][prev][0]
            y_prev = pool["targets"][prev][src].reindex(q_prev.index)
            okp = y_prev.notna()
            beta, _ = _centred_fit([(q_prev[okp].to_numpy(float), y_prev[okp].to_numpy(float)),
                                    (q_cur[ok].to_numpy(float), y_cur[ok].to_numpy(float))])
            beta = pd.Series(beta, index=q_cur.columns)
            gs = g[g.source == src]
            at = lambda wt: gs[(gs.production == wt[0]) & (gs.rating == wt[1]) & (gs.experience == wt[2])].iloc[0]  # noqa: E731
            r2, r2_prior = float(at(w).cv_r2), float(at(prior).cv_r2)
            r2_prod, r2_rc = float(at((1.0, 0.0, 0.0)).cv_r2), float(at((0.0, 0.5, 0.5)).cv_r2)
            own = gs[~gs.prior].sort_values(f"cv_r2_{cur}", ascending=False).iloc[0]
            extra = {"cv_r2_this_season_pooled_weights": float(at(w)[f"cv_r2_{cur}"]),
                     "cv_r2_this_season_own_best": float(own[f"cv_r2_{cur}"]),
                     "cv_r2_last_season_pooled_weights": float(at(w)[f"cv_r2_{prev}"]),
                     "own_best_this_season": (own.production, own.rating, own.experience)}
        else:                        # only this season exists for these ratings
            beta, _, r2 = su.fit_unit(q_cur[ok], y_cur[ok])
            fit_at = lambda wt: su.fit_unit(*_q_y(frame, wt, y_cur))[2]  # noqa: E731
            r2_prior, r2_prod, r2_rc = fit_at(prior), fit_at((1.0, 0.0, 0.0)), fit_at((0.0, 0.5, 0.5))
            extra = {}
        pts = pd.Series(0.0, index=frame.index)
        for grp in SLOTS:
            m = frame.group == grp
            pts[m] = beta[grp] * contrib[m]
        team_pts = pts.groupby(frame.team).sum()
        a4_pts = team_pts.reindex(market.index).fillna(0.0)
        price = market.value.sum() / a4_pts.sum()
        teams[src] = a4_pts * price - market.value
        corr = float(np.corrcoef(team_pts.reindex(y_cur[ok].index), y_cur[ok])[0, 1])
        summary.append({"source": src, "label": LABELS[src], "prior": PRIOR[src], "teams": int(ok.sum()),
                        "production": w[0], "rating": w[1], "experience": w[2], "cv_r2": r2,
                        "cv_r2_prior_weights": r2_prior, "cv_r2_production_only": r2_prod, "cv_r2_rating_class_only": r2_rc,
                        "fit_corr": corr, "price_per_point": price, **extra,
                        **{f"pts_{grp}": float(pts[frame.group == grp].groupby(frame.team[frame.group == grp]).sum().mean())
                           for grp in ("Quarterback", "Defensive Lineman", "Offensive Lineman", "Wide Receiver")}})
    return _finish(tg, notes, g, summary, teams, market,
                   pooled={"weights": w, "seasons": pool["seasons"], "team_seasons": int(sum(len(pool["quality"][y][0]) for y in pool["seasons"]))})


def _q_y(frame: pd.DataFrame, w: tuple, y: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    q, _ = su.quality(frame, pl.apply_weights(frame, *su._weights(*w)), SLOTS)
    t = y.reindex(q.index)
    return q[t.notna()], t[t.notna()]
