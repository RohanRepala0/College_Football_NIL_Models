import numpy as np
import pandas as pd

from nilmodel import ratings as rt


def test_fit_margins_recovers_ratings_and_home_edge():
    rng = np.random.default_rng(0)
    teams = [f"T{i}" for i in range(12)]
    true = pd.Series(np.linspace(-10, 10, len(teams)), index=teams)
    rows = []
    for _ in range(400):
        h, a = rng.choice(teams, 2, replace=False)
        neutral = rng.random() < 0.1
        rows.append({"home": h, "away": a, "neutral": neutral,
                     "margin": true[h] - true[a] + (0 if neutral else 2.5) + rng.normal(0, 3)})
    rating, hfa = rt.fit_margins(pd.DataFrame(rows), cap=np.inf)
    assert abs(hfa - 2.5) < 0.5
    assert abs(rating.mean()) < 1e-6
    assert np.allclose(rating.reindex(teams), true - true.mean(), atol=0.8)


def test_margin_cap_limits_blowouts():
    games = pd.DataFrame([{"home": "A", "away": "B", "neutral": True, "margin": 70.0},
                          {"home": "B", "away": "A", "neutral": True, "margin": -10.0}])
    capped, _ = rt.fit_margins(games, cap=28)
    raw, _ = rt.fit_margins(games, cap=np.inf)
    assert capped["A"] - capped["B"] < raw["A"] - raw["B"]


def test_signals_graded_like_the_ratings_repo():
    from nilmodel import season

    assert season._grade("total", "over", 47.5, 28, 21) == "win"          # 49 > 47.5
    assert season._grade("total", "under", 47.5, 28, 21) == "loss"
    assert season._grade("total", "over", 49.0, 28, 21) == "push"
    assert season._grade("spread", "home", -6.5, 28, 21) == "win"         # home by 7 covers -6.5
    assert season._grade("spread", "away", 6.5, 28, 21) == "loss"
    assert season._grade("spread", "away", 7.0, 28, 21) == "push"


def test_pooled_fit_ignores_season_baselines_and_groups_folds_by_program():
    rng = np.random.default_rng(1)
    teams = [f"T{i}" for i in range(60)]
    beta = np.array([2.0, 0.5, 0.0])
    blocks = []
    for offset in (10.0, -7.0):                       # each season's ratings sit on a different baseline
        X = pd.DataFrame(rng.random((60, 3)), index=teams, columns=["a", "b", "c"])
        y = pd.Series(X.to_numpy() @ beta + offset + rng.normal(0, 0.05, 60), index=teams)
        blocks.append((X, y))
    fit, means = rt._centred_fit([(X.to_numpy(), y.to_numpy()) for X, y in blocks])
    assert np.allclose(fit, beta, atol=0.1)
    assert [round(m[1]) for m in means] == [round(blocks[0][1].mean()), round(blocks[1][1].mean())]
    assert rt.pooled_cv(blocks) > 0.95
    shuffled = [(X, pd.Series(rng.permutation(y.to_numpy()), index=y.index)) for X, y in blocks]
    assert rt.pooled_cv(shuffled) < 0.1
