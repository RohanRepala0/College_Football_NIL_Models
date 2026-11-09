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
