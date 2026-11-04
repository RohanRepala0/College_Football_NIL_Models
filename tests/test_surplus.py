import numpy as np
import pandas as pd
import pytest

from nilmodel import surplus as su


def test_quality_counts_starters_above_national_replacement():
    frame = pd.DataFrame({"team": ["A", "A", "B", "B"], "group": "Quarterback"})
    score = pd.Series([2.0, 1.0, 0.5, -1.0])
    q, contrib = su.quality(frame, score, {"Quarterback": 1})
    # replacement = the best score outside the 2 starter slots nationally = 0.5;
    # A's backup counts at rotation weight
    assert contrib.tolist() == pytest.approx([1.5, su.ROTATION * 0.5, 0.0, 0.0])
    assert q.loc["A", "Quarterback"] == pytest.approx(1.5 + su.ROTATION * 0.5) and q.loc["B", "Quarterback"] == 0


def test_fit_unit_recovers_non_negative_weights():
    rng = np.random.default_rng(0)
    q = pd.DataFrame(rng.random((120, 3)), columns=["a", "b", "c"])
    y = pd.Series(5 + 3 * q.a + 1 * q.b + 0 * q.c + rng.normal(0, 0.05, 120))
    beta, b0, r2 = su.fit_unit(q, y)
    assert beta["a"] == pytest.approx(3, abs=0.1) and beta["b"] == pytest.approx(1, abs=0.1)
    assert beta["c"] >= 0 and r2 > 0.95


def test_learned_weights_follow_what_drives_team_results():
    rng = np.random.default_rng(1)
    teams = [f"T{i}" for i in range(80)]
    rows = []
    for t in teams:
        for _ in range(4):
            rows.append({"team": t, "group": "Linebacker", "has_production": True, "production_z": rng.standard_normal(),
                         "rating_z": rng.standard_normal(), "experience_z": rng.standard_normal()})
    f = pd.DataFrame(rows)
    top = f.sort_values("production_z", ascending=False).groupby("team").head(3)
    targets = pd.DataFrame({"defense": top.groupby("team").production_z.sum()})
    for unit in ("offense", "special_teams", "overall"):
        targets[unit] = 0.0
    saved = su.UNITS
    su.UNITS = {"defense": {"Linebacker": 3}}
    try:
        grid = su.learn_weights(f, targets)
    finally:
        su.UNITS = saved
    best = grid[~grid.prior].sort_values("cv_r2", ascending=False).iloc[0]
    assert best.production >= 0.8
