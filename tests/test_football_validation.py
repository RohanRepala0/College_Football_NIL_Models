import numpy as np
import pandas as pd

from nilmodel import football_validation as fv


def _result(cv=0.6, placebo=0.02, oos=0.6, players=7844):
    return {"quality": {"players": players, "csc_rostered": 7743, "rating_coverage": 0.74},
            "surplus": {"placebo": pd.DataFrame({"cv_r2": [cv, cv + 0.1], "placebo_max": [placebo, placebo]})},
            "season": {"results": pd.DataFrame({"r2": [oos, oos + 0.03]})}}


def _rosters(medians, calls=None):
    teams = [f"T{i}" for i in range(len(medians))]
    return pd.DataFrame({"team": teams, "median": medians,
                         "agree": calls or ["surplus everywhere" if m > 0 else "deficit everywhere" for m in medians]})


def test_gates_pass_and_compare_with_the_last_snapshot(tmp_path):
    (tmp_path / "2026-11-02").mkdir()
    _rosters([3.0, 2.0, -1.0, -2.0]).to_csv(tmp_path / "2026-11-02" / "surplus_by_rating.csv", index=False)
    g = fv.gates(_result(), "2026-11-10", _rosters([3.1, 1.9, -1.2, -2.1]), tmp_path).set_index("gate")
    assert g.passed.all() and g.value["week_over_week"] == 1.0


def test_gates_fail_on_a_placebo_fit_a_roster_gap_or_a_reshuffle(tmp_path):
    (tmp_path / "2026-11-02").mkdir()
    _rosters([3.0, 2.0, -1.0, -2.0]).to_csv(tmp_path / "2026-11-02" / "surplus_by_rating.csv", index=False)
    g = fv.gates(_result(placebo=0.4, players=9000), "2026-11-10", _rosters([-2.0, -1.0, 2.0, 3.0]), tmp_path).set_index("gate")
    assert not g.passed["placebo"] and not g.passed["roster_vs_csc"] and not g.passed["week_over_week"]
    assert g.passed["fit_r2"]


def test_gates_without_history_skip_the_weekly_comparison(tmp_path):
    g = fv.gates(_result(), "2026-11-10", _rosters([1.0, -1.0]), tmp_path).set_index("gate")
    assert g.passed["week_over_week"] and g.note["week_over_week"] == "no earlier snapshot"


def test_fit_and_r2():
    rng = np.random.default_rng(0)
    X = rng.random((200, 3))
    y = X @ np.array([2.0, 0.0, 1.0]) + 5 + rng.normal(0, 0.01, 200)
    beta, b0 = fv._fit(X, y)
    assert np.allclose(beta, [2.0, 0.0, 1.0], atol=0.02) and abs(b0 - 5) < 0.05
    assert fv._r2(y, b0 + X @ beta) > 0.99
