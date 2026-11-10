import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from nilmodel import benchmark as bm
from nilmodel import csc
from nilmodel import triangulate as tri


def test_floor_mean_needs_no_model():
    # 10% between $0 and the 10th, 40% paid at least $10, 40% at least $50, 10% at least $90
    assert tri.floor_mean([(10, 10), (50, 50), (90, 90)]) == pytest.approx(33)


def _lognormal_cohort(mu=11.0, sigma=1.2, n=500):
    values = [float(np.exp(mu + sigma * norm.ppf(p / 100))) for p in csc.PERCENTILES]
    rows = [{"report": "nil_go", "payload_sha256": "sha", "gender": "men", "sport": "Football", "position": "Quarterback",
             "cohort": "A4", "a4": True, "population": "deal_holders", "n": n, "n_text": None, "percentile": p,
             "value_usd": v, "min_n": None, "window_start": None, "window_end": None, "as_of": None,
             "window_label": "w", "source_ref": "t"} for p, v in zip(csc.PERCENTILES, values)]
    return pd.DataFrame(rows)


def test_curve_mean_is_exact_for_a_lognormal_cohort():
    c = bm.curves(_lognormal_cohort())[0][0]
    assert c.tail_slope == pytest.approx(1.2)
    assert tri.curve_mean(c) == pytest.approx(np.exp(11.0 + 1.2 ** 2 / 2), rel=1e-3)
    assert tri._Part(c).mean(1.0) == pytest.approx(tri.curve_mean(c), rel=1e-6)
    assert tri.tail_value(c, 99, 1.0) == pytest.approx(np.exp(11.0 + 1.2 * norm.ppf(0.99)), rel=1e-6)


def test_solve_tail_recovers_the_multiplier():
    parts = tri.football_parts(_lognormal_cohort(), "nil_go", ("A4",))
    assert tri.solve_tail(parts, tri.parts_total(parts, 0.7)) == pytest.approx(0.7, abs=1e-6)
    assert tri.solve_tail(parts, tri.parts_total(parts, 0.0) * 0.9) is None      # below even a flat tail


REAL = sorted(csc.ARCHIVE_DIR.glob("*_2026-10-30_*.json.gz"))


@pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")
def test_first_real_release(con):
    csc.ingest_archive(con, csc.ARCHIVE_DIR)
    df = con.execute("SELECT * FROM csc_latest").df()
    pp = tri.per_program(tri.roll_up(tri.cohort_totals(df)))
    assert 11e6 < pp["floor"] < 12.5e6 and pp["heavy_cap_share"] > 1          # a heavy tail breaks the cap
    cal = tri.calibrate(df).set_index(["report", "case"]).tail_mult
    assert 0 < cal["revenue_share", "central"] < cal["revenue_share", "high"] < 1
    assert 0 < cal["nil_go", "central"] < cal["nil_go", "high"] < 1
    assert np.isnan(cal["revenue_share", "low"]) and np.isnan(cal["nil_go", "low"])


@pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")
def test_caps_year_one_bounds_footballs_share(con):
    for path in REAL:
        csc.ingest_archive(con, path.parent)
    df = con.execute("SELECT * FROM csc_latest").df()
    bound = tri.football_share_bound(df)
    assert 0.75 < bound < 0.90                                   # other A4 sports' floor leaves football at most ~88%
    assert tri.football_cap_share(df)[2] == pytest.approx(bound)
    c = tri.caps_check(df)
    assert c["floor_total"] < c["caps_total"] < c["estimate_total"]    # floors hold; fitted tails overshoot
    assert c["athletes_published"] < c["athletes_caps"]
    assert c["football_share_published"] < c["football_share_max"]
