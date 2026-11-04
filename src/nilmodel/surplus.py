"""Surplus value: what each A4 roster delivers on the field against what it would cost at market rates.

On-field value comes from team strength. SP+ rates every FBS team's offense, defense and special teams
in points per game. A regression of those unit ratings on each team's position-group quality (its
starters' scores above a national replacement level, with non-negative weights) says how many rating
points each group is worth. The player score's weights (production, rating, class year) are chosen by
cross-validation against the same team ratings: learned from every team's results, with no selection,
instead of assumed.

A player's on-field points = his group's points per unit of quality x his slot weight x his score
above replacement. Points are priced at the A4 market: total A4 roster market value / total A4 on-field
points. Surplus = on-field value - market value, per team. Market value uses last season's production
(what was known when deals were struck); on-field points use this season's (what is being delivered).
About 0.3 wins per rating point over a 12-game season (a margin SD near 16). Team totals only.
"""

from __future__ import annotations

import itertools

import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import nnls
from scipy.stats import norm

from . import config
from . import players as pl
from .fetch import Fetcher

UNITS = {
    "offense": {"Quarterback": 1, "Running Back": 1, "Wide Receiver": 3, "Tight End": 1, "Offensive Lineman": 5},
    "defense": {"Defensive Lineman": 4, "Linebacker": 3, "Defensive Back": 4},
    "special_teams": {"Kicker": 1, "Punter": 1},
}
SP_COLUMNS = {"offense": "offense.rating", "defense": "defense.rating", "special_teams": "specialTeams.rating"}
ROTATION = 0.3                                   # weight of the next k players after a group's k starters
WINS_PER_POINT = 12 * norm.pdf(0) / 16          # wins per rating point per season, margin SD 16
GRID_STEP = 0.1


def pull_season(con: duckdb.DuckDBPyConnection, fetcher: Fetcher, season: int = 2026, fresh: bool = False) -> dict:
    """SP+ team ratings and this season's usage, PPA and stats (4 calls)."""
    api = pl.CFBD(fetcher, config.secret("CFBD_API_KEY") or "")
    frames = {
        "cfbd_sp": pd.json_normalize(api.get("/ratings/sp", fresh, year=season)),
        f"cfbd_usage_{season}": pd.json_normalize(api.get("/player/usage", fresh, year=season)),
        f"cfbd_ppa_{season}": pd.json_normalize(api.get("/ppa/players/season", fresh, year=season)),
        f"cfbd_stats_{season}": pd.DataFrame(api.get("/stats/player/season", fresh, year=season)),
    }
    return {t: pl._store(con, t, df.astype({c: str for c in df.columns if df[c].dtype == object}))
            for t, df in frames.items()}


def unit_targets(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """SP+ unit ratings per team, oriented so higher is better (defense is points allowed, so negated)."""
    sp = con.execute("SELECT * FROM cfbd_sp").df()
    out = pd.DataFrame({"team": sp.team, "overall": pd.to_numeric(sp.rating, errors="coerce")})
    for unit, col in SP_COLUMNS.items():
        out[unit] = pd.to_numeric(sp[col], errors="coerce") * (-1 if unit == "defense" else 1)
    return out.dropna().set_index("team")


def quality(frame: pd.DataFrame, score: pd.Series, slots: dict[str, int]) -> tuple[pd.DataFrame, pd.Series]:
    """(team x group quality, each player's contribution). A group's replacement level is the best score
    nationally outside its starter slots; a player contributes slot weight x his score above it."""
    teams = frame.team.nunique()
    contrib = pd.Series(0.0, index=frame.index)
    for group, k in slots.items():
        m = frame.group == group
        s = score[m]
        ranked = s.sort_values(ascending=False)
        repl = ranked.iloc[k * teams] if len(ranked) > k * teams else ranked.min()
        rank = s.groupby(frame.team[m]).rank(ascending=False, method="first") - 1
        weight = np.where(rank < k, 1.0, np.where(rank < 2 * k, ROTATION, 0.0))
        contrib[m] = weight * np.maximum(0.0, s - repl)
    q = (pd.DataFrame({"team": frame.team, "group": frame.group, "c": contrib})
         .pivot_table(index="team", columns="group", values="c", aggfunc="sum", fill_value=0.0))
    return q.reindex(columns=list(slots), fill_value=0.0), contrib


def fit_unit(q: pd.DataFrame, y: pd.Series, folds: int = 5, seed: int = 0) -> tuple[pd.Series, float, float]:
    """(points per unit of quality per group, intercept, cross-validated R^2): least squares with
    non-negative group weights on centered data."""
    X, yv = q.to_numpy(float), y.to_numpy(float)

    def solve(Xt, yt):
        mx, my = Xt.mean(axis=0), yt.mean()
        beta, _ = nnls(Xt - mx, yt - my)
        return beta, my - mx @ beta

    beta, b0 = solve(X, yv)
    fold = np.random.default_rng(seed).integers(folds, size=len(yv))
    pred = np.empty(len(yv))
    for f in range(folds):
        tr, te = fold != f, fold == f
        if te.any() and tr.sum() > X.shape[1] + 1:
            bt, b0t = solve(X[tr], yv[tr])
            pred[te] = b0t + X[te] @ bt
    r2 = 1 - np.sum((yv - pred) ** 2) / np.sum((yv - yv.mean()) ** 2)
    return pd.Series(beta, index=q.columns), float(b0), float(r2)


def _weights(wp: float, wr: float, we: float) -> tuple[dict, dict]:
    rest = wr + we
    return ({"production": wp, "rating": wr, "experience": we},
            {"rating": wr / rest, "experience": we / rest} if rest > 0 else {"rating": 0.5, "experience": 0.5})


def learn_weights(frame: pd.DataFrame, targets: pd.DataFrame, step: float = GRID_STEP) -> pd.DataFrame:
    """Cross-validated R^2 of every unit's regression for each (production, rating, experience) weight
    on a simplex grid, plus the prior weights. Special teams have no production, so only rating against
    experience varies."""
    f = frame[frame.team.isin(targets.index)]
    n = int(round(1 / step))
    grid = [(i * step, j * step, (n - i - j) * step) for i in range(n + 1) for j in range(n + 1 - i)]
    rows = []
    for unit, slots in UNITS.items():
        pts = sorted({(0.0, round(wr, 2), round(1 - wr, 2)) for _, wr, _ in grid}) if unit == "special_teams" else grid
        for wp, wr, we in [*pts, (pl.WEIGHTS["production"], pl.WEIGHTS["rating"], pl.WEIGHTS["experience"])]:
            score = pl.apply_weights(f, *_weights(wp, wr, we))
            q, _ = quality(f, score, slots)
            _, _, r2 = fit_unit(q, targets.loc[q.index, unit])
            rows.append({"unit": unit, "production": round(wp, 2), "rating": round(wr, 2), "experience": round(we, 2),
                         "cv_r2": r2, "prior": (wp, wr, we) == (pl.WEIGHTS["production"], pl.WEIGHTS["rating"],
                                                                pl.WEIGHTS["experience"])})
    return pd.DataFrame(rows)


def run(con: duckdb.DuckDBPyConnection, season: int = 2026) -> dict:
    """Fit on all FBS teams, then value A4 players and price their points at the A4 market."""
    from . import simulate as sim

    fbs = pl.base_frame(con, "fbs", usage=f"cfbd_usage_{season}", ppa=f"cfbd_ppa_{season}",
                        stats=f"cfbd_stats_{season}")
    targets = unit_targets(con)
    fit_frame = fbs[fbs.team.isin(targets.index)].copy()
    grid = learn_weights(fit_frame, targets)
    best = grid[~grid.prior].sort_values("cv_r2", ascending=False).groupby("unit").head(1).set_index("unit")

    points = pd.Series(0.0, index=fit_frame.index)
    groups = []
    for unit, slots in UNITS.items():
        b = best.loc[unit]
        score = pl.apply_weights(fit_frame, *_weights(b.production, b.rating, b.experience))
        q, contrib = quality(fit_frame, score, slots)
        beta, _, r2 = fit_unit(q, targets.loc[q.index, unit])
        for g in slots:
            m = fit_frame.group == g
            points[m] = beta[g] * contrib[m]
            groups.append({"unit": unit, "group": g, "starters": slots[g], "points_per_quality": beta[g],
                           "starter_points": float(points[m].groupby(fit_frame.team[m]).sum().mean())})
    fit_frame["points"] = points
    team_points = fit_frame.groupby("team").points.sum()
    check = float(np.corrcoef(team_points, targets.loc[team_points.index, "overall"])[0, 1])

    a4 = pl.features(con)
    market, per_player = pl.roster_values(a4, sim.football_transports(con.execute("SELECT * FROM csc_latest").df()))
    a4_points = fit_frame[fit_frame.id.isin(a4.id)].groupby("team").points.sum()
    price = market.value.sum() / a4_points.sum()
    t = market.set_index("team")
    t["points"] = a4_points.reindex(t.index).fillna(0.0)
    t["on_field_value"] = t.points * price
    t["surplus"] = t.on_field_value - t.value
    t["points_per_million"] = t.points / (t.value / 1e6)
    t["wins"] = t.points * WINS_PER_POINT
    t["sp_rating"] = targets.overall.reindex(t.index)
    teams = t.reset_index().sort_values("surplus", ascending=False).reset_index(drop=True)
    return {"teams": teams, "grid": grid, "best": best.reset_index(), "groups": pd.DataFrame(groups),
            "price_per_point": price, "check_corr": check, "fit_teams": int(len(targets.index.intersection(fbs.team.unique())))}
