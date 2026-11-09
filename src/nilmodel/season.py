"""The season so far: every game the CollegeFootballRatings2026 weekly files cover, with the pre-game
projections of SP+ and BCF Toys FEI (the rating systems that model is built on) and the final score.

`games` is what the football page shows: the projected home margin (the average of the two systems' projections)
and the final home margin, nothing derived from betting lines. Final scores come from CollegeFootballData
(`cfbd_games_<season>`, pulled by `nil ratings`). `signals` reads that repository's own records for its research
reports; the football page doesn't use it.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from . import config

RATINGS_SEASON_DIR = config.ROOT.parent / "CollegeFootballRatings2026" / "2026"


def _week(path: Path) -> int:
    return int(path.parent.name.split("-")[1])


def _finals(con: duckdb.DuckDBPyConnection, season: int) -> pd.DataFrame:
    g = con.execute(f"SELECT id, homePoints, awayPoints, completed FROM cfbd_games_{season}").df()
    g = g[g.completed.astype(str) == "True"]
    return pd.DataFrame({"game_id": pd.to_numeric(g.id).astype("int64"), "home_points": pd.to_numeric(g.homePoints),
                         "away_points": pd.to_numeric(g.awayPoints)}).dropna().set_index("game_id")


def games(con: duckdb.DuckDBPyConnection, weeks_dir: Path = RATINGS_SEASON_DIR, season: int = 2026) -> list[dict]:
    """One row per game: the projected home margin (SP+ and BCF Toys FEI, averaged) and the final home margin
    once played."""
    files = sorted(weeks_dir.glob("week-*/ratings.csv"))
    if not files:
        return []
    d = pd.concat([pd.read_csv(f).assign(week=_week(f)) for f in files], ignore_index=True)
    fin = _finals(con, season)
    d["projected"] = d[["sp_plus_margin", "bcftoys_margin"]].mean(axis=1)
    rows = []
    for r in d.dropna(subset=["projected"]).itertuples(index=False):
        f = fin.loc[int(r.game_id)] if int(r.game_id) in fin.index else None
        rows.append({"id": str(int(r.game_id)), "week": int(r.week), "kickoff": str(r.kickoff)[:10], "home": r.home_team,
                     "away": r.away_team, "neutral": str(r.neutral_site) == "True", "projected": round(float(r.projected), 2),
                     "final": None if f is None else int(f.home_points - f.away_points)})
    return rows


def _grade(market: str, side: str, line: float, home_points: float, away_points: float) -> str:
    if market == "total":
        edge = (home_points + away_points - line) * (1 if side == "over" else -1)
    else:
        margin = home_points - away_points
        edge = (margin if side == "home" else -margin) + line
    return "win" if edge > 0 else "loss" if edge < 0 else "push"


def signals(con: duckdb.DuckDBPyConnection, weeks_dir: Path = RATINGS_SEASON_DIR, season: int = 2026) -> list[dict]:
    """Every posted signal with its result: as recorded in the weekly file, or graded here from the final."""
    files = sorted(weeks_dir.glob("week-*/bets.csv"))
    if not files:
        return []
    b = pd.concat([pd.read_csv(f).assign(wk=_week(f)) for f in files], ignore_index=True)
    fin = _finals(con, season)
    rows = []
    for r in b.itertuples(index=False):
        result, units, graded = (r.result, r.units, "weekly file") if isinstance(r.result, str) and r.result else (None, None, None)
        if result is None and int(r.game_id) in fin.index:
            f = fin.loc[int(r.game_id)]
            result = _grade(r.market, r.side, float(r.line), f.home_points, f.away_points)
            win = (100 / abs(r.price) if r.price < 0 else r.price / 100)
            units, graded = {"win": win, "push": 0.0, "loss": -1.0}[result], "here, from the final score"
        rows.append({"id": f"{int(r.wk)}|{int(r.game_id)}|{r.market}|{r.side}", "week": int(r.wk), "game": r.game,
                     "rule": r.rule, "pick": r.pick, "price": float(r.price), "live": r.status == "posted" and int(r.wk) >= 7,
                     "result": result, "units": None if units is None or pd.isna(units) else round(float(units), 3),
                     "graded": graded})
    return rows
