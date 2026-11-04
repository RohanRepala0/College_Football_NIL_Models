"""CollegeFootballData player layer: rosters, recruiting, transfer portal and last season's production,
mapped to the CSC's cohorts, and each A4 roster valued at the market rates the CSC publishes.

Every call costs against the free tier (1,000 a month). Each response is kept as a raw snapshot and
reused unless `fresh`, so a full pull is about a dozen calls, once.

Tables (replaced on each pull): cfbd_teams, cfbd_roster, cfbd_recruits, cfbd_portal, cfbd_usage,
cfbd_ppa, cfbd_stats, and player_features (A4 players with their CSC group and features).

Roster market value is what a roster would cost if each player were paid his position's A4 market
rate at his rank: the CSC's revenue-share distribution read at a ranking from public features. It is
not what a school spends. Individual estimates stay in the local database; only team totals leave it.
"""

from __future__ import annotations

import json

import duckdb
import numpy as np
import pandas as pd

from . import config
from . import extend as ex
from .fetch import Fetcher

BASE = "https://api.collegefootballdata.com"
A4_CONFERENCES = {"ACC", "Big Ten", "Big 12", "SEC"}
A4_INDEPENDENTS = {"Notre Dame"}          # in the ACC for other sports, so the CSC counts it as A4
POSITION_GROUPS = {
    "QB": "Quarterback", "RB": "Running Back", "FB": "Running Back", "WR": "Wide Receiver", "TE": "Tight End",
    "OL": "Offensive Lineman", "OT": "Offensive Lineman", "OG": "Offensive Lineman", "C": "Offensive Lineman",
    "IOL": "Offensive Lineman", "DL": "Defensive Lineman", "DE": "Defensive Lineman", "DT": "Defensive Lineman",
    "NT": "Defensive Lineman", "EDGE": "Defensive Lineman", "LB": "Linebacker", "ILB": "Linebacker",
    "OLB": "Linebacker", "DB": "Defensive Back", "CB": "Defensive Back", "S": "Defensive Back",
    "SAF": "Defensive Back", "K": "Kicker", "PK": "Kicker", "P": "Punter", "LS": "Long Snapper",
}
OFFENSE = {"Quarterback", "Running Back", "Wide Receiver", "Tight End"}
DEFENSE = {"Defensive Lineman", "Linebacker", "Defensive Back"}
# Feature weights within a group: a stated prior until representative claims can teach better ones.
WEIGHTS = {"production": 0.45, "rating": 0.35, "experience": 0.20}
WEIGHTS_NO_PRODUCTION = {"rating": 0.60, "experience": 0.40}
STAR_RATING = {2: 0.80, 3: 0.86, 4: 0.92, 5: 0.98}   # a rating for a transfer listed with stars only
RANK_CORR = 0.5      # how well the features are assumed to rank pay; the simulation's weak-to-strong range is 0.43-0.66


class CFBD:
    def __init__(self, fetcher: Fetcher, key: str):
        self.fetcher, self.headers = fetcher, {"Authorization": f"Bearer {key}", "Accept": "application/json"}

    def get(self, path: str, fresh: bool = False, **params) -> list[dict]:
        snap = self.fetcher.fetch("cfbd", BASE + path, fresh=fresh, ext="json", params=params, headers=self.headers)
        return json.loads(snap.body)


def _store(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> int:
    con.register("_frame", df)
    try:
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _frame")
    finally:
        con.unregister("_frame")
    return len(df)


def pull(con: duckdb.DuckDBPyConnection, fetcher: Fetcher, season: int = 2026, fresh: bool = False,
         recruit_years: range | None = None) -> dict[str, int]:
    """Teams, rosters and transfers for `season`; recruits from the classes on its roster; production
    from the season before."""
    api = CFBD(fetcher, config.secret("CFBD_API_KEY") or "")
    if not api.headers["Authorization"].removeprefix("Bearer ").strip():
        raise RuntimeError("CFBD_API_KEY is not set (environment or .env)")
    prior = season - 1
    recruit_years = recruit_years or range(season - 5, season + 1)
    teams = pd.DataFrame(api.get("/teams/fbs", fresh, year=season))
    roster = pd.DataFrame(api.get("/roster", fresh, year=season))
    recruits = pd.concat([pd.DataFrame(api.get("/recruiting/players", fresh, year=y)) for y in recruit_years],
                         ignore_index=True)
    portal = pd.DataFrame(api.get("/player/portal", fresh, year=season))
    usage = pd.json_normalize(api.get("/player/usage", fresh, year=prior))
    ppa = pd.json_normalize(api.get("/ppa/players/season", fresh, year=prior))
    stats = pd.DataFrame(api.get("/stats/player/season", fresh, year=prior))
    for frame in (roster, recruits):
        for col in ("recruitIds",):
            if col in frame:
                frame[col] = frame[col].map(lambda v: [str(x) for x in v] if isinstance(v, list) else [])
    counts = {}
    for table, df in [("cfbd_teams", teams), ("cfbd_roster", roster), ("cfbd_recruits", recruits),
                      ("cfbd_portal", portal), ("cfbd_usage", usage), ("cfbd_ppa", ppa), ("cfbd_stats", stats)]:
        df = df.assign(pulled_for=season)
        counts[table] = _store(con, table, df.astype({c: str for c in df.columns if df[c].dtype == object
                                                      and c not in ("recruitIds",)}))
    return counts


def _z(x: pd.Series) -> pd.Series:
    sd = x.std()
    return (x - x.mean()) / sd if sd and sd > 0 else x * 0.0


def base_frame(con: duckdb.DuckDBPyConnection, scope: str = "a4", usage: str = "cfbd_usage", ppa: str = "cfbd_ppa",
               stats: str = "cfbd_stats") -> pd.DataFrame:
    """Players with their CSC group, raw features and standardized features (z within group over the
    scope: "a4" or "fbs"). Production comes from the named usage, PPA and stats tables (one season).
    Missing production counts as the group's lowest (no stats usually means little playing time); a
    missing rating as the group's 10th percentile."""
    teams = con.execute("SELECT school, conference FROM cfbd_teams").df()
    roster = con.execute("SELECT * FROM cfbd_roster").df().merge(teams, left_on="team", right_on="school", how="left")
    roster["a4"] = roster.conference.isin(A4_CONFERENCES) | roster.team.isin(A4_INDEPENDENTS)
    p = roster[roster.a4 if scope == "a4" else roster.conference.notna()].copy()
    p["id"] = p["id"].astype(str)
    p["group"] = p.position.map(POSITION_GROUPS).fillna("Position Unspecified")
    p["experience"] = pd.to_numeric(p.year, errors="coerce").clip(1, 6)

    rec = con.execute("SELECT id, rating FROM cfbd_recruits").df()
    rating_by_id = dict(zip(rec.id.astype(str), pd.to_numeric(rec.rating, errors="coerce")))
    p["recruit_rating"] = [max([rating_by_id[i] for i in ids if i in rating_by_id and pd.notna(rating_by_id[i])],
                               default=np.nan) for ids in p.recruitIds]

    portal = con.execute("SELECT firstName, lastName, destination, rating, stars FROM cfbd_portal").df()
    portal["key"] = (portal.firstName.str.lower().str.strip() + " " + portal.lastName.str.lower().str.strip()
                     + "|" + portal.destination.astype(str))
    portal["portal_rating"] = pd.to_numeric(portal.rating, errors="coerce").fillna(
        pd.to_numeric(portal.stars, errors="coerce").map(STAR_RATING))
    portal = portal.drop_duplicates("key")
    p["key"] = p.firstName.str.lower().str.strip() + " " + p.lastName.str.lower().str.strip() + "|" + p.team
    p = p.merge(portal[["key", "portal_rating"]], on="key", how="left")
    p["transfer"] = p.portal_rating.notna() | p.key.isin(portal.key)
    p["rating"] = p.recruit_rating.fillna(p.portal_rating)

    u = con.execute(f'SELECT id, "usage.overall" AS usage FROM {usage}').df()
    pp = con.execute(f'SELECT id, "totalPPA.all" AS ppa FROM {ppa}').df()
    st = con.execute(f"SELECT playerId AS id, category, statType, stat FROM {stats} "
                     "WHERE category IN ('defensive', 'interceptions')").df()
    st["stat"] = pd.to_numeric(st.stat, errors="coerce")
    d = st.pivot_table(index="id", columns=["category", "statType"], values="stat", aggfunc="sum")
    d.columns = [f"{a}_{b}" for a, b in d.columns]
    d = d.fillna(0)            # a defender with stats but no interception row had none
    get = lambda col: d[col] if col in d else 0.0      # noqa: E731
    defense = (get("defensive_TOT") + 3 * get("defensive_SACKS") + 1.5 * get("defensive_TFL")
               + 2 * get("defensive_PD") + 3 * get("interceptions_INT")).rename("defense").reset_index()
    for frame in (u, pp, defense):
        frame["id"] = frame["id"].astype(str)
    p = p.merge(u, on="id", how="left").merge(pp, on="id", how="left").merge(defense, on="id", how="left")
    for col in ("usage", "ppa", "defense"):
        p[col] = pd.to_numeric(p[col], errors="coerce")

    parts = []
    for group, g in p.groupby("group"):
        g = g.copy()
        if group in OFFENSE:
            prod = _z(g.usage.fillna(0)) + _z(g.ppa.fillna(0))
            g["production"] = prod.where(g.usage.notna() | g.ppa.notna(), np.nan)
        elif group in DEFENSE:
            g["production"] = g.defense
        else:
            g["production"] = np.nan
        g["has_production"] = bool(g.production.notna().any())
        g["production_z"] = _z(g.production.fillna(g.production.min() if g.has_production.iloc[0] else 0))
        g["rating_z"] = _z(g.rating.fillna(g.rating.quantile(0.10) if g.rating.notna().any() else 0))
        g["experience_z"] = _z(g.experience.fillna(g.experience.median()))
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def apply_weights(frame: pd.DataFrame, weights: dict = WEIGHTS, weights_no_production: dict = WEIGHTS_NO_PRODUCTION) -> pd.Series:
    """Score = weighted standardized features; groups without production use the second weights."""
    with_prod = sum(wt * frame[f"{name}_z"] for name, wt in weights.items())
    without = sum(wt * frame[f"{name}_z"] for name, wt in weights_no_production.items())
    return with_prod.where(frame.has_production, without)


def features(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """A4 players with their CSC group, features and score (the prior weights), stored as player_features."""
    p = base_frame(con, "a4")
    p["score"] = apply_weights(p)
    cols = ["id", "firstName", "lastName", "team", "conference", "position", "group", "experience", "rating",
            "transfer", "usage", "ppa", "defense", "production", "score"]
    out = p[cols]
    _store(con, "player_features", out)
    return out


def roster_values(players: pd.DataFrame, transports: dict, rho: float = RANK_CORR, draws: int = 300,
                  seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    """Each A4 roster's market value: the sum, over its players, of their position's A4 revenue-share
    quantile at their rank among all A4 players at the position. Ranks are uncertain (the features rank
    pay at about `rho`), so each draw re-ranks a noisy latent and re-totals; the team value is the
    middle draw and its range the central 80%. Returns (team table, each player's median estimate)."""
    cohort = players.group.to_numpy()
    scores = players.score.to_numpy(float)
    team = players.team.to_numpy()
    z = np.zeros(len(scores))
    for key in transports:
        m = cohort == key
        if m.sum() > 1:
            z[m] = (scores[m] - scores[m].mean()) / (scores[m].std() or 1)
    rng = np.random.default_rng(seed)
    teams = np.unique(team)
    idx = {t: team == t for t in teams}
    totals, top5, paid = (np.empty((draws, len(teams))) for _ in range(3))
    pay_draws = np.empty((draws, len(scores)))
    for d in range(draws):
        latent = rho * z + np.sqrt(1 - rho ** 2) * rng.standard_normal(len(z))
        pay = ex.transport_all(latent, cohort, transports)
        pay_draws[d] = pay
        for j, t in enumerate(teams):
            v = pay[idx[t]]
            totals[d, j] = v.sum()
            top5[d, j] = np.sort(v)[-5:].sum() / v.sum() if v.sum() else 0
            paid[d, j] = (v > 0).sum()
    conf = players.groupby("team").conference.first()
    table = pd.DataFrame({
        "team": teams, "conference": [conf[t] for t in teams],
        "players": [int(idx[t].sum()) for t in teams],
        "value": np.median(totals, axis=0), "low": np.quantile(totals, 0.1, axis=0),
        "high": np.quantile(totals, 0.9, axis=0), "top5_share": np.median(top5, axis=0),
        "paid_players": np.median(paid, axis=0),
    }).sort_values("value", ascending=False).reset_index(drop=True)
    return table, pd.Series(np.median(pay_draws, axis=0), index=players.id)


def roster_check(players: pd.DataFrame, published: pd.DataFrame) -> pd.DataFrame:
    """A4 players per CSC group: this season's rosters against the CSC's rostered count (calendar year)."""
    csc = published[(published.report == "revenue_share") & (published.sport == "Football")
                    & (published.cohort == "A4") & (published.population == "all_rostered")]
    csc = csc.drop_duplicates("position").set_index("position").n
    ours = players.group.value_counts()
    rows = [{"group": g, "rosters_now": int(ours.get(g, 0)), "csc_calendar_2026": int(csc.get(g, 0))}
            for g in sorted(set(ours.index) | set(csc.index))]
    return pd.DataFrame(rows)
