import numpy as np
import pandas as pd
import pytest

from nilmodel import benchmark as bm
from nilmodel import csc
from nilmodel import extend as ex
from nilmodel import simulate as sim

REAL = sorted(csc.ARCHIVE_DIR.glob("*_2026-10-30_*.json.gz"))
pytestmark = pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")


@pytest.fixture
def published(con):
    csc.ingest_archive(con, csc.ARCHIVE_DIR)
    return con.execute("SELECT * FROM csc_latest").df()


@pytest.fixture
def qb(published):
    return ex.Transport(bm.find(bm.curves(published)[0], "revenue_share", "Football", "Quarterback", "A4"))


def test_transport_reproduces_the_published_distribution(qb):
    pay = qb.pay(np.random.default_rng(0).standard_normal(20_000))
    assert np.mean(pay == 0) == pytest.approx(qb.zero, abs=0.001)                  # 30% unpaid
    assert np.median(pay[pay > 0]) == pytest.approx(230_000, rel=0.02)             # published paid median
    assert np.quantile(pay[pay > 0], 0.9) == pytest.approx(1_611_000, rel=0.02)    # published paid 90th
    assert qb.rank_of(float(qb.pay_at(0.8))) == pytest.approx(0.8, abs=1e-3)


def test_anchor_pins_a_claimed_player_at_his_claim(qb):
    scores = np.random.default_rng(1).standard_normal(367)
    cohort = np.array(["Quarterback"] * 367)
    value = np.zeros(367)
    value[5] = 900_000
    anchored = ex.anchor(scores, cohort, np.array([5]), value, {"Quarterback": qb})
    pay = qb.pay(anchored)
    assert pay[5] == pytest.approx(900_000, rel=0.03)
    assert np.array_equal(np.delete(anchored, 5), np.delete(scores, 5))            # nobody else moves


def test_rake_matches_a_disclosed_total(qb):
    rng = np.random.default_rng(2)
    scores = rng.standard_normal(367)
    cohort, school = np.array(["Quarterback"] * 367), rng.integers(10, size=367)
    t = {"Quarterback": qb}
    base = qb.pay(scores)[school == 3].sum()
    gamma = ex.rake(scores, cohort, school, t, {3: base * 1.5})
    shifted = scores + np.where(school == 3, gamma[3], 0.0)
    assert qb.pay(shifted)[school == 3].sum() == pytest.approx(base * 1.5, rel=0.02)


def test_weights_are_learned_from_claims_that_cover_the_cohort():
    rng = np.random.default_rng(3)
    n = 400
    talent = rng.standard_normal(n)
    X = np.column_stack([talent + 0.3 * rng.standard_normal(n), rng.standard_normal(n)])   # feature 2 is noise
    claimed = rng.choice(n, 120, replace=False)                                          # a random sample, not just stars
    value = np.zeros(n)
    value[claimed] = np.exp(talent[claimed])
    w = ex.fit_weights(ex.standardize(X), np.zeros(n, int), claimed, value, np.array([0.5, 0.5]))
    assert w[0] > 3 * abs(w[1])


def test_synthetic_market_matches_the_curves_and_claims_carry_bias(published):
    transports = sim.football_transports(published)
    world = sim.market(transports, seed=0)
    qb = world["players"][world["players"].cohort == "Quarterback"].pay
    assert len(qb) == 367 and np.mean(qb == 0) == pytest.approx(transports["Quarterback"].zero, abs=0.01)
    claims = sim.make_claims(world["players"], seed=0)
    assert set(claims.source) == set(sim.SOURCES)
    truth = world["players"].set_index("player_id").pay
    hype = claims[claims.source == "hype_account"]
    assert np.median(hype.amount.to_numpy() / truth.loc[hype.player].to_numpy()) == pytest.approx(2.5, rel=0.25)
