import numpy as np
import pandas as pd
import pytest

from nilmodel import benchmark as bm
from nilmodel import csc
from nilmodel import extend as ex
from nilmodel import players as pl


def _load(con, tables):
    for name, df in tables.items():
        pl._store(con, name, df)


def test_features_join_recruits_portal_and_defense(con):
    _load(con, {
        "cfbd_teams": pd.DataFrame({"school": ["Georgia", "Notre Dame", "Toledo"], "conference": ["SEC", "FBS Independents", "MAC"]}),
        "cfbd_roster": pd.DataFrame({
            "id": ["1", "2", "3", "4", "5"], "firstName": ["A", "B", "C", "D", "E"],
            "lastName": ["One", "Two", "Three", "Four", "Five"], "team": ["Georgia", "Georgia", "Notre Dame", "Georgia", "Toledo"],
            "position": ["LB", "LB", "EDGE", "QB", "LB"], "year": [3, 1, 4, 2, 3],
            "recruitIds": [["r1"], [], ["r3"], [], []]}),
        "cfbd_recruits": pd.DataFrame({"id": ["r1", "r3"], "rating": [0.95, 0.88]}),
        "cfbd_portal": pd.DataFrame({"firstName": ["D"], "lastName": ["Four"], "destination": ["Georgia"],
                                     "rating": [None], "stars": [4]}),
        "cfbd_usage": pd.DataFrame({"id": ["4"], "usage.overall": [0.3]}),
        "cfbd_ppa": pd.DataFrame({"id": ["4"], "totalPPA.all": [55.0]}),
        "cfbd_stats": pd.DataFrame({"playerId": ["1", "1", "2", "3"], "category": ["defensive", "defensive", "defensive", "interceptions"],
                                    "statType": ["TOT", "SACKS", "TOT", "INT"], "stat": ["60", "4", "10", "2"]}),
    })
    f = pl.features(con).set_index("id")
    assert set(f.index) == {"1", "2", "3", "4"}                        # Toledo is not A4; Notre Dame is
    assert f.loc["3", "group"] == "Defensive Lineman" and f.loc["4", "group"] == "Quarterback"
    assert f.loc["1", "rating"] == 0.95 and f.loc["4", "rating"] == pl.STAR_RATING[4] and bool(f.loc["4", "transfer"])
    assert f.loc["1", "defense"] == 60 + 3 * 4 and f.loc["2", "defense"] == 10   # no interception row counts as 0
    assert f.loc["1", "score"] > f.loc["2", "score"]


REAL = sorted(csc.ARCHIVE_DIR.glob("*_2026-10-30_*.json.gz"))


@pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")
def test_roster_values_add_up_and_bracket(con):
    csc.ingest_archive(con, csc.ARCHIVE_DIR)
    curve = bm.find(bm.curves(con.execute("SELECT * FROM csc_latest").df())[0], "revenue_share", "Football", "Quarterback", "A4")
    t = {"Quarterback": ex.Transport(curve)}
    rng = np.random.default_rng(0)
    players = pd.DataFrame({"id": [str(i) for i in range(60)], "group": "Quarterback", "team": rng.choice(["A", "B", "C"], 60),
                            "conference": "SEC", "score": rng.standard_normal(60)})
    table, per_player = pl.roster_values(players, t, draws=100)
    assert (table.low <= table.value).all() and (table.value <= table.high).all()
    assert table.players.sum() == 60 and len(per_player) == 60
    full = t["Quarterback"].pay(rng.standard_normal(60)).sum()           # any ranking spends the same total
    assert table.value.sum() == pytest.approx(full, rel=0.1)


def test_position_groups_cover_the_csc_groups():
    assert set(pl.POSITION_GROUPS.values()) | {"Position Unspecified"} == set(csc.FOOTBALL_POSITIONS)
